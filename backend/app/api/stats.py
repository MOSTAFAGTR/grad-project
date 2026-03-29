from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models
from ..db.database import get_db
from .auth import require_role, get_current_user
from ..security.security_logger import SecurityEventType
from ..security.learning_tracker import (
    build_learning_progress_payload,
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

    # 5. DATA FOR BAR CHART (all 10 challenges, no fabricated attempts)
    progress_counts = db.query(
        models.UserProgress.challenge_id, func.count(models.UserProgress.challenge_id)
    ).group_by(models.UserProgress.challenge_id).all()

    success_counts = {str(pid): int(count) for pid, count in progress_counts}

    event_counts = {
        event_type: int(count)
        for event_type, count in db.query(
            models.SecurityLog.event_type,
            func.count(models.SecurityLog.id),
        )
        .filter(models.SecurityLog.context_type == "challenge")
        .group_by(models.SecurityLog.event_type)
        .all()
    }

    challenge_rows = [
        {
            "name": "SQL Injection",
            "ids": {"1", "sql-injection"},
            "events": {SecurityEventType.CHALLENGE_SQLI},
        },
        {
            "name": "XSS",
            "ids": {"2", "xss"},
            "events": {SecurityEventType.CHALLENGE_XSS},
        },
        {
            "name": "CSRF",
            "ids": {"3", "csrf"},
            "events": {SecurityEventType.CHALLENGE_CSRF},
        },
        {
            "name": "Command Injection",
            "ids": {"4", "command-injection"},
            "events": {SecurityEventType.CHALLENGE_COMMAND},
        },
        {
            "name": "Broken Authentication",
            "ids": {"5", "broken-auth"},
            "events": set(),  # CHALLENGE_AUTH is shared with security-misc in current logger mapping
        },
        {
            "name": "Security Misconfiguration",
            "ids": {"6", "security-misc"},
            "events": set(),  # CHALLENGE_AUTH is shared with broken-auth in current logger mapping
        },
        {
            "name": "Insecure Storage",
            "ids": {"7", "insecure-storage"},
            "events": {SecurityEventType.CHALLENGE_STORAGE},
        },
        {
            "name": "Directory Traversal",
            "ids": {"8", "directory-traversal"},
            "events": {SecurityEventType.CHALLENGE_TRAVERSAL},
        },
        {
            "name": "XXE",
            "ids": {"9", "xxe"},
            "events": {SecurityEventType.CHALLENGE_XXE},
        },
        {
            "name": "Redirect",
            "ids": {"10", "redirect"},
            "events": {SecurityEventType.CHALLENGE_REDIRECT},
        },
    ]

    challenge_usage = []
    for row in challenge_rows:
        successes = sum(success_counts.get(ch_id, 0) for ch_id in row["ids"])
        attempts = sum(event_counts.get(evt, 0) for evt in row["events"]) if row["events"] else successes
        challenge_usage.append(
            {
                "name": row["name"],
                "attempts": max(successes, attempts),
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
    return build_learning_progress_payload(db, current_user.id)