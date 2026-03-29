from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import os
import sqlite3

from .. import schemas, crud, models
from ..db.database import get_db
from ..security.security_logger import (
    SecurityEventType,
    SecuritySeverity,
    is_repeated_failed_login,
    log_security_event,
)
import logging

SECRET_KEY = os.getenv("SECRET_KEY", "scale_graduation_project_secret_key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "600"))
ENABLE_BROKEN_AUTH_CHALLENGE = os.getenv("ENABLE_BROKEN_AUTH_CHALLENGE", "true").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "access_token")
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "lax")
AUTH_COOKIE_MAX_AGE = int(os.getenv("AUTH_COOKIE_MAX_AGE", str(ACCESS_TOKEN_EXPIRE_MINUTES * 60)))

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _try_decode_user(db: Session, raw_token: Optional[str]) -> Optional[models.User]:
    token = (raw_token or "").strip()
    if not token or token in {"null", "undefined", "cookie-auth"}:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None
    return db.query(models.User).filter(models.User.email == email).first()


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # Try Authorization header token first, then fall back to HttpOnly cookie.
    user = _try_decode_user(db, token)
    if user:
        return user

    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    user = _try_decode_user(db, cookie_token)
    if user:
        return user

    raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(user: models.User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user


def require_role(*allowed_roles: str):
    """
    Reusable RBAC dependency.
    Accepted aliases:
      - "student" -> "user"
    """
    normalized = {("user" if role == "student" else role) for role in allowed_roles}

    async def _role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in normalized:
            raise HTTPException(status_code=403, detail="Not authorized for this operation")
        return current_user

    return _role_dependency

# --- AUTH ENDPOINTS ---
@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.role == 'admin':
        raise HTTPException(status_code=403, detail="Admin registration is restricted.")
    return crud.create_user(db=db, user=user, role=user.role)

@router.post("/login")
def login(
    user: schemas.LoginAttempt,
    response: Response,
    db: Session = Depends(get_db),
    request: Request = None,
    # Optional challenge flag: when set to "broken-auth" we simulate a vulnerable login
    challenge: Optional[str] = None,
):
    db_user = crud.get_user_by_email(db, email=user.username)
    challenge_name = (challenge or "").strip().lower()
    is_challenge_login = bool(challenge_name)

    # --- Broken-auth challenge mode: intentionally vulnerable branch ---
    # This preserves normal authentication while allowing a special mode
    # for the Broken Authentication mini-game.
    if challenge_name == "broken-auth" and ENABLE_BROKEN_AUTH_CHALLENGE:
        users = [
            {"id": 1, "email": "admin@scale.edu", "password": "secret123", "role": "admin"},
            {"id": 2, "email": "user@scale.edu", "password": "user123", "role": "user"},
        ]
        vulnerable_query = f"SELECT * FROM users WHERE email = '{user.username}' AND password = '{user.password}'"

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password TEXT, role TEXT)"
        )
        for row in users:
            conn.execute(
                "INSERT INTO users (id, email, password, role) VALUES (?,?,?,?)",
                (row["id"], row["email"], row["password"], row["role"]),
            )
        conn.commit()

        returned_row = None
        try:
            cur = conn.execute(vulnerable_query)
            rows = cur.fetchall()
            for r in rows:
                if r["role"] == "admin":
                    returned_row = r
                    break
            if returned_row is None and rows:
                returned_row = rows[0]
        except sqlite3.DatabaseError:
            returned_row = None
        conn.close()

        returned_user = None
        bypass_success = False
        is_injected = False
        explanation = "No row matched the executed query."

        if returned_row:
            returned_user = {
                "id": returned_row["id"],
                "email": returned_row["email"],
                "password": returned_row["password"],
                "role": returned_row["role"],
            }
            password_matches_stored = user.password == returned_user["password"]
            is_injected = not password_matches_stored
            bypass_success = returned_user["role"] == "admin" and not password_matches_stored
            if bypass_success:
                explanation = (
                    "The vulnerable query returned the admin account without the correct password "
                    "(SQL logic was satisfied by the supplied input)."
                )
            elif password_matches_stored and returned_user["role"] == "admin":
                explanation = "Valid admin credentials were supplied."
            else:
                explanation = "A row matched the executed query."

        log_security_event(
            db=db,
            event_type=SecurityEventType.CHALLENGE_SQLI,
            severity=SecuritySeverity.HIGH if bypass_success else SecuritySeverity.MEDIUM,
            payload={"username": user.username, "password": user.password, "challenge": challenge_name},
            request=request,
            metadata={
                "challenge": challenge_name,
                "query": vulnerable_query,
                "is_injected": is_injected,
                "bypass_success": bypass_success,
                "returned_user": returned_user["email"] if returned_user else None,
            },
            context_type="challenge",
        )

        if returned_user:
            platform_user = crud.get_user_by_email(db, email=returned_user["email"])
            role = returned_user["role"]
            token_email = platform_user.email if platform_user else returned_user["email"]
            token = create_access_token(data={"sub": token_email, "role": role})
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": platform_user.id if platform_user else returned_user["id"],
                "role": role,
                "email": token_email,
                "executed_query": vulnerable_query,
                "returned_user": returned_user["email"],
                "is_admin": role == "admin",
                "is_injected": is_injected,
                "bypass_success": bypass_success,
                "explanation": explanation,
                "broken_auth": True,
            }

        raise HTTPException(
            status_code=401,
            detail={
                "executed_query": vulnerable_query,
                "returned_user": None,
                "is_admin": False,
                "is_injected": is_injected,
                "bypass_success": bypass_success,
                "explanation": explanation,
            },
        )

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        repeated = False
        if not is_challenge_login:
            repeated = is_repeated_failed_login(
                db=db,
                user_id=db_user.id if db_user else None,
                ip_address=request.client.host if request and request.client else None,
            )
        log_security_event(
            db=db,
            event_type=SecurityEventType.CHALLENGE_AUTH if is_challenge_login else SecurityEventType.LOGIN_FAILED,
            severity=SecuritySeverity.CRITICAL if repeated else SecuritySeverity.MEDIUM,
            payload={"username": user.username, "challenge": challenge_name},
            request=request,
            user_id=db_user.id if db_user else None,
            metadata={"reason": "invalid_credentials", "repeated_failed_login": repeated, "challenge": challenge_name},
            context_type="challenge" if is_challenge_login else "real",
        )
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval.")

    token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )
    log_security_event(
        db=db,
        event_type=SecurityEventType.CHALLENGE_AUTH if is_challenge_login else SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.LOW,
        payload={"username": user.username, "challenge": challenge_name},
        request=request,
        user_id=db_user.id,
        metadata={"role": db_user.role, "challenge": challenge_name},
        context_type="challenge" if is_challenge_login else "real",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role,
        "email": db_user.email,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return {"ok": True}

@router.get("/users", response_model=List[schemas.UserSearchResponse])
def search_users(
    query: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "instructor")),
):
    if query: return db.query(models.User).filter(models.User.email.contains(query)).limit(20).all()
    return db.query(models.User).limit(50).all()


@router.get("/me", response_model=schemas.UserSearchResponse)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- ADMIN ENDPOINTS ---
@router.get("/admin/pending", response_model=List[schemas.UserSearchResponse])
def get_pending_instructors(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    return db.query(models.User).filter(models.User.role == 'instructor', models.User.is_approved == False).all()

@router.post("/admin/approve/{user_id}")
def approve_instructor(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    return crud.approve_user(db, user_id)

@router.post("/admin/create-admin", response_model=schemas.User)
def create_admin_internal(user: schemas.UserCreateAdmin, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_in = schemas.UserCreate(email=user.email, password=user.password, role='admin')
    return crud.create_user(db=db, user=user_in, role='admin', is_admin_created=True)

# NEW: DELETE USER (BAN)
@router.delete("/admin/users/{user_id}")
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    success = crud.delete_user(db, user_id)
    if not success: raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# NEW: UPDATE USER ROLE
class RoleUpdate(BaseModel):
    role: str

@router.put("/admin/users/{user_id}/role")
def update_role_endpoint(user_id: int, update: RoleUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    return crud.update_user_role(db, user_id, update.role)