from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..db.database import get_db
import logging # Import the logging library

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with email: {user.email}")
    try:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            logger.warning(f"Registration failed: Email '{user.email}' already registered.")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        logger.info("Email not found, creating new user.")
        new_user = crud.create_user(db=db, user=user)
        logger.info(f"Successfully created user with email: {user.email}")
        return new_user
    except Exception as e:
        logger.error(f"An unexpected error occurred during registration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during user creation.")

@router.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # This function remains unchanged for now
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not crud.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"message": "Login successful"}