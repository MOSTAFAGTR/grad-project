from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..db.database import get_db

router = APIRouter(
    prefix="/quizzes",
    tags=["quizzes"]
)

# مؤقتًا: قائمة أسئلة تجريبية (بدون قاعدة بيانات)
DUMMY_QUESTIONS = [
    {
        "id": 1,
        "text": "What does SQL stand for?",
        "type": "MCQ",
        "answer": "Structured Query Language",
        "explanation": "SQL is a standard language for accessing and manipulating databases."
    },
    {
        "id": 2,
        "text": "Which of the following is a common type of Cross-Site Scripting (XSS)?",
        "type": "MCQ",
        "answer": "Stored XSS",
        "explanation": "Stored XSS attacks involve an attacker injecting a script that is permanently stored on the target application."
    },
    {
        "id": 3,
        "text": "Is it safe to concatenate user input directly into a SQL query?",
        "type": "TF",
        "answer": "False",
        "explanation": "Directly concatenating user input can lead to SQL Injection vulnerabilities."
    },
]

@router.get("/questions", response_model=list[schemas.Question])
def get_quiz_questions(db: Session = Depends(get_db)):
    """
    Retrieves a list of quiz questions.
    Currently returns dummy questions for testing.
    In the future, this will fetch data from the database.
    """
    return DUMMY_QUESTIONS
