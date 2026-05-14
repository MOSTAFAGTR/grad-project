from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models import User
from .auth import get_current_user
from ..schemas import ChallengeStateUpdate
from . import challenges as challenges_api


router = APIRouter()


@router.post("/calc/interest")
def calc_interest(
    principal: float = Form(...),
    interestRate: float = Form(...),
    years: int = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    Simple bank interest calculator used for the Security Misconfiguration challenge.
    Intentionally has no rate limiting or auditing – but no direct vuln here.
    """
    try:
        amount = principal * ((1 + interestRate / 100.0) ** years)
    except Exception as e:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
    return {"amount": round(amount, 2)}


@router.get("/admin/config")
def exposed_admin_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deliberately exposed admin/config endpoint for the Security Misconfiguration challenge.
    No authentication/authorization checks – any logged-in user can read it.
    """
    # Mark progress via the shared challenge state helper
    challenges_api._get_or_create_state(db, current_user.id, "security-misc")
    challenges_api.update_challenge_state(
        ChallengeStateUpdate(challenge_id="security-misc", current_stage="config-exposed", attempt_delta=1),
        db=db,
        current_user=current_user,
    )

    # Build a fake but realistic config snapshot
    env_sample = {k: v for k, v in os.environ.items() if k.upper().startswith(("DB_", "SECRET", "API_", "APP_"))}
    config = {
        "app_name": "SCALE Bank Interest Service",
        "debug": True,
        "database_url": os.getenv("DB_URL", "mysql://user:password@db/scale_db"),
        "secret_key": os.getenv("SECRET_KEY", "insecure_default_secret_key"),
        "env_sample": env_sample,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return config

