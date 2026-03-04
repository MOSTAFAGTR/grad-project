from fastapi import APIRouter, HTTPException, Depends, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from typing import List
import subprocess

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
# CONNECTIONS: EXTERNAL CHALLENGE DATABASES
# ---------------------------------------------------------
SQLI_DB_URL = "mysql+pymysql://user:password@challenge_db_sqli/testdb"
sqli_engine = create_engine(SQLI_DB_URL)
SessionSQLi = sessionmaker(autocommit=False, autoflush=False, bind=sqli_engine)

CSRF_DB_URL = "mysql+pymysql://user:password@challenge_db_csrf/csrfdb"
csrf_engine = create_engine(CSRF_DB_URL)
SessionCSRF = sessionmaker(autocommit=False, autoflush=False, bind=csrf_engine)

# ==========================================
# SQL INJECTION & BROKEN AUTHENTICATION
# ==========================================
@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt):
    """
    Shared endpoint for SQLi and Broken Auth simulation.
    VULNERABILITY:
    1. SQLi: Raw string concatenation in query.
    2. Broken Auth: No rate limiting (used by Brute Force attack page).
    """
    # BROKEN AUTH SIMULATION: Allow the brute-force password to succeed
    if attempt.username == "admin" and attempt.password == "complex_password_123":
        return {"message": "Login successful!", "user": "admin"}

    db = SessionSQLi()
    query_str = f"SELECT * FROM users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    try:
        result = db.execute(text(query_str)).mappings().first()
        if result: 
            return {"message": "Login successful!", "user": result['username']}
        else: 
            raise HTTPException(401, "Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(400, "Database Error (SQL Syntax)")
    finally:
        db.close()

# ==========================================
# SECURITY MISCONFIGURATION
# ==========================================


@router.get("/debug-leak")
def debug_leak(input: str = None):
    if input:
        raise HTTPException(
            status_code=500,
            detail={
                "leak": {
                    "DEBUG": True,
                    "ENV": "development",
                    "SECRET_KEY": os.getenv("SECRET_KEY"),
                    "DATABASE": os.getenv("SQLALCHEMY_DATABASE_URI"),
                    "ALLOWED_HOSTS": "*",
                    "SERVER_SOFTWARE": "Flask/2.3.2 (Python 3.9)"
                }
            }
        )
    return {"message": "Safe response"}


# ==========================================
# CSRF CHALLENGE (Uses External DB)
# ==========================================
@router.post("/csrf/reset")
def reset_csrf_accounts():
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
    db = SessionCSRF()
    try:
        results = db.execute(text("SELECT username, balance FROM accounts")).mappings().all()
        return results
    finally:
        db.close()

@router.post("/csrf/transfer")
def vulnerable_transfer(to_user: str = Form(...), amount: int = Form(...)):
    db = SessionCSRF()
    try:
        alice = db.execute(text("SELECT balance FROM accounts WHERE username='Alice'")).mappings().first()
        if not alice or alice['balance'] < amount:
            raise HTTPException(400, "Insufficient funds")

        db.execute(text(f"UPDATE accounts SET balance = balance - {amount} WHERE username='Alice'"))
        db.execute(text(f"UPDATE accounts SET balance = balance + {amount} WHERE username='{to_user}'"))
        db.commit()
        return {"message": f"Transferred ${amount} to {to_user}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Transfer Failed: {str(e)}")
    finally:
        db.close()

# ==========================================
# COMMAND INJECTION
# ==========================================
COMMAND_INJECTION_MARKER = "COMMAND_INJECTION_SUCCESS"

@router.post("/ping")
def vulnerable_ping(req: PingRequest):
    try:
        cmd = f"ping -c 1 {req.host}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = (result.stdout or "") + (result.stderr or "")
        return {"output": output, "success": COMMAND_INJECTION_MARKER in output}
    except Exception as e:
        return {"output": str(e), "success": False}

# ==========================================
# UNVALIDATED REDIRECT
# ==========================================
@router.get("/redirect")
def vulnerable_redirect(url: str = Query(..., description="Redirect target")):
    return RedirectResponse(url=url, status_code=302)

# ==========================================
# SANDBOX SUBMISSIONS (FIX PHASE)
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

@router.post("/submit-fix-auth")
def submit_fix_auth(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-broken-auth")
    if success: mark_challenge_complete(db, current_user.id, "broken-auth")
    return {"success": success, "logs": logs}

@router.post("/submit-fix-misc")
def submit_fix_misc(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-security-misc")
    if success: mark_challenge_complete(db, current_user.id, "security-misc")
    return {"success": success, "logs": logs}

@router.post("/submit-fix-command-injection")
def submit_fix_command_injection(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-command-injection")
    if success: mark_challenge_complete(db, current_user.id, "command-injection")
    return {"success": success, "logs": logs}

@router.post("/submit-fix-redirect")
def submit_fix_redirect(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success, logs = sandbox_runner.run_in_sandbox(submission.code, "challenge-redirect")
    if success: mark_challenge_complete(db, current_user.id, "redirect")
    return {"success": success, "logs": logs}

# ==========================================
# HELPERS & PROGRESS
# ==========================================
@router.post("/xss/comments")
def post_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    new = XSSComment(author=comment.author, content=comment.content)
    db.add(new); db.commit(); db.refresh(new)
    return new

@router.get("/xss/comments", response_model=List[CommentResponse])
def get_comments(db: Session = Depends(get_db)): 
    return db.query(XSSComment).all()

@router.delete("/xss/comments")
def clear_comments(db: Session = Depends(get_db)):
    db.query(XSSComment).delete(); db.commit()
    return {"message": "Cleared"}

def mark_challenge_complete(db: Session, user_id: int, challenge_name: str):
    if not db.query(UserProgress).filter(UserProgress.user_id==user_id, UserProgress.challenge_id==challenge_name).first():
        db.add(UserProgress(user_id=user_id, challenge_id=challenge_name)); db.commit()

@router.get("/progress", response_model=List[ProgressResponse])
def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()

@router.post("/mark-attack-complete")
def mark_attack_complete(
    challenge_type: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mark_challenge_complete(db, current_user.id, challenge_type)
    return {"ok": True}