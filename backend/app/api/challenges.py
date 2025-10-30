from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.database import get_db

router = APIRouter()

class LoginAttempt(BaseModel):
    username: str
    password: str

@router.post("/vulnerable-login")
def execute_vulnerable_login(attempt: LoginAttempt, db: Session = Depends(get_db)):
    """
    This endpoint is vulnerable to SQL injection.
    It allows for a valid username and an injection payload in the password field.
    """
    
    # DANGER: Raw query construction.
    # This is the classic vulnerable pattern you asked for.
    query = f"SELECT * FROM challenge_users WHERE username = '{attempt.username}' AND password = '{attempt.password}'"
    
    print(f"Executing vulnerable query: {query}")

    try:
        result = db.execute(text(query))
        user = result.first()
        
        if user:
            # If the database returns ANY row, the login is a success.
            return {"message": "Login successful!"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    except Exception as e:
        # If the database throws a syntax error (from a bad injection),
        # return a generic failure message.
        print(f"SQL Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")