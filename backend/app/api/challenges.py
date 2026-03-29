from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List
from pathlib import Path
import os
import hashlib
import xml.etree.ElementTree as ET
import re
import shlex

from ..db.database import get_db
from .. import sandbox_runner 
from ..models import XSSComment, UserProgress, User, ChallengeState, CSRFAccount
from .auth import get_current_user
from ..security.security_logger import (
    SecurityEventType,
    SecuritySeverity,
    detect_attack_severity,
    log_security_event,
)
from ..security.learning_tracker import recalculate_learning_progress
from ..schemas import (
    LoginAttempt, CodeSubmission, CommentCreate,
    CommentResponse, ProgressResponse, CSRFAccountResponse,
    PingRequest,
    ChallengeStateResponse, ChallengeStateUpdate, HintEntry, HintUseRequest,
)

router = APIRouter()
UPLOADS_ROOT = Path("/app/uploads").resolve()
INSECURE_USERS: dict[str, str] = {"alice": "password123", "bob": "qwerty", "admin": "admin123"}

# ---------------------------------------------------------
# CONNECTION: SQL INJECTION DATABASE (challenge_db_sqli)
# ---------------------------------------------------------
SQLI_DB_URL = os.getenv("SQLI_DATABASE_URL", "mysql+pymysql://user:password@challenge_db_sqli/testdb")
sqli_engine = create_engine(SQLI_DB_URL, pool_pre_ping=True)
SessionSQLi = sessionmaker(autocommit=False, autoflush=False, bind=sqli_engine)

# ---------------------------------------------------------
# CONNECTION: CSRF DATABASE (challenge_db_csrf)
# ---------------------------------------------------------
CSRF_DB_URL = os.getenv("CSRF_DATABASE_URL", "mysql+pymysql://user:password@challenge_db_csrf/csrfdb")
csrf_engine = create_engine(CSRF_DB_URL, pool_pre_ping=True)
SessionCSRF = sessionmaker(autocommit=False, autoflush=False, bind=csrf_engine)

try:
    from lxml import etree as LET  # type: ignore
except Exception:
    LET = None

def _challenge_source_file(challenge_dir: str) -> Path:
    return (Path("/app/challenges").resolve() / challenge_dir / "app.py").resolve()


def _challenge_slug_from_dir(challenge_dir: str) -> str:
    return challenge_dir.replace("challenge-", "", 1)


def _verify_fix_improvement(challenge_dir: str, submitted_code: str):
    source_file = _challenge_source_file(challenge_dir)
    if source_file.exists():
        with open(source_file, "r", encoding="utf-8", errors="ignore") as source_fp:
            vulnerable_source = source_fp.read()
    else:
        vulnerable_source = ""

    before_result = sandbox_runner.run_in_sandbox_detailed(vulnerable_source, challenge_dir)
    after_result = sandbox_runner.run_in_sandbox_detailed(submitted_code or "", challenge_dir)

    before_count = int(before_result.get("failures", 0)) + int(before_result.get("errors", 0))
    after_count = int(after_result.get("failures", 0)) + int(after_result.get("errors", 0))
    fixed = bool(after_result.get("success")) and after_count == 0
    improvement_score = (
        100
        if before_count == 0 and after_count == 0
        else max(0, min(100, int(((before_count - after_count) / max(before_count, 1)) * 100)))
    )
    challenge_slug = _challenge_slug_from_dir(challenge_dir)
    code_diff = (
        sandbox_runner.generate_code_diff(vulnerable_source, submitted_code or "", challenge_slug)
        if fixed and vulnerable_source
        else []
    )
    return {
        "fixed": fixed,
        "improvement_score": improvement_score,
        "before_vulnerabilities": before_count,
        "after_vulnerabilities": after_count,
        "test_output": str(after_result.get("logs") or ""),
        "code_diff": code_diff,
    }


def _extract_external_entities(xml_data: str) -> dict[str, str]:
    entities: dict[str, str] = {}
    pattern = r"<!ENTITY\s+([A-Za-z0-9_:-]+)\s+SYSTEM\s+['\"]file://([^'\"]+)['\"]>"
    for name, path in re.findall(pattern, xml_data, flags=re.IGNORECASE):
        try:
            entities[name] = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            entities[name] = ""
    return entities


