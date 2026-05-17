"""
Instructor-assigned timed challenge labs (separate from self-paced labs).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..db.database import get_db
from ..schemas import AssignmentFixSubmit, ChallengeAssignmentCreate
from .auth import get_current_user, require_role
from .challenges import _verify_fix_improvement

router = APIRouter(tags=["challenge_assignments"])

VALID_CHALLENGE_SLUGS = frozenset(
    {
        "sql-injection",
        "xss",
        "csrf",
        "command-injection",
        "broken-auth",
        "security-misc",
        "insecure-storage",
        "directory-traversal",
        "xxe",
        "redirect",
    }
)


def _normalize_slug(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s.startswith("challenge-"):
        s = s.replace("challenge-", "", 1)
    return s


def _parse_due_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace("Z", "")
    try:
        if "T" not in s and len(s) <= 10:
            return datetime.fromisoformat(s + "T23:59:59")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _challenge_title(slug: str) -> str:
    return {
        "sql-injection": "SQL Injection",
        "xss": "XSS",
        "csrf": "CSRF",
        "command-injection": "Command Injection",
        "broken-auth": "Broken Authentication",
        "security-misc": "Security Misconfiguration",
        "insecure-storage": "Insecure Storage",
        "directory-traversal": "Directory Traversal",
        "xxe": "XXE",
        "redirect": "Open Redirect",
    }.get(slug, slug.replace("-", " ").title())


@router.post("/create")
def create_challenge_assignment(
    body: ChallengeAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    slug = _normalize_slug(body.challenge_slug)
    if slug not in VALID_CHALLENGE_SLUGS:
        raise HTTPException(status_code=400, detail="Invalid challenge_slug.")
    if body.time_limit_minutes < 10 or body.time_limit_minutes > 240:
        raise HTTPException(status_code=400, detail="time_limit_minutes must be between 10 and 240.")
    if not body.student_ids:
        raise HTTPException(status_code=400, detail="At least one student is required.")

    rows = db.query(models.User).filter(models.User.id.in_(body.student_ids)).all()
    found = {r.id for r in rows}
    missing = sorted(set(body.student_ids) - found)
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown user id(s): {missing}")
    bad_role = sorted({r.id for r in rows if r.role != "user"})
    if bad_role:
        raise HTTPException(status_code=400, detail=f"These ids are not students (role user): {bad_role}")

    due = _parse_due_date(body.due_date)
    assign = models.ChallengeAssignment(
        created_by=current_user.id,
        challenge_slug=slug,
        title=(body.title or "").strip()[:255],
        instructions=(body.instructions or "").strip() or None,
        time_limit_minutes=int(body.time_limit_minutes),
        due_date=due,
    )
    db.add(assign)
    db.flush()
    for sid in body.student_ids:
        db.add(
            models.ChallengeAssignmentStudent(
                assignment_id=assign.id,
                student_id=sid,
                status="assigned",
            )
        )
    db.commit()
    db.refresh(assign)
    return {
        "assignment_id": assign.id,
        "title": assign.title,
        "challenge_slug": assign.challenge_slug,
        "students_assigned": len(body.student_ids),
    }


@router.get("/my")
def my_challenge_assignments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.utcnow()
    rows = (
        db.query(models.ChallengeAssignmentStudent, models.ChallengeAssignment)
        .join(
            models.ChallengeAssignment,
            models.ChallengeAssignment.id == models.ChallengeAssignmentStudent.assignment_id,
        )
        .filter(models.ChallengeAssignmentStudent.student_id == current_user.id)
        .filter(models.ChallengeAssignment.is_active == True)  # noqa: E712
        .all()
    )
    out: list[dict[str, Any]] = []
    for cas, ca in rows:
        due = ca.due_date
        is_past_due = bool(due and now > due)
        time_remaining: Optional[int] = None
        if cas.status == "in_progress" and cas.started_at:
            limit_sec = ca.time_limit_minutes * 60
            used = int((now - cas.started_at).total_seconds())
            time_remaining = max(0, limit_sec - used)
        out.append(
            {
                "assignment_id": ca.id,
                "student_row_id": cas.id,
                "title": ca.title,
                "challenge_slug": ca.challenge_slug,
                "challenge_name": _challenge_title(ca.challenge_slug),
                "time_limit_minutes": ca.time_limit_minutes,
                "due_date": ca.due_date.isoformat() if ca.due_date else None,
                "status": cas.status,
                "started_at": cas.started_at.isoformat() if cas.started_at else None,
                "submitted_at": cas.submitted_at.isoformat() if cas.submitted_at else None,
                "score": cas.score,
                "sandbox_passed": cas.sandbox_passed,
                "is_past_due": is_past_due,
                "time_remaining_seconds": time_remaining,
            }
        )
    return out


@router.post("/{assignment_id}/start")
def start_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.utcnow()
    cas = (
        db.query(models.ChallengeAssignmentStudent)
        .join(
            models.ChallengeAssignment,
            models.ChallengeAssignment.id == models.ChallengeAssignmentStudent.assignment_id,
        )
        .filter(
            models.ChallengeAssignmentStudent.assignment_id == assignment_id,
            models.ChallengeAssignmentStudent.student_id == current_user.id,
        )
        .filter(models.ChallengeAssignment.is_active == True)  # noqa: E712
        .first()
    )
    if not cas:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    ca = db.query(models.ChallengeAssignment).filter(models.ChallengeAssignment.id == assignment_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if ca.due_date and now > ca.due_date:
        raise HTTPException(status_code=403, detail="Assignment has expired.")

    if cas.status != "assigned":
        raise HTTPException(status_code=400, detail="Already started or submitted.")

    cas.started_at = now
    cas.status = "in_progress"
    db.commit()
    db.refresh(cas)
    return {
        "started_at": cas.started_at.isoformat() if cas.started_at else "",
        "time_limit_minutes": ca.time_limit_minutes,
        "time_limit_seconds": ca.time_limit_minutes * 60,
    }


@router.post("/{assignment_id}/submit-fix")
def submit_assignment_fix(
    assignment_id: int,
    body: AssignmentFixSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.utcnow()
    cas = (
        db.query(models.ChallengeAssignmentStudent)
        .join(
            models.ChallengeAssignment,
            models.ChallengeAssignment.id == models.ChallengeAssignmentStudent.assignment_id,
        )
        .filter(
            models.ChallengeAssignmentStudent.assignment_id == assignment_id,
            models.ChallengeAssignmentStudent.student_id == current_user.id,
        )
        .filter(models.ChallengeAssignment.is_active == True)  # noqa: E712
        .first()
    )
    if not cas:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    ca = db.query(models.ChallengeAssignment).filter(models.ChallengeAssignment.id == assignment_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if cas.status != "in_progress":
        raise HTTPException(status_code=400, detail="Assignment not in progress.")

    if not cas.started_at:
        raise HTTPException(status_code=400, detail="Assignment not started.")

    elapsed = (now - cas.started_at).total_seconds()
    if elapsed > ca.time_limit_minutes * 60:
        cas.status = "expired"
        db.commit()
        raise HTTPException(status_code=403, detail="Time limit exceeded. Assignment expired.")

    if ca.due_date and now > ca.due_date:
        cas.status = "expired"
        db.commit()
        raise HTTPException(status_code=403, detail="Past due date.")

    challenge_dir = f"challenge-{ca.challenge_slug}"
    result = _verify_fix_improvement(challenge_dir, body.submitted_code or "")
    passed = bool(result.get("fixed"))
    logs = str(result.get("test_output") or "")

    cas.submitted_at = now
    cas.time_used_seconds = int(elapsed)
    cas.fix_code_submitted = (body.submitted_code or "")[:10000]
    cas.sandbox_passed = passed
    cas.score = 100 if passed else 0
    cas.status = "passed" if passed else "failed"
    db.commit()

    return {
        "passed": passed,
        "score": cas.score,
        "time_used_seconds": cas.time_used_seconds,
        "message": "Assignment submitted and validated.",
        "sandbox_logs": logs[:500],
    }


@router.get("/{assignment_id}/status")
def assignment_status(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.utcnow()
    cas = (
        db.query(models.ChallengeAssignmentStudent)
        .join(
            models.ChallengeAssignment,
            models.ChallengeAssignment.id == models.ChallengeAssignmentStudent.assignment_id,
        )
        .filter(
            models.ChallengeAssignmentStudent.assignment_id == assignment_id,
            models.ChallengeAssignmentStudent.student_id == current_user.id,
        )
        .filter(models.ChallengeAssignment.is_active == True)  # noqa: E712
        .first()
    )
    if not cas:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    ca = db.query(models.ChallengeAssignment).filter(models.ChallengeAssignment.id == assignment_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    limit_sec = ca.time_limit_minutes * 60
    time_used = 0
    if cas.started_at and cas.status == "in_progress":
        time_used = int((now - cas.started_at).total_seconds())
    elif cas.time_used_seconds is not None:
        time_used = int(cas.time_used_seconds)

    time_remaining = None
    if cas.status == "in_progress" and cas.started_at:
        time_remaining = max(0, limit_sec - time_used)

    is_expired = False
    if cas.status == "in_progress" and time_remaining is not None:
        is_expired = time_remaining <= 0
    if ca.due_date and now > ca.due_date:
        is_expired = True

    return {
        "assignment_id": ca.id,
        "title": ca.title,
        "challenge_slug": ca.challenge_slug,
        "instructions": ca.instructions,
        "time_limit_minutes": ca.time_limit_minutes,
        "due_date": ca.due_date.isoformat() if ca.due_date else None,
        "status": cas.status,
        "started_at": cas.started_at.isoformat() if cas.started_at else None,
        "submitted_at": cas.submitted_at.isoformat() if cas.submitted_at else None,
        "score": cas.score,
        "sandbox_passed": cas.sandbox_passed,
        "time_used_seconds": time_used,
        "time_remaining_seconds": time_remaining,
        "is_expired": is_expired,
        "is_past_due": bool(ca.due_date and now > ca.due_date),
    }


@router.get("/instructor")
def instructor_list_assignments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    rows = (
        db.query(models.ChallengeAssignment)
        .filter(
            models.ChallengeAssignment.created_by == current_user.id,
            models.ChallengeAssignment.is_active == True,  # noqa: E712
        )
        .order_by(models.ChallengeAssignment.created_at.desc())
        .all()
    )
    out = []
    for ca in rows:
        studs = (
            db.query(models.ChallengeAssignmentStudent)
            .filter(models.ChallengeAssignmentStudent.assignment_id == ca.id)
            .all()
        )
        total = len(studs)
        passed_count = sum(1 for s in studs if s.status == "passed")
        failed_count = sum(1 for s in studs if s.status == "failed")
        in_progress_count = sum(1 for s in studs if s.status == "in_progress")
        not_started_count = sum(1 for s in studs if s.status == "assigned")
        expired_count = sum(1 for s in studs if s.status == "expired")
        out.append(
            {
                "id": ca.id,
                "title": ca.title,
                "challenge_slug": ca.challenge_slug,
                "challenge_name": _challenge_title(ca.challenge_slug),
                "time_limit_minutes": ca.time_limit_minutes,
                "due_date": ca.due_date.isoformat() if ca.due_date else None,
                "created_at": ca.created_at.isoformat() if ca.created_at else None,
                "total_students": total,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "in_progress_count": in_progress_count,
                "not_started_count": not_started_count,
                "expired_count": expired_count,
            }
        )
    return out


@router.get("/{assignment_id}/results")
def instructor_assignment_results(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    ca = db.query(models.ChallengeAssignment).filter(models.ChallengeAssignment.id == assignment_id).first()
    if not ca or ca.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    studs = (
        db.query(models.ChallengeAssignmentStudent, models.User)
        .join(models.User, models.User.id == models.ChallengeAssignmentStudent.student_id)
        .filter(models.ChallengeAssignmentStudent.assignment_id == assignment_id)
        .all()
    )
    return {
        "assignment": {
            "id": ca.id,
            "title": ca.title,
            "challenge_slug": ca.challenge_slug,
            "time_limit_minutes": ca.time_limit_minutes,
            "due_date": ca.due_date.isoformat() if ca.due_date else None,
        },
        "students": [
            {
                "email": u.email,
                "status": s.status,
                "time_used_seconds": s.time_used_seconds,
                "sandbox_passed": s.sandbox_passed,
                "score": s.score,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            }
            for s, u in studs
        ],
    }


@router.delete("/{assignment_id}")
def deactivate_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    ca = db.query(models.ChallengeAssignment).filter(models.ChallengeAssignment.id == assignment_id).first()
    if not ca or ca.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    ca.is_active = False
    db.commit()
    return {"message": "Deactivated."}
