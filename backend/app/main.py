from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, quizzes, challenges # <--- 1. Import the new challenges router
from .db import database
from . import models

models.Base.metadata.create_all(bind=database.engine)

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
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"]) # <--- 2. Add the new router

@app.get("/")
def read_root():
    return {"message": "Welcome to the SCALE API"}