class _XXEFileResolver(LET.Resolver if LET is not None else object):
    """
    Restrict XXE file entity resolution to controlled lab targets.
    """

    def resolve(self, system_url, public_id, context):  # type: ignore[override]
        if LET is None:
            return None

        if not isinstance(system_url, str) or not system_url.startswith("file://"):
            return self.resolve_string("", context)

        raw_path = system_url[len("file://") :]
        target = Path(raw_path).resolve()
        allowed = target == Path("/etc/passwd").resolve()
        if not allowed:
            uploads_real = UPLOADS_ROOT.resolve()
            target_real = target.resolve()
            allowed = target_real == uploads_real or str(target_real).startswith(str(uploads_real) + os.sep)
        if not allowed or not target.exists() or target.is_dir():
            return self.resolve_string("", context)

        try:
            data = target.read_text(encoding="utf-8", errors="ignore")[:5000]
        except Exception:
            data = ""
        return self.resolve_string(data, context)


# ==========================================
# SQL INJECTION CHALLENGE
# ==========================================
@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt, db_main: Session = Depends(get_db)):
    db = SessionSQLi()
    query_str = f"SELECT * FROM users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    sev = detect_attack_severity(f"{attempt.username} {attempt.password}", default=SecuritySeverity.MEDIUM)
    try:
        result = db.execute(text(query_str)).mappings().first()
        if result:
            log_security_event(
                db=db_main,
                event_type=SecurityEventType.CHALLENGE_SQLI,
                severity=sev,
                payload={"username": attempt.username, "password": attempt.password},
                metadata={"result": "success", "challenge": "sqli-login"},
                context_type="challenge_simulation",
            )
            return {"message": "Login successful!", "user": result['username']}
        else: raise HTTPException(401, "Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(400, "Database Error (SQL Syntax)")
    finally:
        db.close()


# ==========================================
# XSS CHALLENGE
# ==========================================
@router.get("/xss/comments", response_model=List[CommentResponse])
def get_xss_comments(db: Session = Depends(get_db)):
    return db.query(XSSComment).order_by(XSSComment.id.asc()).all()


@router.post("/xss/comments", response_model=CommentResponse)
def create_xss_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    request: Request = None,
):
    row = XSSComment(author=(comment.author or "Guest")[:255], content=comment.content or "")
    db.add(row)
    db.commit()
    db.refresh(row)
    log_security_event(
        db=db,
        event_type=SecurityEventType.CHALLENGE_XSS,
        severity=detect_attack_severity(comment.content, default=SecuritySeverity.MEDIUM),
        payload={"author": row.author, "content_preview": (row.content or "")[:200]},
        request=request,
        metadata={"challenge": "xss", "action": "comment_post"},
        context_type="challenge_simulation",
    )
    return row


@router.delete("/xss/comments")
def clear_xss_comments(db: Session = Depends(get_db)):
    db.query(XSSComment).delete()
    db.commit()
    return {"ok": True}

# ==========================================
# CSRF CHALLENGE (Uses External DB)
# ==========================================

@router.post("/csrf/reset")
def reset_csrf_accounts(db_main: Session = Depends(get_db)):
    """Resets the balances in the external CSRF database."""
    db = SessionCSRF()
    try:
        db.execute(text("UPDATE accounts SET balance=1000 WHERE username='Alice'"))
        db.execute(text("UPDATE accounts SET balance=0 WHERE username='Bob'"))
        db.commit()
        for username, balance in [("Alice", 1000), ("Bob", 0)]:
            row = db_main.query(CSRFAccount).filter(CSRFAccount.username == username).first()
            if not row:
                row = CSRFAccount(username=username, balance=balance)
                db_main.add(row)
            else:
                row.balance = balance
        db_main.commit()
        return {"message": "Accounts reset. Alice: $1000, Bob: $0"}
    except Exception as e:
        db.rollback()
        db_main.rollback()
        raise HTTPException(500, f"DB Error: {str(e)}")
    finally:
        db.close()

