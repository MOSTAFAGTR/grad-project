from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..db.database import get_db
import logging

# ✅ Configure logging (مرة واحدة في الملف)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ إنشاء Router
router = APIRouter(prefix="/auth", tags=["Auth"])

# ===============================
# 🔹 Register User Endpoint
# ===============================
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with email: {user.email}")

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"Registration failed: Email '{user.email}' already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        logger.info("Creating new user...")
        new_user = crud.create_user(db=db, user=user)
        logger.info(f"User created successfully: {user.email}")
        return new_user
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# ===============================
# 🔹 Login User Endpoint
# ===============================
@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user by email and password."""
    logger.info(f"Login attempt for email: {user.email}")

    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        logger.warning(f"Login failed:
