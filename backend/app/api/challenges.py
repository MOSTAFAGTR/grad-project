from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

from ..db.database import get_db
from .. import sandbox_runner 
from ..models import XSSComment, UserProgress, User
from .auth import get_current_user
from ..schemas import LoginAttempt, CodeSubmission, CommentCreate, CommentResponse, ProgressResponse

router = APIRouter()

CHALLENGE_DB_URL = "mysql+pymysql://user:password@challenge_db_sqli/testdb"
challenge_engine = create_engine(CHALLENGE_DB_URL)
SessionLocalChallenge = sessionmaker(autocommit=False, autoflush=False, bind=challenge_engine)

@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt):
    db = SessionLocalChallenge()
    query_str = f"SELECT * FROM users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    print(f"SQL Exec: {query_str}")
    try:
        result = db.execute(text(query_str)).mappings().first()
        if result: return {"message": "Login successful!", "user": result['username']}
        else: raise HTTPException(401, "Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(400, "Database Error (SQL Syntax)")
    finally:
        db.close()

@router.post("/submit-fix")
def submit_fix_sql(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success, logs = sandbox_runner.run_in_sandbox(submission.code, challenge_dir="challenge-sql-injection")
        if success: mark_challenge_complete(db, current_user.id, "sql-injection")
        return {"success": success, "logs": logs}
    except Exception as e: raise HTTPException(500, f"Sandbox Error: {str(e)}")

@router.post("/submit-fix-xss")
def submit_fix_xss(submission: CodeSubmission, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success, logs = sandbox_runner.run_in_sandbox(submission.code, challenge_dir="challenge-xss")
        if success: mark_challenge_complete(db, current_user.id, "xss")
        return {"success": success, "logs": logs}
    except Exception as e: raise HTTPException(500, f"Sandbox Error: {str(e)}")

@router.get("/xss/comments", response_model=List[CommentResponse])
def get_comments(db: Session = Depends(get_db)): return db.query(XSSComment).all()

@router.post("/xss/comments")
def post_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    new = XSSComment(author=comment.author, content=comment.content)
    db.add(new); db.commit(); db.refresh(new)
    return new

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