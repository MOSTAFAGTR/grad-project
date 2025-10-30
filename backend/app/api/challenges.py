from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)

class LoginAttempt(BaseModel):
    username: str
    password: str

# مجموعة بسيطة من أنماط payloads شائعة (ممكن توسعها لأغراض تعليمية)
SQLI_PATTERNS = [
    r"(?i)'\s*or\s*'1'\s*=\s*'1",       # ' OR '1'='1
    r"(?i)\"\s*or\s*\"1\"\s*=\s*\"1",   # " OR "1"="1
    r"(?i)or\s+1\s*=\s*1",              # OR 1=1
    r"(?i)--",                          # SQL comment
    r"(?i);\s*drop\s+table",            # ; DROP TABLE
    r"(?i)union\s+select",              # UNION SELECT
]

def contains_sqli(payload: str) -> bool:
    if not payload:
        return False
    for pattern in SQLI_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

@router.post("/sqli-attack")
def simulate_sqli_login(attempt: LoginAttempt):
    """
    Educational endpoint: simulates detection of classic SQL-injection payloads.
    DOES NOT execute any SQL or connect to a database.
    Returns an explanatory response so learners can see why payloads are dangerous.
    """
    # Check both fields for suspicious patterns
    username_flag = contains_sqli(attempt.username)
    password_flag = contains_sqli(attempt.password)

    if username_flag or password_flag:
        # Log the detection (avoid logging sensitive data in production)
        logger.warning("Detected possible SQL injection payload in login attempt.")
        return {
            "vulnerable": True,
            "message": "Simulated login would succeed on a vulnerable system because an injection payload was detected.",
            "detected_in": {
                "username": username_flag,
                "password": password_flag
            },
            "note": (
                "This is only a simulation. To prevent SQL injection: use parameterized queries / prepared statements, "
                "validate and escape input, and avoid building SQL with string concatenation."
            )
        }
    else:
        # Normal failed login simulation
        raise HTTPException(status_code=401, detail="Invalid credentials (simulated).")

# --- Secure demo endpoint (educational) ---
@router.post("/secure-login-demo")
def secure_login_demo(attempt: LoginAttempt):
    """
    Educational demo showing how to check credentials safely (simulated).
    DOES NOT connect to a real DB — it shows the pattern you should use.
    """
    # Example: how a parameterized query would conceptually look
    # (Pseudo-code; do NOT substitute with string concatenation)
    #
    # cursor.execute("SELECT id, hashed_password FROM users WHERE username = %s", (attempt.username,))
    #
    # Then verify the password using a secure hashing function (bcrypt, argon2, etc.)
    #
    # We'll simulate a safe check result here:
    simulated_user = {
        "username": "alice",
        "hashed_password": "$2b$12$examplehash..."  # example only
    }

    # Simulate lookup (safe): only considers exact match, no string concatenation
    if attempt.username == simulated_user["username"]:
        # Here you'd call your password verification function (bcrypt.checkpw / etc.)
        # We'll simulate a failed verification to avoid revealing anything
        password_ok = False
        if password_ok:
            return {"message": "Secure login success (simulated)."}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials (secure flow).")
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials (secure flow).")