@router.get("/csrf/accounts", response_model=List[CSRFAccountResponse])
def get_csrf_accounts(db_main: Session = Depends(get_db)):
    """Fetches accounts from the external CSRF database."""
    db = SessionCSRF()
    try:
        results = db.execute(text("SELECT username, balance FROM accounts")).mappings().all()
        for item in results:
            row = db_main.query(CSRFAccount).filter(CSRFAccount.username == item["username"]).first()
            if not row:
                db_main.add(CSRFAccount(username=item["username"], balance=item["balance"]))
            else:
                row.balance = item["balance"]
        db_main.commit()
        return results
    except Exception:
        db_main.rollback()
        # Fallback to ORM mirror when external challenge DB is unavailable.
        return db_main.query(CSRFAccount).order_by(CSRFAccount.username.asc()).all()
    finally:
        db.close()

@router.post("/csrf/transfer")
def vulnerable_transfer(to_user: str = Form(...), amount: int = Form(...), db_main: Session = Depends(get_db)):
    """
    Vulnerable Transfer Endpoint (External DB).
    Accepts HTML Form Data (application/x-www-form-urlencoded).
    """
    db = SessionCSRF()
    try:
        # Check Sender (Alice)
        alice = db.execute(text("SELECT balance FROM accounts WHERE username='Alice'")).mappings().first()
        
        if not alice: raise HTTPException(404, "Sender Alice not found")
        if alice['balance'] < amount: raise HTTPException(400, "Insufficient funds")

        # Check Recipient
        recipient = db.execute(text(f"SELECT * FROM accounts WHERE username='{to_user}'")).mappings().first()
        if not recipient: raise HTTPException(404, "Recipient not found")

        # Perform Transfer
        db.execute(text(f"UPDATE accounts SET balance = balance - {amount} WHERE username='Alice'"))
        db.execute(text(f"UPDATE accounts SET balance = balance + {amount} WHERE username='{to_user}'"))
        db.commit()
        for username, delta in [("Alice", -amount), (to_user, amount)]:
            row = db_main.query(CSRFAccount).filter(CSRFAccount.username == username).first()
            if not row:
                row = CSRFAccount(username=username, balance=max(delta, 0))
                db_main.add(row)
            else:
                row.balance = (row.balance or 0) + delta
        db_main.commit()
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_CSRF,
            severity=SecuritySeverity.HIGH,
            payload={"to_user": to_user, "amount": amount},
            metadata={"result": "transfer_executed", "challenge": "csrf"},
            context_type="challenge_simulation",
        )

        return {"message": f"Transferred ${amount} to {to_user}"}
    except Exception as e:
        db.rollback()
        db_main.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(500, f"Transfer Failed: {str(e)}")
    finally:
        db.close()

