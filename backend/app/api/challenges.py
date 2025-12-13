from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ..db.database import get_db
from .. import sandbox_runner 
from ..models import XSSComment

router = APIRouter()

# --- Schemas ---
class LoginAttempt(BaseModel):
    username: str
    password: str

class CodeSubmission(BaseModel):
    code: str
    challenge: Optional[str] = "sql-injection"

class MessageAttempt(BaseModel):
    message: str

class CommentCreate(BaseModel):
    author: str
    content: str

class CommentResponse(BaseModel):
    id: int
    author: str
    content: str
    class Config:
        orm_mode = True

# --- SQL Injection Endpoints ---

@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt, db: Session = Depends(get_db)):
    # Vulnerable to SQL Injection - DO NOT DO THIS IN PRODUCTION!
    query = f"SELECT * FROM challenge_users WHERE username = '{attempt.username}' OR password = '{attempt.password}'"
    result = db.execute(text(query)).fetchone()
    if result:
        return {"message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials") 

@router.post("/submit-fix")
def submit_fix_sql(submission: CodeSubmission):
    try:
        # Pass the specific folder for SQL Injection
        success, logs = sandbox_runner.run_in_sandbox(
            submission.code, 
            challenge_dir="challenge-sql-injection"
        )
        return {"success": success, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# --- XSS Endpoints ---

@router.get("/xss/comments", response_model=List[CommentResponse])
def get_comments(db: Session = Depends(get_db)):
    return db.query(XSSComment).all()

@router.post("/xss/comments")
def post_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    # Vulnerable storage: No sanitization happening here
    new_comment = XSSComment(author=comment.author, content=comment.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.delete("/xss/comments")
def clear_comments(db: Session = Depends(get_db)):
    db.query(XSSComment).delete()
    db.commit()
    return {"message": "Comments cleared"}

@router.post("/submit-fix-xss")
def submit_fix_xss(submission: CodeSubmission):
    try:
        # Pass the specific folder for XSS
        success, logs = sandbox_runner.run_in_sandbox(
            submission.code, 
            challenge_dir="challenge-xss"
        )
        return {"success": success, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")