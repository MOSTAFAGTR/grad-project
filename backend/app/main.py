from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
import time
import logging

# Import the routers directly
from .api import auth, quizzes, challenges
from .db import database
from . import models 

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTES (CRITICAL) ---
# This connects the files to the URL
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])

# --- DATABASE CONNECTION RETRY ---
@app.on_event("startup")
def startup_event():
    logger.info("Waiting for Database...")
    retries = 10
    while retries > 0:
        try:
            models.Base.metadata.create_all(bind=database.engine)
            logger.info("Database connected and tables created!")
            break
        except OperationalError as e:
            retries -= 1
            logger.warning(f"DB not ready. Retrying... ({retries} left)")
            time.sleep(3)
            if retries == 0:
                logger.error("Could not connect to database.")
                raise e

@app.get("/")
def read_root():
    return {"message": "Welcome to the SCALE API"}