# ==========================================
# SANDBOX SUBMISSION
# ==========================================
@router.post("/submit-fix")
def submit_fix_sql(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-sql-injection", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "sql-injection")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "sql-injection"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    log_security_event(
        db=db,
        event_type=SecurityEventType.SANDBOX_EXECUTION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.HIGH,
        payload={"challenge": "sql-injection"},
        user_id=current_user.id,
        metadata={"success": success, "logs_preview": (logs or "")[:500]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}

@router.post("/submit-fix-xss")
def submit_fix_xss(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-xss", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "xss")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "xss"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}

@router.post("/submit-fix-csrf")
def submit_fix_csrf(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-csrf", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "csrf")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "csrf"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}

# ==========================================
# COMMAND INJECTION CHALLENGE
# ==========================================
import subprocess

# Success marker: if this appears in command output, frontend treats as attack success
COMMAND_INJECTION_MARKER = "COMMAND_INJECTION_SUCCESS"


def _safe_ping_with_simulated_injection(host_input: str) -> tuple[str, bool]:
    """
    Execute only the primary ping target without shell expansion.
    If an injected segment is present, simulate command-injection success
    when the payload tries to echo the marker string.
    """
    raw = (host_input or "").strip()
    for sep in ("&&", "||", ";", "|"):
        if sep in raw:
            host_target, injected = raw.split(sep, 1)
            host_target = host_target.strip()
            injected = injected.strip()
            break
    else:
        host_target = raw
        injected = ""

    if not host_target:
        raise HTTPException(status_code=400, detail="Host is required")

    result = subprocess.run(
        ["ping", "-c", "1", host_target],
        shell=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    output = (result.stdout or "") + (result.stderr or "")

    simulated_success = False
    if injected:
        try:
            tokens = shlex.split(injected)
        except ValueError:
            tokens = [injected]

        if COMMAND_INJECTION_MARKER in injected:
            simulated_success = True

        simulated_line = (
            f"\n[simulated] injected segment detected: {injected[:200]}\n"
            f"[simulated] shell execution blocked for safety.\n"
        )
        if tokens and tokens[0] == "echo" and len(tokens) > 1:
            simulated_line += " ".join(tokens[1:]) + "\n"
        if simulated_success and COMMAND_INJECTION_MARKER not in simulated_line:
            simulated_line += f"{COMMAND_INJECTION_MARKER}\n"
        output += simulated_line

    return output, simulated_success

@router.post("/ping")
def vulnerable_ping(req: PingRequest, db_main: Session = Depends(get_db)):
    """
    Training endpoint for command-injection payloads.
    Real shell execution of injected segments is blocked for platform safety.
    """
    try:
        # Safety guardrail: keep payload size bounded and reject multiline input.
        # This preserves challenge behavior while reducing abuse potential.
        if len(req.host or "") > 200 or "\n" in req.host or "\r" in req.host:
            raise HTTPException(status_code=400, detail="Invalid host payload")
       
        output, simulated_success = _safe_ping_with_simulated_injection(req.host)
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_COMMAND,
            severity=detect_attack_severity(req.host, default=SecuritySeverity.MEDIUM),
            payload={"host": req.host},
            metadata={"success_marker": simulated_success, "challenge": "command-injection"},
            context_type="challenge_simulation",
        )
        return {"output": output, "success": simulated_success}
    except subprocess.TimeoutExpired:
        return {"output": "Command timed out.", "success": False}
    except Exception as e:
        return {"output": str(e), "success": False}

@router.post("/submit-fix-command-injection")
def submit_fix_command_injection(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-command-injection", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "command-injection")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "command-injection"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}


@router.post("/submit-fix-auth")
def submit_fix_auth(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-broken-auth", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "broken-auth")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "broken-auth"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}


@router.post("/submit-fix-misc")
def submit_fix_misc(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-security-misc", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "security-misc")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "security-misc"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}

# ==========================================
# UNVALIDATED REDIRECT CHALLENGE
# ==========================================
# Vulnerable: redirects to any URL from query param (open redirect).
# Attack goal: craft a link that sends the victim to a malicious/success page.
@router.get("/redirect")
def vulnerable_redirect(
    url: str = Query(..., description="Redirect target"),
    db_main: Session = Depends(get_db),
    request: Request = None,
):
    """Vulnerable endpoint: redirects to the given URL without validation (open redirect)."""
    log_security_event(
        db=db_main,
        event_type=SecurityEventType.CHALLENGE_REDIRECT,
        severity=SecuritySeverity.MEDIUM,
        payload={"url": url},
        request=request,
        metadata={"challenge": "redirect"},
        context_type="challenge_simulation",
    )
    return RedirectResponse(url=url, status_code=302)

@router.post("/submit-fix-redirect")
def submit_fix_redirect(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-redirect", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "redirect")
        recalculate_learning_progress(db, current_user.id)
    log_security_event(
        db=db,
        event_type=SecurityEventType.FIX_SUBMISSION,
        severity=SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM,
        payload={"challenge": "redirect"},
        user_id=current_user.id,
        metadata={"sandbox_success": success, "improvement_score": verification["improvement_score"]},
        context_type="challenge_simulation",
    )
    return {"success": success, "logs": logs, **verification}


# ==========================================
# NEW CHALLENGE FIX SUBMISSIONS
# ==========================================
@router.post("/submit-fix-traversal")
def submit_fix_traversal(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-directory-traversal", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "directory-traversal")
        recalculate_learning_progress(db, current_user.id)
    return {"success": success, "logs": logs, **verification}


@router.post("/submit-fix-xxe")
def submit_fix_xxe(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-xxe", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "xxe")
        recalculate_learning_progress(db, current_user.id)
    return {"success": success, "logs": logs, **verification}


@router.post("/submit-fix-storage")
def submit_fix_storage(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = _verify_fix_improvement("challenge-insecure-storage", submission.code)
    success = bool(verification.get("fixed"))
    logs = str(verification.get("test_output") or "")
    if success:
        mark_challenge_complete(db, current_user.id, "insecure-storage")
        recalculate_learning_progress(db, current_user.id)
    return {"success": success, "logs": logs, **verification}


# ==========================================
# DIRECTORY TRAVERSAL CHALLENGE
# ==========================================
@router.get("/traversal/read")
def traversal_read_file(
    file: str = Query(..., description="File name/path"),
    secure: bool = Query(False),
    db_main: Session = Depends(get_db),
    request: Request = None,
):
    """Vulnerable path joins user input to base dir and reads the file — no payload classification."""
    base = str(UPLOADS_ROOT.resolve())
    os.makedirs(base, exist_ok=True)
    full_path = os.path.join(base, file)
    requested_path = file
    if secure:
        base_real = os.path.realpath(base)
        target_real = os.path.realpath(full_path)
        if target_real != base_real and not target_real.startswith(base_real + os.sep):
            raise HTTPException(status_code=403, detail="Blocked by secure path normalization")
    try:
        if not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()[:5000]
        resolved_path = os.path.realpath(full_path)
        response = {
            "secure_mode": secure,
            "request_path": requested_path,
            "accessed_path": resolved_path,
            "resolved_path": resolved_path,
            "content": content,
        }
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_TRAVERSAL,
            severity=SecuritySeverity.MEDIUM,
            payload={"file": file, "secure": secure},
            request=request,
            metadata={"challenge": "traversal"},
            context_type="challenge",
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# XXE CHALLENGE
# ==========================================
@router.post("/xxe/parse")
def parse_xml(payload: dict, db_main: Session = Depends(get_db), request: Request = None):
    xml_data = payload.get("xml") or ""
    secure = bool(payload.get("secure", False))
    if secure:
        # Secure mode: block DTD and external entities entirely.
        if "<!DOCTYPE" in xml_data.upper() or "<!ENTITY" in xml_data.upper():
            return {
                "secure_mode": True,
                "xml_input": xml_data,
                "parsed_result": "External entities are blocked by secure parser policy.",
                "extracted_sensitive_data": None,
            }
        try:
            root = ET.fromstring(xml_data)
            return {
                "secure_mode": True,
                "xml_input": xml_data,
                "parsed_result": ET.tostring(root, encoding="unicode"),
                "extracted_sensitive_data": None,
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Secure parse error: {e}")

    # Vulnerable mode: use a real XML parser that resolves entities.
    if LET is None:
        raise HTTPException(status_code=500, detail="XXE parser unavailable: lxml is not installed")

    try:
        parser = LET.XMLParser(resolve_entities=True, load_dtd=True, no_network=True, recover=True)
        parser.resolvers.add(_XXEFileResolver())
        root = LET.fromstring(xml_data.encode("utf-8"), parser=parser)
        parsed_output = LET.tostring(root, encoding="unicode")[:5000]
        extracted = parsed_output if any(marker in parsed_output for marker in ["root:x:", "daemon:x:", "/bin/", "nobody:"]) else None

        response = {
            "secure_mode": False,
            "xml_input": xml_data,
            "parsed_result": parsed_output,
            "parsed_output": parsed_output,
            "extracted_sensitive_data": extracted,
            "sensitive_data": extracted,
        }
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_XXE,
            severity=SecuritySeverity.MEDIUM if extracted else SecuritySeverity.LOW,
            payload={"xml_preview": xml_data[:300], "secure": secure},
            request=request,
            metadata={"challenge": "xxe", "real_parser": "lxml"},
            context_type="challenge",
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")


# ==========================================
# INSECURE STORAGE CHALLENGE
# ==========================================
@router.post("/storage/register")
def insecure_storage_register(payload: dict, db_main: Session = Depends(get_db), request: Request = None):
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    secure = bool(payload.get("secure", False))
    if not username or not password:
        raise HTTPException(status_code=400, detail="username/password required")
    stored_value = hashlib.sha256(password.encode()).hexdigest() if secure else password
    INSECURE_USERS[username] = stored_value
    response = {
        "ok": True,
        "username": username,
        "secure_mode": secure,
        "stored_value_preview": f"{stored_value[:24]}..." if secure else stored_value,
        "risk": "Low (hashed password)" if secure else "High (plaintext password)",
    }
    log_security_event(
        db=db_main,
        event_type=SecurityEventType.CHALLENGE_STORAGE,
        severity=SecuritySeverity.HIGH if not secure else SecuritySeverity.LOW,
        payload={"username": username, "secure": secure},
        request=request,
        metadata={"challenge": "storage", "action": "register"},
        context_type="challenge",
    )
    return response


@router.get("/storage/dump")
def insecure_storage_dump(
    secure: bool = Query(False),
    db_main: Session = Depends(get_db),
    request: Request = None,
):
    if secure:
        users = [
            {"username": u, "password_hash": hashlib.sha256(p.encode()).hexdigest() if len(p) < 64 else p}
            for u, p in INSECURE_USERS.items()
        ]
        response = {
            "secure_mode": True,
            "users": users,
            "exposure_risk": "Passwords are hashed; direct credential disclosure is reduced.",
        }
        log_security_event(
            db=db_main,
            event_type=SecurityEventType.CHALLENGE_STORAGE,
            severity=SecuritySeverity.LOW,
            payload={"secure": True},
            request=request,
            metadata={"challenge": "storage", "action": "dump"},
            context_type="challenge",
        )
        return response
    users = [{"username": u, "password": p} for u, p in INSECURE_USERS.items()]
    response = {
        "secure_mode": False,
        "users": users,
        "exposure_risk": "Dump returns stored credential material as persisted.",
    }
    log_security_event(
        db=db_main,
        event_type=SecurityEventType.CHALLENGE_STORAGE,
        severity=SecuritySeverity.MEDIUM,
        payload={"secure": False},
        request=request,
        metadata={"challenge": "storage", "action": "dump"},
        context_type="challenge",
    )
    return response

# ==========================================
# HELPERS
# ==========================================
def mark_challenge_complete(db: Session, user_id: int, challenge_name: str):
    if not db.query(UserProgress).filter(UserProgress.user_id==user_id, UserProgress.challenge_id==challenge_name).first():
        db.add(UserProgress(user_id=user_id, challenge_id=challenge_name)); db.commit()

@router.get("/progress", response_model=List[ProgressResponse])
def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()

@router.post("/mark-attack-complete")
def mark_attack_complete(
    challenge_type: str = Query(..., description="Challenge type: sql-injection, xss, csrf, command-injection, redirect"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark that the current user successfully completed an attack simulation."""
    allowed = {
        "sql-injection",
        "xss",
        "csrf",
        "command-injection",
        "redirect",
        "broken-auth",
        "security-misc",
        "directory-traversal",
        "xxe",
        "insecure-storage",
    }
    if challenge_type not in allowed:
        raise HTTPException(400, f"Invalid challenge type. Must be one of: {allowed}")
    mark_challenge_complete(db, current_user.id, challenge_type)
    recalculate_learning_progress(db, current_user.id)
    return {"ok": True}


# ==========================================
# CHALLENGE STATE & HINTS (GAME LAYER)
# ==========================================

def _get_or_create_state(db: Session, user_id: int, challenge_id: str) -> ChallengeState:
    state = (
        db.query(ChallengeState)
        .filter(ChallengeState.user_id == user_id, ChallengeState.challenge_id == challenge_id)
        .first()
    )
    if not state:
        state = ChallengeState(user_id=user_id, challenge_id=challenge_id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/state", response_model=ChallengeStateResponse)
def get_challenge_state(
    challenge_id: str = Query(..., description="Challenge id, e.g. csrf, broken-auth, redirect"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state = _get_or_create_state(db, current_user.id, challenge_id)
    return state


@router.post("/state/update", response_model=ChallengeStateResponse)
def update_challenge_state(
    update: ChallengeStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state = _get_or_create_state(db, current_user.id, update.challenge_id)
    if update.current_stage:
        state.current_stage = update.current_stage
    if update.attempt_delta:
        state.attempt_count = (state.attempt_count or 0) + update.attempt_delta
    if update.time_spent_delta:
        state.time_spent_seconds = (state.time_spent_seconds or 0) + update.time_spent_delta
    from datetime import datetime as _dt
    state.last_updated = _dt.utcnow()
    db.commit()
    db.refresh(state)
    return state


_HINTS: dict[str, list[dict[str, object]]] = {
    "csrf": [
        {"level": 1, "text": "Look for an action that changes server state without validation.", "penalty": 0},
        {"level": 2, "text": "Think about how a victim's browser might send a request without them clicking a bank button.", "penalty": 5},
        {"level": 3, "text": "Consider abusing an auto-submitting mechanism in HTML that can talk to the vulnerable transfer endpoint.", "penalty": 10},
    ],
    "broken-auth": [
        {"level": 1, "text": "Can you log in without knowing the real password?", "penalty": 0},
        {"level": 2, "text": "Try manipulating the login input so that the server's check always evaluates as true.", "penalty": 5},
        {"level": 3, "text": "Think about classic injection techniques against authentication queries, but work the exact payload out yourself.", "penalty": 10},
    ],
    "security-misc": [
        {"level": 1, "text": "Real apps sometimes expose debug or admin endpoints.", "penalty": 0},
        {"level": 2, "text": "Try calling endpoints that are not linked from the UI or that sound internal/administrative.", "penalty": 5},
        {"level": 3, "text": "Hunt for a configuration or debug endpoint that should never be reachable in production.", "penalty": 10},
    ],
    "directory-traversal": [
        {"level": 1, "text": "Try using ../ in the file name parameter.", "penalty": 0},
        {"level": 2, "text": "Your goal is to escape the intended files directory.", "penalty": 5},
        {"level": 3, "text": "Fix by normalizing paths and rejecting paths outside the base directory.", "penalty": 10},
    ],
    "xxe": [
        {"level": 1, "text": "Use a DOCTYPE payload with an external entity.", "penalty": 0},
        {"level": 2, "text": "Try reading file:///etc/passwd through an entity reference.", "penalty": 5},
        {"level": 3, "text": "Fix by disabling external entities and blocking DTD processing.", "penalty": 10},
    ],
    "insecure-storage": [
        {"level": 1, "text": "Register a user, then dump storage.", "penalty": 0},
        {"level": 2, "text": "Look for plaintext passwords in the dump output.", "penalty": 5},
        {"level": 3, "text": "Fix by hashing before storing credentials.", "penalty": 10},
    ],
}


@router.get("/hints", response_model=list[HintEntry])
def get_hints(
    challenge_id: str = Query(..., description="Challenge id, e.g. csrf, broken-auth, security-misc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hints = _HINTS.get(challenge_id, [])
    state = _get_or_create_state(db, current_user.id, challenge_id)
    # Unlock up to hints_used + 1 (progressive reveal)
    unlock_count = min(len(hints), (state.hints_used or 0) + 1)
    return [
        HintEntry(id=i, text=h["text"] if i < unlock_count else "Locked hint", unlocked=i < unlock_count)
        for i, h in enumerate(hints, start=1)
    ]


@router.post("/hints/use", response_model=ChallengeStateResponse)
def use_hint(
    req: HintUseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hints = _HINTS.get(req.challenge_id, [])
    if req.hint_id < 1 or req.hint_id > len(hints):
        raise HTTPException(400, "Invalid hint id for this challenge")
    state = _get_or_create_state(db, current_user.id, req.challenge_id)
    state.hints_used = (state.hints_used or 0) + 1
    from datetime import datetime as _dt
    state.last_updated = _dt.utcnow()
    db.commit()
    db.refresh(state)
    recalculate_learning_progress(db, current_user.id)
    return state