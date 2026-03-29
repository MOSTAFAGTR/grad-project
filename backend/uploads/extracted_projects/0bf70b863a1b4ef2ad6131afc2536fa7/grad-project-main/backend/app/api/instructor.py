from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..db.database import get_db
from .auth import require_role
from ..security.learning_tracker import build_learning_progress_payload, TOTAL_CHALLENGES

router = APIRouter()


@router.get("/user/{user_id}/analytics")
def get_student_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    student = db.query(models.User).filter(models.User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="User not found")
    if student.role != "user":
        raise HTTPException(status_code=400, detail="Analytics are only available for student accounts")
    return build_learning_progress_payload(db, user_id)


@router.post("/user/{user_id}/reset-progress")
def reset_student_progress(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    student = db.query(models.User).filter(models.User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="User not found")
    if student.role != "user":
        raise HTTPException(status_code=400, detail="Reset is only allowed for student accounts")

    db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).delete()
    db.query(models.ChallengeState).filter(models.ChallengeState.user_id == user_id).delete()
    db.query(models.UserAnswer).filter(models.UserAnswer.user_id == user_id).delete()
    db.query(models.QuizAttempt).filter(models.QuizAttempt.user_id == user_id).delete()
    db.query(models.UserLearningProgress).filter(models.UserLearningProgress.user_id == user_id).delete()
    db.commit()

    return {"ok": True, "user_id": user_id, "total_challenges": TOTAL_CHALLENGES}
