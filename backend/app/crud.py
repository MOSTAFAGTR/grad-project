from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, role: str = 'user', is_admin_created: bool = False):
    hashed_password = pwd_context.hash(user.password)
    
    # Approval Logic
    is_approved = True
    if role == 'instructor' and not is_admin_created:
        is_approved = False
        
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password, 
        role=role,
        is_approved=is_approved
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def approve_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_approved = True
        db.commit()
        db.refresh(user)
    return user

# --- NEW FUNCTIONS FOR ADMIN ACTIONS ---
def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def update_user_role(db: Session, user_id: int, new_role: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
    return user