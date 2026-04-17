from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models
from ..db.database import get_db
from .auth import require_role, get_current_user
from ..security.learning_tracker import (
    build_learning_progress_payload,
    build_challenge_progress_detail,
    compute_skills_scores,
    SKILL_BUCKETS,
    TOTAL_CHALLENGES,
)

router = APIRouter()

@router.get("/admin/dashboard")
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    # 1. REAL USER COUNTS
    total_users = db.query(models.User).count()
    student_count = db.query(models.User).filter(models.User.role == 'user').count()
    instructor_count = db.query(models.User).filter(models.User.role == 'instructor').count()
    admin_count = db.query(models.User).filter(models.User.role == 'admin').count()

    # 2. Core lab count used across the learning system.
    active_exploits = TOTAL_CHALLENGES

    # 3. REAL FIXED VULNERABILITIES
    # Counts exact number of times students passed a sandbox test.
    fixed_vulns = db.query(models.UserProgress).count()

    # 4. DATA FOR PIE CHART
    user_distribution = [
        {"name": "Students", "value": student_count},
        {"name": "Instructors", "value": instructor_count},
        {"name": "Admins", "value": admin_count},
    ]

    # 5. DATA FOR BAR CHART — real attempt sums from challenge_state.attempt_count
    # and completion counts from user_progress per challenge slug (not fabricated).
    challenge_slugs: list[tuple[str, str]] = [
        ("SQL Injection", "sql-injection"),
        ("XSS", "xss"),
        ("CSRF", "csrf"),
        ("Command Injection", "command-injection"),
        ("Broken Authentication", "broken-auth"),
        ("Security Misconfiguration", "security-misc"),
        ("Insecure Storage", "insecure-storage"),
        ("Directory Traversal", "directory-traversal"),
        ("XXE", "xxe"),
        ("Redirect", "redirect"),
    ]

    challenge_usage = []
    for display_name, slug in challenge_slugs:
        attempts_raw = (
            db.query(func.coalesce(func.sum(models.ChallengeState.attempt_count), 0))
            .filter(models.ChallengeState.challenge_id == slug)
            .scalar()
        )
        attempts = int(attempts_raw or 0)

        successes = (
            db.query(func.count(func.distinct(models.UserProgress.user_id)))
            .filter(models.UserProgress.challenge_id == slug)
            .scalar()
            or 0
        )
        successes = int(successes)

        challenge_usage.append(
            {
                "name": display_name,
                "attempts": attempts,
                "successes": successes,
            }
        )

    return {
        "total_users": total_users,
        "active_exploits": active_exploits,
        "fixed_vulns": fixed_vulns,
        "user_distribution": user_distribution,
        "challenge_usage": challenge_usage,
        "system_status": "Operational"
    }

@router.get("/instructor/dashboard")
def get_instructor_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    students = db.query(models.User).filter(models.User.role == 'user').all()
    student_ids = [s.id for s in students]
    total_students = len(students)
    total_questions = db.query(models.Question).count()
    total_assignments = db.query(models.QuizAssignment).count()

    if total_students == 0:
        avg_completion = 0
        class_performance = []
    else:
        per_user_solved = (
            db.query(models.UserProgress.user_id, func.count(models.UserProgress.id))
            .filter(models.UserProgress.user_id.in_(student_ids))
            .group_by(models.UserProgress.user_id)
            .all()
        )
        solved_map = {uid: c for uid, c in per_user_solved}
        total_slots = total_students * TOTAL_CHALLENGES
        sum_solved = sum(min(solved_map.get(uid, 0), TOTAL_CHALLENGES) for uid in student_ids)
        avg_completion = int((sum_solved / total_slots) * 100) if total_slots else 0

        totals = {k: 0 for k in SKILL_BUCKETS}
        full_count = {k: 0 for k in SKILL_BUCKETS}
        for uid in student_ids:
            sc = compute_skills_scores(db, uid)
            for k in SKILL_BUCKETS:
                totals[k] += sc[k]
                if sc[k] >= 100:
                    full_count[k] += 1
        n = total_students
        class_performance = [
            {"name": k, "avgScore": totals[k] // n, "completions": full_count[k]}
            for k in SKILL_BUCKETS
        ]

    return {
        "total_students": total_students,
        "quizzes_created": total_assignments,
        "questions_in_bank": total_questions,
        "class_performance": class_performance,
        "avg_completion_rate": avg_completion,
        "total_challenges": TOTAL_CHALLENGES,
    }


@router.get("/progress/me")
def get_my_learning_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    payload = build_learning_progress_payload(db, current_user.id)
    payload["challenge_detail"] = build_challenge_progress_detail(db, current_user.id)
    return payload