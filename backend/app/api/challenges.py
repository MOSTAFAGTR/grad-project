from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.database import get_db
from .. import sandbox_runner # Import the sandbox runner

router = APIRouter()

class LoginAttempt(BaseModel):
    username: str
    password: str

class CodeSubmission(BaseModel):
    code: str

# --- The "Attack" endpoint remains the same ---
@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt, db: Session = Depends(get_db)):
    query = f"SELECT * FROM challenge_users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    print(f"Executing vulnerable query: {query}")
    try:
        result = db.execute(text(query))
        user = result.first()
        if user:
            return {"message": "Login successful!"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(f"SQL Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

# --- NEW "FIX" ENDPOINT ---
@router.post("/submit-fix")
def submit_fix(submission: CodeSubmission):
    """
    Receives the user's fixed code and runs it in the sandbox.
    """
    try:
        success, logs = sandbox_runner.run_in_sandbox(submission.code)
        return {"success": success, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running sandbox: {e}")