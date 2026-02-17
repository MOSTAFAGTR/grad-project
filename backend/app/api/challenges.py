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
def execute_vulnerable_login(attempt: LoginAttempt):
    db = SessionLocalChallenge()
    query_str = f'SELECT * FROM users WHERE username ="' + attempt.username + '" AND password ="' + attempt.password + '"'
    print(f"SQL Exec: {query_str}")
    try:
        result = db.execute(text(query_str)).mappings().first()
        if result: return {"message": "Login successful!", "user": dict(result)}
        else: raise HTTPException(401, "Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(400, "Database Error (SQL Syntax)")
    finally:
        db.close()

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