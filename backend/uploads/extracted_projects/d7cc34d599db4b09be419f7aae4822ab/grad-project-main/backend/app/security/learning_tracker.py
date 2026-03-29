from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models

# Canonical lab count (7 original + 3 new); not derived from DB rows to avoid doubled totals.
TOTAL_CHALLENGES = 10

LEGACY_CHALLENGE_IDS: dict[str, str] = {
    "1": "sql-injection",
    "2": "xss",
    "3": "csrf",
    "4": "command-injection",
    "5": "broken-auth",
    "6": "security-misc",
    "7": "insecure-storage",
    "8": "directory-traversal",
    "9": "xxe",
    "10": "redirect",
}

# Six radar dimensions; each maps to one or more progress slugs (10 labs total).
SKILL_BUCKETS: dict[str, list[str]] = {
    "SQL Injection": ["sql-injection", "broken-auth"],
    "XSS": ["xss"],
    "CSRF": ["csrf", "redirect"],
    "Traversal": ["directory-traversal", "command-injection"],
    "XXE": ["xxe"],
    "Storage": ["insecure-storage", "security-misc"],
}


def normalize_progress_challenge_id(raw: str) -> str:
    r = (raw or "").strip().lower()
    return LEGACY_CHALLENGE_IDS.get(r, r)


def compute_skills_scores(db: Session, user_id: int) -> dict[str, int]:
    rows = (
        db.query(models.UserProgress.challenge_id)
        .filter(models.UserProgress.user_id == user_id)
        .all()
    )
    solved = {normalize_progress_challenge_id(p[0]) for p in rows}
    out: dict[str, int] = {}
    for skill, slugs in SKILL_BUCKETS.items():
        done = sum(1 for s in slugs if s in solved)
        out[skill] = int(round(100 * done / len(slugs)))
    return out


def _determine_level(vulnerabilities_solved: int, accuracy: float) -> str:
    if vulnerabilities_solved >= 9 and accuracy >= 80:
        return "Advanced"
    if vulnerabilities_solved >= 4 and accuracy >= 60:
        return "Intermediate"
    return "Beginner"


def ensure_learning_progress(db: Session, user_id: int) -> models.UserLearningProgress:
    row = db.query(models.UserLearningProgress).filter(models.UserLearningProgress.user_id == user_id).first()
    if row:
        return row
    row = models.UserLearningProgress(user_id=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def recalculate_learning_progress(db: Session, user_id: int) -> models.UserLearningProgress:
    row = ensure_learning_progress(db, user_id)

    solved = (
        db.query(func.count(func.distinct(models.UserProgress.challenge_id)))
        .filter(models.UserProgress.user_id == user_id)
        .scalar()
        or 0
    )
    total_answers = db.query(models.UserAnswer).filter(models.UserAnswer.user_id == user_id).count()
    correct_answers = (
        db.query(models.UserAnswer)
        .filter(models.UserAnswer.user_id == user_id, models.UserAnswer.is_correct == True)  # noqa: E712
        .count()
    )
    failed_answers = max(total_answers - correct_answers, 0)
    avg_time_value = (
        db.query(func.avg(models.QuizAttempt.time_seconds))
        .filter(models.QuizAttempt.user_id == user_id)
        .scalar()
    )
    avg_time = float(avg_time_value or 0.0)
    accuracy = (correct_answers / total_answers * 100.0) if total_answers > 0 else 0.0

    challenge_rows = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).all()
    skills = compute_skills_scores(db, user_id)
    if skills:
        strongest = max(skills, key=skills.get)
        weakest = min(skills, key=skills.get)
    else:
        strongest = "N/A"
        weakest = "N/A"
    # Streak approximation from consecutive challenge completion days.
    progress_dates = sorted(
        {p.completed_at.date() for p in challenge_rows if p.completed_at is not None},
        reverse=True,
    )
    streak = 0
    if progress_dates:
        current = progress_dates[0]
        for d in progress_dates:
            if (current - d).days == 0:
                streak += 1
                current = d
            elif (current - d).days == 1:
                streak += 1
                current = d
            else:
                break

    learning_speed = (solved / max(avg_time, 1.0)) * 100.0 if solved > 0 else 0.0
    retention_score = min(
        100.0,
        max(
            0.0,
            (accuracy * 0.6) + (min(streak, 14) / 14.0 * 20.0) + (100.0 - min(failed_answers * 2, 40)),
        ),
    )

    row.vulnerabilities_solved = min(solved, TOTAL_CHALLENGES)
    row.failed_attempts = failed_answers
    row.accuracy = round(accuracy, 2)
    row.avg_time = round(avg_time, 2)
    row.strongest_category = strongest
    row.weakest_category = weakest
    row.level = _determine_level(solved, accuracy)
    row.streak_days = streak
    row.learning_speed = round(learning_speed, 2)
    row.retention_score = round(retention_score, 2)
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def build_learning_progress_payload(db: Session, user_id: int) -> dict:
    """
    Single source of truth for student dashboard and instructor analytics.
    """
    profile = recalculate_learning_progress(db, user_id)
    skills = compute_skills_scores(db, user_id)
    skills_radar = [{"subject": name, "value": val} for name, val in skills.items()]
    solved = min(profile.vulnerabilities_solved, TOTAL_CHALLENGES)
    return {
        "vulnerabilities_solved": solved,
        "total_challenges": TOTAL_CHALLENGES,
        "failed_attempts": profile.failed_attempts,
        "accuracy": profile.accuracy,
        "avg_time": profile.avg_time,
        "strongest_category": profile.strongest_category,
        "weakest_category": profile.weakest_category,
        "level": profile.level,
        "streak_days": profile.streak_days,
        "learning_speed": profile.learning_speed,
        "retention_score": profile.retention_score,
        "skills": skills,
        "skills_radar": skills_radar,
        "recommendations": get_learning_recommendations(profile),
    }


def get_learning_recommendations(profile: Optional[models.UserLearningProgress]) -> list[str]:
    if not profile:
        return ["Start with SQL Injection and XSS beginner labs."]
    recs: list[str] = []
    if profile.weakest_category and profile.weakest_category != "N/A":
        recs.append(f"Focus next on {profile.weakest_category} scenarios.")
    if profile.accuracy < 60:
        recs.append("Review AI Mentor explanations before retrying quizzes.")
    if profile.failed_attempts > 10:
        recs.append("Use progressive hints strategically to reduce repeated failures.")
    if not recs:
        recs.append("Maintain momentum by attempting advanced mixed-vulnerability projects.")
    return recs

