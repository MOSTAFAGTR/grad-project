from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Define a schema to receive the username and password
class LoginAttempt(BaseModel):
    username: str
    password: str

@router.post("/sqli-attack")
def simulate_sqli_login(attempt: LoginAttempt):
    """
    This endpoint simulates a login form vulnerable to SQL injection.
    It does NOT connect to a real database for this check.
    It only checks if a classic injection payload is present.
    """
    # The classic SQL injection payload to bypass authentication
    injection_payload = "' OR '1'='1'"

    # In a real vulnerable app, this would be a raw SQL query like:
    # "SELECT * FROM users WHERE username = '" + attempt.username + "' AND password = '" + attempt.password + "'"
    
    # We are safely SIMULATING the result of that query
    if injection_payload in attempt.username or injection_payload in attempt.password:
        # If the payload is found, the "attack" is successful
        return {"message": "Login successful!"}
    else:
        # If it's a normal login attempt, it fails
        raise HTTPException(status_code=401, detail="Invalid credentials")