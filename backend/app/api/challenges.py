from fastapi import APIRouter, HTTPException, Depends, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

from ..db.database import get_db
from .. import sandbox_runner 
from ..models import XSSComment, UserProgress, User
from .auth import get_current_user
from ..schemas import (
    LoginAttempt, CodeSubmission, CommentCreate,
    CommentResponse, ProgressResponse, CSRFAccountResponse,
    PingRequest,
)

router = APIRouter()

# ---------------------------------------------------------
# CONNECTION: SQL INJECTION DATABASE (challenge_db_sqli)
# ---------------------------------------------------------
SQLI_DB_URL = "mysql+pymysql://user:password@challenge_db_sqli/testdb"
sqli_engine = create_engine(SQLI_DB_URL)
SessionSQLi = sessionmaker(autocommit=False, autoflush=False, bind=sqli_engine)

# ---------------------------------------------------------
# CONNECTION: CSRF DATABASE (challenge_db_csrf)
# ---------------------------------------------------------
CSRF_DB_URL = "mysql+pymysql://user:password@challenge_db_csrf/csrfdb"
csrf_engine = create_engine(CSRF_DB_URL)
SessionCSRF = sessionmaker(autocommit=False, autoflush=False, bind=csrf_engine)

# ==========================================
# SQL INJECTION CHALLENGE
# ==========================================
@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt):
    db = SessionSQLi()
    query_str = f"SELECT * FROM users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    try:
        result = db.execute(text(query_str)).mappings().first()
        if result: return {"message": "Login successful!", "user": result['username']}
        else: raise HTTPException(401, "Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(400, "Database Error (SQL Syntax)")
    finally:
        db.close()

# ==========================================
# CSRF CHALLENGE (Uses External DB)
# ==========================================

@router.post("/csrf/reset")
def reset_csrf_accounts():
    """Resets the balances in the external CSRF database."""
    db = SessionCSRF()
    try:
        db.execute(text("UPDATE accounts SET balance=1000 WHERE username='Alice'"))
        db.execute(text("UPDATE accounts SET balance=0 WHERE username='Bob'"))
        db.commit()
        return {"message": "Accounts reset. Alice: $1000, Bob: $0"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"DB Error: {str(e)}")
    finally:
        db.close()

@router.get("/csrf/accounts", response_model=List[CSRFAccountResponse])
def get_csrf_accounts():
    """Fetches accounts from the external CSRF database."""
    db = SessionCSRF()
    try:
        results = db.execute(text("SELECT username, balance FROM accounts")).mappings().all()
        return results
    finally:
        db.close()

@router.post("/csrf/transfer")
def vulnerable_transfer(to_user: str = Form(...), amount: int = Form(...)):
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

        return {"message": f"Transferred ${amount} to {to_user}"}
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(500, f"Transfer Failed: {str(e)}")
    finally:
        db.close()

# ==========================================
# SANDBOX SUBMISSION
# ==========================================
@router.post("/submit-fix")
def submit_fix_sql(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-sql-injection")
    if success: mark_challenge_complete(db, current_user.id, "sql-injection")
    return {"success": success, "logs": logs}

@router.post("/submit-fix-xss")
def submit_fix_xss(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-xss")
    if success: mark_challenge_complete(db, current_user.id, "xss")
    return {"success": success, "logs": logs}

@router.post("/submit-fix-csrf")
def submit_fix_csrf(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-csrf")
    if success: mark_challenge_complete(db, current_user.id, "csrf")
    return {"success": success, "logs": logs}

# ==========================================
# COMMAND INJECTION CHALLENGE
# ==========================================
import subprocess

# Success marker: if this appears in command output, frontend treats as attack success
COMMAND_INJECTION_MARKER = "COMMAND_INJECTION_SUCCESS"

@router.post("/ping")
def vulnerable_ping(req: PingRequest):
    """
    Vulnerable endpoint: runs 'ping -c 1 <host>' with shell=True.
    Attacker can inject e.g. host='8.8.8.8; echo COMMAND_INJECTION_SUCCESS'
    """
    try:
       
        cmd = f"ping -c 1 {req.host}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return {"output": output, "success": COMMAND_INJECTION_MARKER in output}
    except subprocess.TimeoutExpired:
        return {"output": "Command timed out.", "success": False}
    except Exception as e:
        return {"output": str(e), "success": False}

@router.post("/submit-fix-command-injection")
def submit_fix_command_injection(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-command-injection")
    if success:
        mark_challenge_complete(db, current_user.id, "command-injection")
    return {"success": success, "logs": logs}

# ==========================================
# UNVALIDATED REDIRECT CHALLENGE
# ==========================================
# Vulnerable: redirects to any URL from query param (open redirect).
# Attack goal: craft a link that sends the victim to a malicious/success page.
@router.get("/redirect")
def vulnerable_redirect(url: str = Query(..., description="Redirect target")):
    """Vulnerable endpoint: redirects to the given URL without validation (open redirect)."""
    return RedirectResponse(url=url, status_code=302)

@router.post("/submit-fix-redirect")
def submit_fix_redirect(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-redirect")
    if success: mark_challenge_complete(db, current_user.id, "redirect")
    return {"success": success, "logs": logs}

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
    allowed = {"sql-injection", "xss", "csrf", "command-injection", "redirect"}
    if challenge_type not in allowed:
        raise HTTPException(400, f"Invalid challenge type. Must be one of: {allowed}")
    mark_challenge_complete(db, current_user.id, challenge_type)
    return {"ok": True}