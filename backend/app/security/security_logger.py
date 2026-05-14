import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from .. import models

logger = logging.getLogger(__name__)


class SecurityEventType:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    SQL_INJECTION_ATTEMPT = "SQL_INJECTION_ATTEMPT"
    XSS_ATTEMPT = "XSS_ATTEMPT"
    COMMAND_INJECTION_ATTEMPT = "COMMAND_INJECTION_ATTEMPT"
    CSRF_ATTEMPT = "CSRF_ATTEMPT"
    FILE_UPLOAD = "FILE_UPLOAD"
    PROJECT_SCAN = "PROJECT_SCAN"
    ATTACK_SIMULATION = "ATTACK_SIMULATION"
    FIX_SUBMISSION = "FIX_SUBMISSION"
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"
    SUSPICIOUS_BEHAVIOR = "SUSPICIOUS_BEHAVIOR"
    CHALLENGE_SQLI = "CHALLENGE_SQLI"
    CHALLENGE_CSRF = "CHALLENGE_CSRF"
    CHALLENGE_XSS = "CHALLENGE_XSS"
    CHALLENGE_COMMAND = "CHALLENGE_COMMAND"
    CHALLENGE_REDIRECT = "CHALLENGE_REDIRECT"
    CHALLENGE_BROKEN_AUTH = "CHALLENGE_BROKEN_AUTH"
    CHALLENGE_MISC = "CHALLENGE_MISC"
    CHALLENGE_AUTH = "CHALLENGE_AUTH"
    CHALLENGE_TRAVERSAL = "CHALLENGE_TRAVERSAL"
    CHALLENGE_XXE = "CHALLENGE_XXE"
    CHALLENGE_STORAGE = "CHALLENGE_STORAGE"


class SecuritySeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _safe_payload(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload[:3000]
    try:
        return json.dumps(payload, default=str)[:3000]
    except Exception:
        return str(payload)[:3000]


def detect_attack_severity(payload: str, default: str = SecuritySeverity.LOW) -> str:
    lower = (payload or "").lower()
    if any(x in lower for x in ["' or 1=1", "union select", "drop table", "--"]):
        return SecuritySeverity.HIGH
    if any(x in lower for x in ["<script", "onerror=", "javascript:"]):
        return SecuritySeverity.HIGH
    if any(x in lower for x in [";", "&&", "|", "cat /etc/passwd", "whoami"]):
        return SecuritySeverity.HIGH
    return default


def is_repeated_failed_login(db: Session, user_id: Optional[int], ip_address: Optional[str]) -> bool:
    since = datetime.utcnow() - timedelta(minutes=10)
    q = db.query(models.SecurityLog).filter(
        models.SecurityLog.event_type == SecurityEventType.LOGIN_FAILED,
        models.SecurityLog.context_type == "real",
        models.SecurityLog.created_at >= since,
    )
    if user_id:
        q = q.filter(models.SecurityLog.user_id == user_id)
    elif ip_address:
        q = q.filter(models.SecurityLog.ip_address == ip_address)
    return q.count() >= 5


def log_security_event(
    db: Session,
    event_type: str,
    severity: str,
    payload: Any = None,
    endpoint: Optional[str] = None,
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    context_type: str = "real",
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> models.SecurityLog:
    def _is_challenge_request(path: Optional[str], payload_data: Any, metadata_data: Optional[dict[str, Any]]) -> bool:
        request_path = (path or "").lower()
        if request_path.startswith("/api/challenges/") or request_path.startswith("/api/attack/"):
            return True
        if request_path.startswith("/api/auth/login"):
            challenge_value = None
            if request is not None:
                challenge_value = request.query_params.get("challenge")
            if not challenge_value and isinstance(payload_data, dict):
                challenge_value = payload_data.get("challenge")
            if not challenge_value and isinstance(metadata_data, dict):
                challenge_value = metadata_data.get("challenge")
            return bool(challenge_value)
        return False

    def _challenge_event_for(
        event: str,
        payload_data: Any,
        metadata_data: Optional[dict[str, Any]],
        endpoint_path: Optional[str],
    ) -> str:
        challenge_name = ""
        if isinstance(payload_data, dict):
            challenge_name = str(payload_data.get("challenge") or "").strip().lower()
        if not challenge_name and isinstance(metadata_data, dict):
            challenge_name = str(metadata_data.get("challenge") or "").strip().lower()
        endpoint_lower = (endpoint_path or "").lower()
        if not challenge_name:
            if "/csrf/" in endpoint_lower:
                challenge_name = "csrf"
            elif "/xxe/" in endpoint_lower:
                challenge_name = "xxe"
            elif "/traversal/" in endpoint_lower:
                challenge_name = "traversal"
            elif "/storage/" in endpoint_lower:
                challenge_name = "storage"
            elif endpoint_lower.endswith("/ping") or "command" in endpoint_lower:
                challenge_name = "command-injection"
            elif "broken-auth" in endpoint_lower:
                challenge_name = "broken-auth"
            elif "xss" in endpoint_lower:
                challenge_name = "xss"
            elif "sql" in endpoint_lower or "login" in endpoint_lower:
                challenge_name = "sql-injection"
        mapping = {
            "csrf": SecurityEventType.CHALLENGE_CSRF,
            "sql-injection": SecurityEventType.CHALLENGE_SQLI,
            "sqli": SecurityEventType.CHALLENGE_SQLI,
            "xss": SecurityEventType.CHALLENGE_XSS,
            "command-injection": SecurityEventType.CHALLENGE_COMMAND,
            "redirect": SecurityEventType.CHALLENGE_REDIRECT,
            "broken-auth": SecurityEventType.CHALLENGE_AUTH,
            "security-misc": SecurityEventType.CHALLENGE_AUTH,
            "traversal": SecurityEventType.CHALLENGE_TRAVERSAL,
            "xxe": SecurityEventType.CHALLENGE_XXE,
            "storage": SecurityEventType.CHALLENGE_STORAGE,
        }
        mapped = mapping.get(challenge_name, SecurityEventType.CHALLENGE_AUTH)
        if event == SecurityEventType.LOGIN_SUCCESS:
            return SecurityEventType.CHALLENGE_AUTH
        return mapped

    normalized_context = (context_type or "real").strip().lower()
    context_aliases = {
        "real_user_action": "real",
        "challenge_simulation": "challenge",
        "real": "real",
        "challenge": "challenge",
        "system": "system",
    }
    normalized_context = context_aliases.get(normalized_context, "system")

    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    endpoint_value = endpoint or (request.url.path if request else None)
    if _is_challenge_request(endpoint_value, payload, metadata):
        normalized_context = "challenge"
    if normalized_context == "challenge":
        event_type = _challenge_event_for(event_type, payload, metadata, endpoint_value)
    derived_session_id = session_id or (request.headers.get("x-session-id") if request else None) or str(user_id or "anon")
    derived_correlation_id = correlation_id or (request.headers.get("x-correlation-id") if request else None) or str(uuid.uuid4())
    geo_bucket = None
    if ip_address:
        if "." in ip_address:
            parts = ip_address.split(".")
            geo_bucket = ".".join(parts[:2]) if len(parts) >= 2 else ip_address
        elif ":" in ip_address:
            geo_bucket = ip_address.split(":")[0]
        else:
            geo_bucket = ip_address

    log_row = models.SecurityLog(
        user_id=user_id,
        event_type=event_type,
        severity=severity,
        payload=_safe_payload(payload),
        endpoint=endpoint_value,
        ip_address=ip_address,
        geo_bucket=geo_bucket,
        user_agent=user_agent,
        session_id=derived_session_id,
        correlation_id=derived_correlation_id,
        context_type=normalized_context,
        meta_data=metadata or {},
    )
    try:
        db.add(log_row)
        db.commit()
        db.refresh(log_row)
    except Exception as exc:
        # Keep primary platform flows available even if logging schema is not yet migrated.
        db.rollback()
        logger.warning(
            "Security log persistence failed, using console fallback. event=%s severity=%s context=%s error=%s payload=%s",
            event_type,
            severity,
            normalized_context,
            str(exc),
            _safe_payload(payload),
        )
    return log_row

