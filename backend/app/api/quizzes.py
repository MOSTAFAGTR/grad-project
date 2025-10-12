from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas # <--- CORRECTED: Removed ', crud' from this line
from ..db.database import get_db

router = APIRouter()

# A dummy database of questions for now
DUMMY_QUESTIONS = [
    {"id": 1, "text": "What does SQL stand for?", "type": "MCQ", "answer": "Structured Query Language", "explanation": "SQL is a standard language for accessing and manipulating databases."},
    {"id": 2, "text": "Which of the following is a common type of Cross-Site Scripting (XSS)?", "type": "MCQ", "answer": "Stored XSS", "explanation": "Stored XSS attacks involve an attacker injecting a script that is permanently stored on the target application."},
    {"id": 3, "text": "Is it safe to concatenate user input directly into a SQL query?", "type": "TF", "answer": "False", "explanation": "Directly concatenating user input can lead to SQL Injection vulnerabilities."},
]

@router.get("/questions", response_model=list[schemas.Question])
def get_quiz_questions(db: Session = Depends(get_db)):
    """
    This endpoint retrieves a list of quiz questions.
    In a real application, this would fetch questions from the database.
    """
    return DUMMY_QUESTIONS