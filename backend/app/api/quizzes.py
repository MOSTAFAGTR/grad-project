from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import requests
import random

from ..db.database import get_db
from ..models import Question, QuestionOption, UserAnswer, User, QuizAssignment
from ..schemas import QuestionCreate, QuestionResponse, QuestionUpdate, QuizRequest, AnswerSubmit, AnswerResponse, AIGenerationRequest, AssignmentCreate, AssignmentResponse
from .auth import get_current_user

router = APIRouter()
AI_SERVICE_URL = "http://ai_service:8001/generate"

@router.get("/topics", response_model=List[str])
def get_topics(db: Session = Depends(get_db)):
    topics = db.query(Question.topic).distinct().all()
    return [t[0] for t in topics]

@router.post("/questions", response_model=QuestionResponse)
def create_question(q: QuestionCreate, db: Session = Depends(get_db)):
    new_q = Question(text=q.text, type=q.type, topic=q.topic, difficulty=q.difficulty, skill_focus=q.skill_focus, explanation=q.explanation)
    db.add(new_q); db.commit(); db.refresh(new_q)
    for opt in q.options: db.add(QuestionOption(question_id=new_q.id, text=opt.text, is_correct=opt.is_correct))
    db.commit()
    return new_q

@router.get("/questions", response_model=List[QuestionResponse])
def get_questions(topic: str = Query(None), difficulty: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(Question)
    if topic: q = q.filter(Question.topic == topic)
    if difficulty: q = q.filter(Question.difficulty == difficulty)
    return q.all()

@router.put("/questions/{q_id}")
def update_question(q_id: int, u: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q: raise HTTPException(404, "Not found")
    if u.text: q.text = u.text
    if u.topic: q.topic = u.topic
    if u.difficulty: q.difficulty = u.difficulty
    if u.explanation: q.explanation = u.explanation
    db.commit()
    return {"message": "Updated"}

@router.delete("/questions/{q_id}")
def delete_question(q_id: int, db: Session = Depends(get_db)):
    db.query(Question).filter(Question.id == q_id).delete(); db.commit()
    return {"message": "Deleted"}

@router.post("/generate-ai-preview")
def generate_ai(req: AIGenerationRequest, user: User = Depends(get_current_user)):
    try:
        res = requests.post(AI_SERVICE_URL, json=req.dict())
        if res.status_code == 200: return res.json()
        raise HTTPException(500, "AI Service Error")
    except Exception as e: raise HTTPException(500, f"AI Error: {str(e)}")

@router.post("/assignments", response_model=AssignmentResponse)
def create_assign(d: AssignmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    assign = QuizAssignment(title=d.title, instructor_id=user.id, question_ids=",".join(map(str, d.question_ids)), assigned_student_ids=",".join(map(str, d.student_ids)))
    db.add(assign); db.commit(); db.refresh(assign)
    return assign

@router.get("/assignments/instructor", response_model=List[AssignmentResponse])
def get_instr_assigns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(QuizAssignment).filter(QuizAssignment.instructor_id == user.id).all()

@router.delete("/assignments/{id}")
def delete_assign(id: int, db: Session = Depends(get_db)):
    db.query(QuizAssignment).filter(QuizAssignment.id == id).delete(); db.commit()
    return {"message": "Deleted"}

@router.get("/assignments/student", response_model=List[AssignmentResponse])
def get_student_assigns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    all = db.query(QuizAssignment).all()
    return [a for a in all if str(user.id) in a.assigned_student_ids.split(',')]

@router.get("/assignments/{id}/take", response_model=List[QuestionResponse])
def take_assign_quiz(id: int, db: Session = Depends(get_db)):
    a = db.query(QuizAssignment).filter(QuizAssignment.id == id).first()
    if not a: raise HTTPException(404, "Not found")
    ids = [int(i) for i in a.question_ids.split(',') if i]
    return db.query(Question).filter(Question.id.in_(ids)).all()

@router.post("/take", response_model=List[QuestionResponse])
def take_quiz(req: QuizRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.topic.in_(req.topics))
    if req.difficulty: q = q.filter(Question.difficulty == req.difficulty)
    questions = q.limit(100).all()
    count = min(req.count, len(questions))
    return random.sample(questions, count) if count > 0 else []

@router.post("/submit-answer", response_model=AnswerResponse)
def submit_answer(sub: AnswerSubmit, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    opt = db.query(QuestionOption).filter(QuestionOption.id == sub.selected_option_id).first()
    if not opt: raise HTTPException(404, "Option not found")
    q = db.query(Question).filter(Question.id == sub.question_id).first()
    db.add(UserAnswer(user_id=user.id, question_id=sub.question_id, selected_option_id=sub.selected_option_id, is_correct=opt.is_correct))
    db.commit()
    return {"correct": opt.is_correct, "explanation": q.explanation}