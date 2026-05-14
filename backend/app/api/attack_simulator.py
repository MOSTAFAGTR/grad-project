from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .. import schemas, models
from .auth import get_current_user
from ..attacks.templates import ATTACK_TEMPLATES, simulate_unsupported
from ..db.database import get_db
from ..security.learning_tracker import recalculate_learning_progress
from ..security.security_logger import (
    SecurityEventType,
    SecuritySeverity,
    detect_attack_severity,
    log_security_event,
)


router = APIRouter()


@router.post("/simulate", response_model=schemas.AttackSimulateResponse)
def simulate_attack(
    req: schemas.AttackSimulateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    normalized = (req.vulnerability_type or "").strip().lower().replace("-", " ").replace("_", " ")
    simulator = ATTACK_TEMPLATES.get(normalized)
    sev = detect_attack_severity(f"{req.vulnerability_type} {req.payload}", default=SecuritySeverity.MEDIUM)
    if not simulator:
        log_security_event(
            db=db,
            event_type=SecurityEventType.ATTACK_SIMULATION,
            severity=sev,
            payload={"type": req.vulnerability_type, "payload": req.payload},
            request=request,
            user_id=current_user.id,
            metadata={"supported": False},
            context_type="challenge",
        )
        recalculate_learning_progress(db, current_user.id)
        return schemas.AttackSimulateResponse(
            **simulate_unsupported(req.vulnerability_type, req.code, req.payload)
        )

    data = simulator(req.code, req.payload)
    log_security_event(
        db=db,
        event_type=SecurityEventType.ATTACK_SIMULATION,
        severity=sev,
        payload={"type": req.vulnerability_type, "payload": req.payload},
        request=request,
        user_id=current_user.id,
        metadata={"supported": True, "timeline_steps": len(data.get("timeline", []))},
        context_type="challenge",
    )
    recalculate_learning_progress(db, current_user.id)
    return schemas.AttackSimulateResponse(**data)

