from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List 
from pydantic import BaseModel

from .. import schemas, crud, models
from ..db.database import get_db
import logging

SECRET_KEY = "scale_graduation_project_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError: raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None: raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_admin(user: models.User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

# --- AUTH ENDPOINTS ---
@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.role == 'admin':
        raise HTTPException(status_code=403, detail="Admin registration is restricted.")
    return crud.create_user(db=db, user=user, role=user.role)

@router.post("/login")
def login(user: schemas.LoginAttempt, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.username) 
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval.")

    token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer", "user_id": db_user.id, "role": db_user.role}

@router.get("/users", response_model=List[schemas.UserSearchResponse])
def search_users(query: str = "", db: Session = Depends(get_db)):
    if query: return db.query(models.User).filter(models.User.email.contains(query)).limit(20).all()
    return db.query(models.User).limit(50).all()

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