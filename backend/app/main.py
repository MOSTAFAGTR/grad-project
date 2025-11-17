from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, quizzes, challenges
from .db import database
from . import models
import time
from sqlalchemy.exc import OperationalError


# Delay creating tables until the database is reachable. When running in Docker
# the database may take a few seconds to start; importing models and calling
# create_all at import time causes the app to crash if the DB isn't ready.
def ensure_db_ready(retries: int = 10, delay: float = 1.0):
    last_exc = None
    for i in range(retries):
        try:
            models.Base.metadata.create_all(bind=database.engine)
            return
        except OperationalError as e:
            last_exc = e
            time.sleep(delay)
    # If we reach here, re-raise the last exception so the startup fails visibly
    if last_exc:
        raise last_exc


# Try to create tables on startup (will retry until DB is up)
ensure_db_ready()
# --------------------------------

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the SCALE API"}