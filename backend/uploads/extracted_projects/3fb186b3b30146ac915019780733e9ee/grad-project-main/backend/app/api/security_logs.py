from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..db.database import get_db
from .auth import require_role


router = APIRouter()

def _normalize_context_filter(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"real", "real_user_action"}:
        return "real"
    if v in {"challenge", "challenge_simulation"}:
        return "challenge"
    if v == "system":
        return "system"
    return None


@router.get("/logs")
def get_security_logs(
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    context_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    q = db.query(models.SecurityLog)
    if severity:
        q = q.filter(models.SecurityLog.severity == severity.upper())
    if event_type:
        q = q.filter(models.SecurityLog.event_type == event_type)
    if user_id:
        q = q.filter(models.SecurityLog.user_id == user_id)
    normalized_context = _normalize_context_filter(context_type)
    if normalized_context:
        if normalized_context == "real":
            q = q.filter(models.SecurityLog.context_type.in_(["real", "real_user_action"]))
        elif normalized_context == "challenge":
            q = q.filter(models.SecurityLog.context_type.in_(["challenge", "challenge_simulation"]))
        else:
            q = q.filter(models.SecurityLog.context_type == "system")
    if start_date:
        q = q.filter(models.SecurityLog.created_at >= start_date)
    if end_date:
        q = q.filter(models.SecurityLog.created_at <= end_date)

    total = q.count()
    rows = (
        q.order_by(models.SecurityLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "event_type": r.event_type,
                "severity": r.severity,
                "payload": r.payload,
                "endpoint": r.endpoint,
                "ip_address": r.ip_address,
                "geo_bucket": r.geo_bucket,
                "user_agent": r.user_agent,
                "session_id": r.session_id,
                "correlation_id": r.correlation_id,
                "context_type": r.context_type,
                "metadata": r.meta_data or {},
                "created_at": r.created_at,
            }
            for r in rows
        ],
    }


@router.get("/logs/stats")
def get_security_log_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    real_q = db.query(models.SecurityLog).filter(models.SecurityLog.context_type.in_(["real", "real_user_action"]))
    challenge_q = db.query(models.SecurityLog).filter(models.SecurityLog.context_type.in_(["challenge", "challenge_simulation"]))
    total_attacks = real_q.count()
    challenge_events = challenge_q.count()

    common_attack_row = (
        real_q.with_entities(models.SecurityLog.event_type, func.count(models.SecurityLog.id).label("c"))
        .group_by(models.SecurityLog.event_type)
        .order_by(func.count(models.SecurityLog.id).desc())
        .first()
    )
    top_users_rows = (
        real_q.with_entities(models.SecurityLog.user_id, func.count(models.SecurityLog.id).label("c"))
        .filter(models.SecurityLog.user_id.isnot(None))
        .group_by(models.SecurityLog.user_id)
        .order_by(func.count(models.SecurityLog.id).desc())
        .limit(5)
        .all()
    )

    timeline_rows = (
        db.query(models.SecurityLog.user_id, models.SecurityLog.event_type, models.SecurityLog.created_at, models.SecurityLog.context_type)
        .order_by(models.SecurityLog.created_at.desc())
        .limit(100)
        .all()
    )
    trend_rows = (
        real_q.with_entities(
            func.date(models.SecurityLog.created_at).label("day"),
            func.count(models.SecurityLog.id).label("count"),
        )
        .group_by(func.date(models.SecurityLog.created_at))
        .order_by(func.date(models.SecurityLog.created_at).desc())
        .limit(14)
        .all()
    )
    attack_frequency_rows = (
        real_q.with_entities(models.SecurityLog.event_type, func.count(models.SecurityLog.id).label("count"))
        .group_by(models.SecurityLog.event_type)
        .order_by(func.count(models.SecurityLog.id).desc())
        .all()
    )
    unique_attackers = (
        real_q.filter(models.SecurityLog.user_id.isnot(None))
        .with_entities(models.SecurityLog.user_id)
        .distinct()
        .count()
    )

    return {
        "total_attacks": total_attacks,
        "challenge_events": challenge_events,
        "most_common_attack": common_attack_row[0] if common_attack_row else None,
        "unique_attackers": unique_attackers,
        "top_users": [{"user_id": uid, "count": c} for uid, c in top_users_rows],
        "attack_trends": [{"day": str(day), "count": count} for day, count in trend_rows],
        "attack_frequency": [{"event_type": et, "count": c} for et, c in attack_frequency_rows],
        "timeline": [
            {"user_id": row.user_id, "event_type": row.event_type, "created_at": row.created_at, "context_type": row.context_type}
            for row in timeline_rows
        ],
    }

