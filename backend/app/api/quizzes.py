from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
import json
import re
import requests
import random
import os
import httpx

from ..db.database import get_db
from ..models import (
    Question,
    QuestionOption,
    UserAnswer,
    User,
    QuizAssignment,
    QuizAttempt,
    QuizAssignmentStudent,
    QuizAssignmentQuestion,
)
from ..schemas import (
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    QuizRequest,
    AnswerSubmit,
    AnswerResponse,
    AIGenerationRequest,
    AssignmentCreate,
    AssignmentResponse,
    QuizAttemptSubmit,
    QuizAttemptResponse,
    AIQuizAssignRequest,
    AIQuizAssignResponse,
    MistakesQuizAssignRequest,
    QuizAssignmentStartResponse,
)
from .auth import get_current_user, require_role
from ..ai.serper_helpers import build_quiz_questions_from_serper, serper_configured

router = APIRouter()


def _parse_due_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace("Z", "")
    try:
        if "T" not in s and len(s) <= 10:
            return datetime.fromisoformat(s + "T23:59:59")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _validate_time_limit(minutes: Optional[int]) -> Optional[int]:
    if minutes is None:
        return None
    m = int(minutes)
    if m < 5 or m > 240:
        raise HTTPException(status_code=400, detail="time_limit_minutes must be between 5 and 240.")
    return m


def _get_student_assignment_row(
    db: Session, assignment_id: int, user_id: int
) -> Optional[QuizAssignmentStudent]:
    return (
        db.query(QuizAssignmentStudent)
        .filter(
            QuizAssignmentStudent.assignment_id == assignment_id,
            QuizAssignmentStudent.student_id == user_id,
        )
        .first()
    )


def _ensure_student_assigned(db: Session, assign: QuizAssignment, user: User) -> QuizAssignmentStudent:
    mapped = _get_student_assignment_row(db, assign.id, user.id)
    if mapped:
        return mapped
    if user.role != "user":
        raise HTTPException(status_code=403, detail="Assignment is not assigned to this user")
    assigned = {int(i) for i in (assign.assigned_student_ids or "").split(",") if i}
    if user.id not in assigned:
        raise HTTPException(status_code=403, detail="Assignment is not assigned to this user")
    mapped = QuizAssignmentStudent(assignment_id=assign.id, student_id=user.id, status="assigned")
    db.add(mapped)
    db.flush()
    return mapped


def _student_assignment_payload(
    db: Session, assign: QuizAssignment, cas: Optional[QuizAssignmentStudent], user_id: int
) -> dict:
    now = datetime.utcnow()
    if not cas:
        cas = _get_student_assignment_row(db, assign.id, user_id)
    status = (cas.status if cas else None) or "assigned"
    due = assign.due_date
    is_past_due = bool(due and now > due)
    time_remaining: Optional[int] = None
    if cas and status == "in_progress" and cas.started_at and assign.time_limit_minutes:
        limit_sec = int(assign.time_limit_minutes) * 60
        used = int((now - cas.started_at).total_seconds())
        time_remaining = max(0, limit_sec - used)
    return {
        "id": assign.id,
        "title": assign.title,
        "instructor_id": assign.instructor_id,
        "created_at": assign.created_at,
        "time_limit_minutes": assign.time_limit_minutes,
        "due_date": assign.due_date,
        "status": status,
        "is_past_due": is_past_due,
        "time_remaining_seconds": time_remaining,
    }


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY", "") or "").strip()
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai_service:8001")


class QuizManageRequest(BaseModel):
    action: str
    id: Optional[int] = None
    question: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[int] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None

@router.get("/topics", response_model=List[str])
def get_topics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    topics = db.query(Question.topic).distinct().all()
    return [t[0] for t in topics]

