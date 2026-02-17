from fastapi import APIRouter, HTTPException, Depends, Form
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
    CommentResponse, ProgressResponse, CSRFAccountResponse
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
# HELPERS
# ==========================================
def mark_challenge_complete(db: Session, user_id: int, challenge_name: str):
    if not db.query(UserProgress).filter(UserProgress.user_id==user_id, UserProgress.challenge_id==challenge_name).first():
        db.add(UserProgress(user_id=user_id, challenge_id=challenge_name)); db.commit()

@router.get("/progress", response_model=List[ProgressResponse])
def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()