@router.post("/questions", response_model=QuestionResponse)
def create_question(
    q: QuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    new_q = Question(text=q.text, type=q.type, topic=q.topic, difficulty=q.difficulty, skill_focus=q.skill_focus, explanation=q.explanation)
    db.add(new_q); db.commit(); db.refresh(new_q)
    for opt in q.options: db.add(QuestionOption(question_id=new_q.id, text=opt.text, is_correct=opt.is_correct))
    db.commit()
    return new_q

@router.get("/questions", response_model=List[QuestionResponse])
def get_questions(
    topic: str = Query(None),
    difficulty: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    q = db.query(Question)
    if topic: q = q.filter(Question.topic == topic)
    if difficulty: q = q.filter(Question.difficulty == difficulty)
    return q.all()

@router.put("/questions/{q_id}")
def update_question(
    q_id: int,
    u: QuestionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q: raise HTTPException(404, "Not found")
    if u.text: q.text = u.text
    if u.topic: q.topic = u.topic
    if u.difficulty: q.difficulty = u.difficulty
    if u.explanation: q.explanation = u.explanation
    db.commit()
    return {"message": "Updated"}

@router.delete("/questions")
def delete_all_questions(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    db.query(UserAnswer).delete()
    db.query(QuestionOption).delete()
    db.query(Question).delete()
    db.commit()
    return {"message": "All questions deleted"}

@router.delete("/questions/{q_id}")
def delete_question(
    q_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    db.query(UserAnswer).filter(UserAnswer.question_id == q_id).delete()
    db.query(Question).filter(Question.id == q_id).delete()
    db.commit()
    return {"message": "Deleted"}



def _quiz_dicts_to_ai_preview(
    questions: list[dict],
    topic: str,
    difficulty: str,
    skill_focus: str,
) -> list[dict]:
    """Shape Serper/OpenAI quiz dicts like the template ai_service /generate response."""
    out: list[dict] = []
    sf = (skill_focus or "General")[:50]
    for q in questions:
        opts = q.get("options") or []
        try:
            ci = int(q.get("correct_index", 0))
        except (TypeError, ValueError):
            ci = 0
        if len(opts) != 4 or ci not in (0, 1, 2, 3):
            continue
        out.append(
            {
                "text": (q.get("question") or "")[:8000],
                "type": "MCQ",
                "topic": (topic or "General")[:80],
                "difficulty": difficulty or "Medium",
                "skill_focus": sf,
                "explanation": (q.get("explanation") or "").strip()[:2000],
                "options": [{"text": str(o)[:255], "is_correct": (i == ci)} for i, o in enumerate(opts)],
            }
        )
    return out


@router.post("/generate-ai-preview")
def generate_ai(
    req: AIGenerationRequest,
    user: User = Depends(require_role("admin", "instructor")),
):
    """
    Prefer the lightweight template ai_service. If it is down or returns nothing,
    fall back to the same OpenAI / Serper generator used for ai-generate-and-assign.
    """
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    url = f"{AI_SERVICE_URL.rstrip('/')}/generate"
    try:
        res = requests.post(url, json=payload, timeout=45)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return data
    except Exception:
        pass

    topic = (req.topic or "").strip() or "cybersecurity"
    n = max(1, min(int(req.count or 3), 10))
    skill = (req.skill_focus or "General").strip() or "General"
    generated = _generate_questions_with_ai(topic, req.difficulty or "Medium", n)
    preview = _quiz_dicts_to_ai_preview(generated, topic, req.difficulty or "Medium", skill)
    if not preview:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not generate preview. Ensure SERPER_API_KEY or OPENAI_API_KEY is set, "
                "or that the ai_service container is healthy."
            ),
        )
    return preview

@router.post("/assignments", response_model=AssignmentResponse)
def create_assign(
    d: AssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    time_limit = _validate_time_limit(d.time_limit_minutes)
    due = _parse_due_date(d.due_date)
    assign = QuizAssignment(
        title=d.title,
        instructor_id=user.id,
        # Keep legacy denormalized columns for backward compatibility.
        question_ids=",".join(map(str, d.question_ids)),
        assigned_student_ids=",".join(map(str, d.student_ids)),
        time_limit_minutes=time_limit,
        due_date=due,
    )
    db.add(assign)
    db.flush()
    for sid in d.student_ids:
        db.add(QuizAssignmentStudent(assignment_id=assign.id, student_id=sid))
    for qid in d.question_ids:
        db.add(QuizAssignmentQuestion(assignment_id=assign.id, question_id=qid))
    db.commit()
    db.refresh(assign)
    return assign

@router.get("/assignments/instructor", response_model=List[AssignmentResponse])
def get_instr_assigns(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    return db.query(QuizAssignment).filter(QuizAssignment.instructor_id == user.id).all()

@router.delete("/assignments/{id}")
def delete_assign(
    id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    a = db.query(QuizAssignment).filter(QuizAssignment.id == id).first()
    if not a:
        raise HTTPException(404, "Not found")
    if user.role != "admin" and a.instructor_id != user.id:
        raise HTTPException(403, "Not authorized to delete this assignment")
    db.query(QuizAttempt).filter(QuizAttempt.assignment_id == id).delete()
    db.query(QuizAssignmentStudent).filter(QuizAssignmentStudent.assignment_id == id).delete()
    db.query(QuizAssignmentQuestion).filter(QuizAssignmentQuestion.assignment_id == id).delete()
    db.query(QuizAssignment).filter(QuizAssignment.id == id).delete()
    db.commit()
    return {"message": "Deleted"}

@router.get("/assignments/student", response_model=List[AssignmentResponse])
def get_student_assigns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mapped_rows = (
        db.query(QuizAssignmentStudent)
        .filter(QuizAssignmentStudent.student_id == user.id)
        .all()
    )
    mapped_assignment_ids = [row.assignment_id for row in mapped_rows]
    cas_by_aid = {row.assignment_id: row for row in mapped_rows}

    if mapped_assignment_ids:
        assigns = db.query(QuizAssignment).filter(QuizAssignment.id.in_(mapped_assignment_ids)).all()
    else:
        # Backward-compatible fallback for legacy comma-separated assignments.
        all_assignments = db.query(QuizAssignment).all()
        assigns = [a for a in all_assignments if str(user.id) in (a.assigned_student_ids or "").split(",")]

    return [_student_assignment_payload(db, a, cas_by_aid.get(a.id), user.id) for a in assigns]


@router.post("/assignments/{assignment_id}/start", response_model=QuizAssignmentStartResponse)
def start_quiz_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    assign = db.query(QuizAssignment).filter(QuizAssignment.id == assignment_id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")

    cas = _ensure_student_assigned(db, assign, user)

    if assign.due_date and now > assign.due_date:
        raise HTTPException(status_code=403, detail="Assignment has expired.")

    if cas.status == "completed":
        raise HTTPException(status_code=400, detail="Assignment already submitted.")

    if cas.status == "in_progress":
        limit_sec = (int(assign.time_limit_minutes) * 60) if assign.time_limit_minutes else None
        if limit_sec and cas.started_at:
            used = int((now - cas.started_at).total_seconds())
            if used >= limit_sec:
                cas.status = "expired"
                db.commit()
                raise HTTPException(status_code=403, detail="Time limit exceeded.")
        return QuizAssignmentStartResponse(
            assignment_id=assign.id,
            title=assign.title,
            time_limit_minutes=assign.time_limit_minutes,
            time_limit_seconds=limit_sec,
            due_date=assign.due_date.isoformat() if assign.due_date else None,
            started_at=cas.started_at.isoformat() if cas.started_at else now.isoformat(),
            status=cas.status,
        )

    cas.started_at = now
    cas.status = "in_progress"
    db.commit()
    db.refresh(cas)

    limit_sec = (int(assign.time_limit_minutes) * 60) if assign.time_limit_minutes else None
    return QuizAssignmentStartResponse(
        assignment_id=assign.id,
        title=assign.title,
        time_limit_minutes=assign.time_limit_minutes,
        time_limit_seconds=limit_sec,
        due_date=assign.due_date.isoformat() if assign.due_date else None,
        started_at=cas.started_at.isoformat(),
        status=cas.status,
    )


@router.get("/assignments/{assignment_id}/status")
def quiz_assignment_status(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assign = db.query(QuizAssignment).filter(QuizAssignment.id == assignment_id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    cas = _ensure_student_assigned(db, assign, user)
    now = datetime.utcnow()
    payload = _student_assignment_payload(db, assign, cas, user.id)
    limit_sec = (int(assign.time_limit_minutes) * 60) if assign.time_limit_minutes else None
    is_expired = False
    if cas.status == "in_progress" and limit_sec and cas.started_at:
        used = int((now - cas.started_at).total_seconds())
        if used >= limit_sec:
            is_expired = True
            payload["time_remaining_seconds"] = 0
    payload["is_expired"] = is_expired
    payload["time_limit_seconds"] = limit_sec
    if assign.due_date:
        payload["due_date"] = assign.due_date.isoformat()
    return payload


@router.get("/assignments/{id}/take", response_model=List[QuestionResponse])
def take_assign_quiz(
    id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    a = db.query(QuizAssignment).filter(QuizAssignment.id == id).first()
    if not a:
        raise HTTPException(404, "Not found")
    now = datetime.utcnow()
    if user.role == "user":
        cas = _ensure_student_assigned(db, a, user)
        if a.due_date and now > a.due_date:
            raise HTTPException(status_code=403, detail="Assignment has expired.")
        if cas.status not in ("in_progress",):
            raise HTTPException(
                status_code=400,
                detail="Start the assignment first via POST /api/quizzes/assignments/{id}/start",
            )
        if a.time_limit_minutes and cas.started_at:
            limit_sec = int(a.time_limit_minutes) * 60
            used = int((now - cas.started_at).total_seconds())
            if used >= limit_sec:
                cas.status = "expired"
                db.commit()
                raise HTTPException(status_code=403, detail="Time limit exceeded.")

    mapped_questions = (
        db.query(QuizAssignmentQuestion.question_id)
        .filter(QuizAssignmentQuestion.assignment_id == a.id)
        .all()
    )
    ids = [int(row[0]) for row in mapped_questions] if mapped_questions else [int(i) for i in (a.question_ids or "").split(',') if i]
    return db.query(Question).filter(Question.id.in_(ids)).all()

@router.post("/take", response_model=List[QuestionResponse])
def take_quiz(
    req: QuizRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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


@router.post("/submit-attempt", response_model=QuizAttemptResponse)
def submit_quiz_attempt(d: QuizAttemptSubmit, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Record a completed quiz attempt with score and time."""
    now = datetime.utcnow()
    if d.assignment_id:
        assign = db.query(QuizAssignment).filter(QuizAssignment.id == d.assignment_id).first()
        if not assign:
            raise HTTPException(status_code=404, detail="Assignment not found")
        cas = _ensure_student_assigned(db, assign, user)
        if assign.due_date and now > assign.due_date:
            raise HTTPException(status_code=403, detail="Assignment has expired.")
        if cas.status == "completed":
            raise HTTPException(status_code=400, detail="Assignment already submitted.")
        if assign.time_limit_minutes and cas.started_at:
            limit_sec = int(assign.time_limit_minutes) * 60
            if int((now - cas.started_at).total_seconds()) > limit_sec + 30:
                raise HTTPException(status_code=403, detail="Time limit exceeded.")
        cas.status = "completed"
        cas.submitted_at = now
        db.flush()

    att = QuizAttempt(
        user_id=user.id,
        assignment_id=d.assignment_id,
        title=d.title,
        score=d.score,
        total=d.total,
        time_seconds=d.time_seconds,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@router.get("/attempts", response_model=List[QuizAttemptResponse])
def get_my_quiz_attempts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get current user's quiz attempts, newest first."""
    return db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id).order_by(QuizAttempt.completed_at.desc()).all()


@router.get("/manage")
def quiz_manage_entry(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    rows = db.query(Question).all()
    data = []
    for q in rows:
        opts = [o.text for o in q.options]
        correct_idx = next((idx for idx, o in enumerate(q.options) if o.is_correct), 0)
        data.append(
            {
                "id": q.id,
                "question": q.text,
                "options": opts,
                "correct_answer": correct_idx,
                "explanation": q.explanation or "",
                "difficulty": q.difficulty or "Easy",
                "category": q.topic or "General",
            }
        )
    return {"ok": True, "questions": data, "role": current_user.role}


@router.post("/manage")
def quiz_manage_mutation(
    req: QuizManageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    action = (req.action or "").strip().lower()
    if action == "list":
        return quiz_manage_entry(db=db, current_user=current_user)

    if action == "delete":
        if not req.id:
            raise HTTPException(status_code=400, detail="Question id is required for delete")
        row = db.query(Question).filter(Question.id == req.id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        db.delete(row)
        db.commit()
        return {"ok": True}

    if action in {"create", "update"}:
        if not req.question or len((req.options or [])) != 4:
            raise HTTPException(status_code=400, detail="Question and exactly 4 options are required")
        if req.correct_answer is None or req.correct_answer < 0 or req.correct_answer > 3:
            raise HTTPException(status_code=400, detail="correct_answer must be an index 0-3")
        if not (req.explanation or "").strip():
            raise HTTPException(status_code=400, detail="Explanation is required")

        difficulty = (req.difficulty or "Easy").strip()
        category = (req.category or "General").strip()

        if action == "create":
            row = Question(
                text=req.question.strip(),
                type="MCQ",
                topic=category,
                difficulty=difficulty,
                skill_focus="Concepts",
                explanation=req.explanation.strip(),
            )
            db.add(row)
            db.flush()
            for idx, text in enumerate(req.options or []):
                db.add(QuestionOption(question_id=row.id, text=text.strip(), is_correct=(idx == req.correct_answer)))
            db.commit()
            return {"ok": True, "id": row.id}

        if not req.id:
            raise HTTPException(status_code=400, detail="Question id is required for update")

        row = db.query(Question).filter(Question.id == req.id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        row.text = req.question.strip()
        row.topic = category
        row.difficulty = difficulty
        row.explanation = req.explanation.strip()
        db.query(QuestionOption).filter(QuestionOption.question_id == row.id).delete()
        for idx, text in enumerate(req.options or []):
            db.add(QuestionOption(question_id=row.id, text=text.strip(), is_correct=(idx == req.correct_answer)))
        db.commit()
        return {"ok": True}

    raise HTTPException(status_code=400, detail="Unsupported action")


def _map_instructor_difficulty_to_bank(difficulty: str) -> str:
    d = (difficulty or "").strip()
    return {
        "Beginner": "Easy",
        "Intermediate": "Medium",
        "Advanced": "Hard",
    }.get(d, d)


def _parse_ai_question_json(raw: str) -> list:
    raw_s = (raw or "").strip()
    if raw_s.startswith("```"):
        raw_s = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw_s)
        raw_s = re.sub(r"\s*```$", "", raw_s)
    try:
        parsed = json.loads(raw_s)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        m = re.search(r"\[[\s\S]*\]", raw_s)
        if not m:
            return []
        parsed = json.loads(m.group(0))
        return parsed if isinstance(parsed, list) else []


def _generate_questions_with_ai(topic: str, difficulty: str, num_questions: int) -> list[dict]:
    """
    Prefer OpenAI (OPENAI_API_KEY). If unset or failing, use Serper.dev web search (SERPER_API_KEY).
    """
    oa = _openai_key()
    use_openai = oa and (oa.startswith("sk-") or oa.startswith("sk-proj-"))
    if use_openai:
        try:
            import openai

            openai.api_key = oa
            model = os.getenv("AI_MENTOR_MODEL", "gpt-4o-mini")
            prompt = (
                f"Generate {num_questions} multiple-choice quiz "
                f"questions about {topic} at {difficulty} level for "
                f"a cybersecurity course. Each question must have "
                f"exactly 4 options with exactly 1 correct answer. "
                f"Return ONLY valid JSON array with this exact schema: "
                f'[{{"question": "...", "options": ["A","B","C","D"], '
                f'"correct_index": 0, "explanation": "..."}}]. '
                f"No markdown, no code blocks, just the JSON array."
            )
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity instructor. Reply with JSON only, no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                timeout=60,
            )
            content = response.choices[0].message["content"]
            questions = _parse_ai_question_json(content)
            if not isinstance(questions, list):
                questions = []
            out: list[dict] = []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                opts = q.get("options") or []
                ci = q.get("correct_index")
                if len(opts) != 4 or ci not in (0, 1, 2, 3):
                    continue
                out.append(q)
            if out:
                return out
        except Exception as e:
            print(f"OpenAI quiz generation failed: {e}")

    if serper_configured():
        serp = build_quiz_questions_from_serper(topic, difficulty, num_questions)
        if serp:
            return serp
    return []


def _select_from_bank(
    db: Session,
    exclude_ids: set[int],
    bank_diff: str,
    topic_raw: str,
    mixed_topic: bool,
    need: int,
) -> tuple[list[Question], bool]:
    mixed_topics = False
    selected: list[Question] = []
    base = db.query(Question).filter(Question.difficulty == bank_diff)
    if exclude_ids:
        base = base.filter(~Question.id.in_(exclude_ids))
    if not mixed_topic:
        term = f"%{topic_raw}%"
        matched = base.filter(or_(Question.topic.ilike(term), Question.text.ilike(term))).all()
    else:
        matched = base.all()

    pool = list(matched)
    random.shuffle(pool)
    for q in pool:
        if len(selected) >= need:
            break
        selected.append(q)

    if len(selected) < need:
        mixed_topics = True
        have = {q.id for q in selected} | exclude_ids
        q_same = db.query(Question).filter(Question.difficulty == bank_diff)
        if have:
            q_same = q_same.filter(~Question.id.in_(have))
        rest_same_diff = q_same.all()
        random.shuffle(rest_same_diff)
        for q in rest_same_diff:
            if len(selected) >= need:
                break
            selected.append(q)

    if len(selected) < need:
        have = {q.id for q in selected} | exclude_ids
        q_any = db.query(Question)
        if have:
            q_any = q_any.filter(~Question.id.in_(have))
        rest_any = q_any.all()
        random.shuffle(rest_any)
        for q in rest_any:
            if len(selected) >= need:
                break
            selected.append(q)
            mixed_topics = True

    return selected, mixed_topics


@router.post("/ai-generate-and-assign", response_model=AIQuizAssignResponse)
def ai_generate_and_assign(
    body: AIQuizAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    if body.num_questions < 5 or body.num_questions > 20:
        raise HTTPException(status_code=400, detail="num_questions must be between 5 and 20")
    if not body.student_ids:
        raise HTTPException(status_code=400, detail="At least one student must be selected")

    rows = db.query(User).filter(User.id.in_(body.student_ids)).all()
    found_ids = {r.id for r in rows}
    missing = sorted({i for i in body.student_ids if i not in found_ids})
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown user id(s): {missing}")
    non_students = sorted({r.id for r in rows if r.role != "user"})
    if non_students:
        raise HTTPException(status_code=400, detail=f"These user ids are not students with role 'user': {non_students}")

    bank_diff = _map_instructor_difficulty_to_bank(body.difficulty)
    topic_raw = (body.topic or "").strip()
    mixed_topic = topic_raw in ("", "Mixed (All Topics)")

    topic_label = topic_raw or "Mixed (All Topics)"
    ai_topic = topic_label if topic_label != "Mixed (All Topics)" else "cybersecurity vulnerabilities (mixed topics)"

    ai_questions = _generate_questions_with_ai(ai_topic, body.difficulty, body.num_questions)
    selected_ids: list[int] = []
    topic_for_q = topic_label if topic_label != "Mixed (All Topics)" else "Mixed"
    ai_questions_created = 0

    if ai_questions:
        for q in ai_questions[: body.num_questions]:
            qtext = (q.get("question") or "").strip()
            if not qtext:
                continue
            opts = q.get("options") or []
            ci = int(q.get("correct_index", 0))
            row = Question(
                text=qtext,
                type="mcq",
                topic=topic_for_q[:50] if topic_for_q else "General",
                difficulty=bank_diff,
                explanation=(q.get("explanation") or "").strip(),
            )
            db.add(row)
            db.flush()
            for oi, opt in enumerate(opts):
                db.add(
                    QuestionOption(
                        question_id=row.id,
                        text=(str(opt) or "")[:255],
                        is_correct=(oi == ci),
                    )
                )
            selected_ids.append(row.id)
            ai_questions_created += 1
        db.commit()

    ai_used = ai_questions_created > 0
    need_bank = body.num_questions - len(selected_ids)
    mixed_topics = False
    if need_bank > 0:
        bank_rows, mixed_topics = _select_from_bank(
            db,
            exclude_ids=set(selected_ids),
            bank_diff=bank_diff,
            topic_raw=topic_raw,
            mixed_topic=mixed_topic,
            need=need_bank,
        )
        selected_ids.extend(q.id for q in bank_rows)

    if len(selected_ids) < 5:
        raise HTTPException(
            status_code=400,
            detail="Not enough questions in the bank to satisfy at least 5 questions for this quiz.",
        )

    selected_ids = selected_ids[: body.num_questions]

    today = date.today().isoformat()
    title = f"AI Generated: {topic_raw or 'Mixed topics'} ({body.difficulty}) — {today}"
    time_limit = _validate_time_limit(body.time_limit_minutes)
    due = _parse_due_date(body.due_date)

    assign = QuizAssignment(
        title=title,
        instructor_id=user.id,
        question_ids=",".join(map(str, selected_ids)),
        assigned_student_ids=",".join(map(str, body.student_ids)),
        time_limit_minutes=time_limit,
        due_date=due,
    )
    db.add(assign)
    db.flush()
    for sid in body.student_ids:
        db.add(QuizAssignmentStudent(assignment_id=assign.id, student_id=sid))
    for qid in selected_ids:
        db.add(QuizAssignmentQuestion(assignment_id=assign.id, question_id=qid))
    db.commit()
    db.refresh(assign)

    return AIQuizAssignResponse(
        assignment_id=assign.id,
        title=title,
        topic=topic_raw or "Mixed (All Topics)",
        difficulty=body.difficulty,
        questions_selected=len(selected_ids),
        students_assigned=len(body.student_ids),
        mixed_topics=mixed_topics,
        message="Quiz generated and assigned successfully.",
        ai_generated=ai_used,
        ai_questions_created=ai_questions_created if ai_used else 0,
    )


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def _format_bank_questions(questions: list[Question]) -> list[dict]:
    out: list[dict] = []
    for q in questions:
        opts = list(q.options)
        try:
            opts.sort(key=lambda o: o.id)
        except Exception:
            pass
        correct_index = next((i for i, o in enumerate(opts) if o.is_correct), 0)
        out.append(
            {
                "id": q.id,
                "text": q.text,
                "type": q.type or "MCQ",
                "topic": q.topic or "General",
                "difficulty": q.difficulty or "Medium",
                "explanation": q.explanation or "",
                "options": [{"id": o.id, "text": o.text, "is_correct": o.is_correct} for o in opts],
                "correct_index": correct_index,
            }
        )
    return out


def _collect_wrong_answers(db: Session, user_id: int, limit: int = 20) -> list[UserAnswer]:
    return (
        db.query(UserAnswer)
        .options(joinedload(UserAnswer.question).joinedload(Question.options))
        .filter(UserAnswer.user_id == user_id, UserAnswer.is_correct.is_(False))
        .order_by(desc(UserAnswer.timestamp))
        .limit(limit)
        .all()
    )


def _wrong_answers_prompt_block(db: Session, wrong_rows: list[UserAnswer]) -> tuple[str, list[str]]:
    wrong_answers_text = ""
    mistake_topics: list[str] = []
    for wa in wrong_rows:
        q = wa.question
        if not q:
            continue
        wrong_opt = (
            db.query(QuestionOption).filter(QuestionOption.id == wa.selected_option_id).first()
        )
        correct_opt = db.query(QuestionOption).filter(
            QuestionOption.question_id == q.id, QuestionOption.is_correct.is_(True)
        ).first()
        wrong_txt = (wrong_opt.text if wrong_opt else "?")[:500]
        correct_txt = (correct_opt.text if correct_opt else "?")[:500]
        topic = (q.topic or "General")[:80]
        mistake_topics.append(topic)
        wrong_answers_text += f"""
      Question: {q.text}
      Student answered: {wrong_txt}
      Correct answer: {correct_txt}
      Topic: {topic}
      """
    weak_topics = list({t for t in mistake_topics})
    return wrong_answers_text, weak_topics


def _common_mistakes_fallback(db: Session, wrong_rows: list[UserAnswer]) -> dict:
    topic_counts: dict[str, int] = {}
    for wa in wrong_rows:
        topic = (wa.question.topic if wa.question else None) or "General"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    weakest_topics = sorted(topic_counts.keys(), key=lambda t: topic_counts[t], reverse=True)[:3]
    bank_questions: list[Question] = []
    for topic in weakest_topics:
        qs = db.query(Question).filter(Question.topic.ilike(f"%{topic}%")).limit(4).all()
        bank_questions.extend(qs)
    seen: set[int] = set()
    unique: list[Question] = []
    for q in bank_questions:
        if q.id not in seen:
            seen.add(q.id)
            unique.append(q)
    formatted = _format_bank_questions(unique[:10])
    return {
        "questions": formatted,
        "total": len(formatted),
        "ai_generated": False,
        "weak_topics": weakest_topics,
        "mistake_patterns": [],
        "message": "Generated from question bank (AI not configured).",
    }


def _generate_common_mistakes_payload(db: Session, user_id: int, save_ai_to_bank: bool = True) -> dict:
    wrong_rows = _collect_wrong_answers(db, user_id, 20)
    if len(wrong_rows) < 3:
        raise HTTPException(
            status_code=400,
            detail=(
                "Not enough quiz history to generate a mistakes quiz. "
                "Complete at least one quiz with some wrong answers first."
            ),
        )
    wrong_answers_text, weak_topics = _wrong_answers_prompt_block(db, wrong_rows)

    prompt = f"""
    A cybersecurity student got these quiz questions wrong:

    {wrong_answers_text}

    Analyze the patterns in their mistakes. Then generate
    10 multiple-choice quiz questions specifically targeting
    the concepts they are struggling with. Focus on:
    - The exact misconceptions shown in their wrong answers
    - Similar but slightly different scenarios to test true understanding
    - Common security mistakes related to their weak topics

    Return ONLY a valid JSON array with this exact schema:
    [{{
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_index": 0,
      "explanation": "...",
      "targets_mistake": "Brief description of which misconception this targets"
    }}]
    No markdown. No code blocks. Pure JSON array only.
    """

    if not (OPENAI_API_KEY or "").strip():
        return _common_mistakes_fallback(db, wrong_rows)

    ai_questions: list[dict] = []
    try:
        response = httpx.post(
            f"{AI_SERVICE_URL.rstrip('/')}/generate",
            json={"prompt": prompt, "api_key": OPENAI_API_KEY},
            timeout=45.0,
        )
        if response.status_code != 200:
            raise RuntimeError(f"AI service error: {response.status_code}")
        data = response.json()
        raw = data.get("content") or data.get("text") or ""
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            raw = raw.strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        ai_questions = json.loads(raw.strip())
        if not isinstance(ai_questions, list):
            ai_questions = []
    except Exception:
        return _common_mistakes_fallback(db, wrong_rows)

    if not ai_questions:
        return _common_mistakes_fallback(db, wrong_rows)

    mistake_patterns: list[str] = []
    saved_ids: list[int] = []
    if save_ai_to_bank and ai_questions:
        for q in ai_questions[:10]:
            if not isinstance(q, dict):
                continue
            opts = q.get("options") or []
            ci = int(q.get("correct_index", 0))
            if len(opts) != 4 or ci not in (0, 1, 2, 3):
                continue
            tm = (q.get("targets_mistake") or "")[:500]
            if tm:
                mistake_patterns.append(tm)
            new_q = Question(
                text=(q.get("question") or "")[:8000],
                type="MCQ",
                topic="Common Mistakes",
                difficulty="Adaptive",
                explanation=(q.get("explanation") or "")[:4000],
                targets_mistake=tm or None,
            )
            db.add(new_q)
            db.flush()
            for i, opt_text in enumerate(opts):
                db.add(
                    QuestionOption(
                        question_id=new_q.id,
                        text=(str(opt_text) or "")[:255],
                        is_correct=(i == ci),
                    )
                )
            saved_ids.append(new_q.id)
        db.commit()
        if not saved_ids:
            return _common_mistakes_fallback(db, wrong_rows)
        saved_qs = db.query(Question).filter(Question.id.in_(saved_ids)).all()
        # preserve order
        id_order = {i: j for j, i in enumerate(saved_ids)}
        saved_qs.sort(key=lambda x: id_order.get(x.id, 999))
        formatted = _format_bank_questions(saved_qs)
        return {
            "questions": formatted,
            "total": len(formatted),
            "ai_generated": True,
            "weak_topics": weak_topics,
            "mistake_patterns": mistake_patterns[:10],
            "message": "Quiz generated from your mistake history.",
        }

    return _common_mistakes_fallback(db, wrong_rows)


@router.get("/wrong-answer-count")
def wrong_answer_count(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("user")),
):
    count = (
        db.query(UserAnswer)
        .filter(UserAnswer.user_id == user.id, UserAnswer.is_correct.is_(False))
        .count()
    )
    return {"count": count, "enough": count >= 3}


@router.post("/common-mistakes-quiz")
def common_mistakes_quiz(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("user")),
):
    return _generate_common_mistakes_payload(db, user.id, save_ai_to_bank=True)


@router.post("/assign-mistakes-quiz")
def assign_mistakes_quiz(
    body: MistakesQuizAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "instructor")),
):
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.role != "user":
        raise HTTPException(status_code=400, detail="Target must be a student (role user)")

    payload = _generate_common_mistakes_payload(db, body.student_id, save_ai_to_bank=True)
    questions = payload.get("questions") or []
    if not questions:
        raise HTTPException(status_code=400, detail="Could not generate questions for this student")

    n = max(1, min(int(body.num_questions or 10), len(questions)))
    questions = questions[:n]
    q_ids = [int(q["id"]) for q in questions if q.get("id") is not None]

    today = date.today().isoformat()
    title = f"Common Mistakes Quiz — {student.email} — {today}"
    time_limit = _validate_time_limit(body.time_limit_minutes)
    due = _parse_due_date(body.due_date)
    assign = QuizAssignment(
        title=title,
        instructor_id=user.id,
        question_ids=",".join(map(str, q_ids)),
        assigned_student_ids=str(body.student_id),
        time_limit_minutes=time_limit,
        due_date=due,
    )
    db.add(assign)
    db.flush()
    db.add(QuizAssignmentStudent(assignment_id=assign.id, student_id=body.student_id))
    for qid in q_ids:
        db.add(QuizAssignmentQuestion(assignment_id=assign.id, question_id=qid))
    db.commit()
    db.refresh(assign)

    return {
        "assignment_id": assign.id,
        "title": title,
        "student_id": body.student_id,
        "question_count": len(q_ids),
        "ai_generated": payload.get("ai_generated"),
        "message": f"Mistakes quiz assigned to {student.email}.",
    }