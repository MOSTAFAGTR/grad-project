from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import json
import re
import requests
import random
import os

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
)
from .auth import get_current_user, require_role
from ..ai.serper_helpers import build_quiz_questions_from_serper, serper_configured

router = APIRouter()
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


class TutorReviewItemIn(BaseModel):
    question_id: Optional[int] = None
    question_text: str
    category: Optional[str] = None
    selected_option_id: Optional[int] = None
    selected_option_text: Optional[str] = None
    correct_option_text: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[str] = None  # bank | generated


class TutorReviewRequest(BaseModel):
    wrong_answers: List[TutorReviewItemIn]


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
    assign = QuizAssignment(
        title=d.title,
        instructor_id=user.id,
        # Keep legacy denormalized columns for backward compatibility.
        question_ids=",".join(map(str, d.question_ids)),
        assigned_student_ids=",".join(map(str, d.student_ids)),
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
    mapped_assignment_ids = [
        row.assignment_id
        for row in db.query(QuizAssignmentStudent)
        .filter(QuizAssignmentStudent.student_id == user.id)
        .all()
    ]
    if mapped_assignment_ids:
        return db.query(QuizAssignment).filter(QuizAssignment.id.in_(mapped_assignment_ids)).all()

    # Backward-compatible fallback for legacy comma-separated assignments.
    all_assignments = db.query(QuizAssignment).all()
    return [a for a in all_assignments if str(user.id) in (a.assigned_student_ids or "").split(',')]

@router.get("/assignments/{id}/take", response_model=List[QuestionResponse])
def take_assign_quiz(
    id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    a = db.query(QuizAssignment).filter(QuizAssignment.id == id).first()
    if not a: raise HTTPException(404, "Not found")
    if user.role == "user":
        mapped = (
            db.query(QuizAssignmentStudent)
            .filter(
                QuizAssignmentStudent.assignment_id == a.id,
                QuizAssignmentStudent.student_id == user.id,
            )
            .first()
        )
        if not mapped:
            assigned = {int(i) for i in (a.assigned_student_ids or "").split(',') if i}
            if user.id not in assigned:
                raise HTTPException(403, "Assignment is not assigned to this user")

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


@router.post("/post-quiz-tutor-review")
def post_quiz_tutor_review(
    req: TutorReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("user")),
):
    """
    Build grounded explanations for wrong answers after quiz completion.
    """
    wrong_answers = req.wrong_answers or []
    if not wrong_answers:
        raise HTTPException(status_code=400, detail="No wrong answers provided.")

    review = []
    for idx, item in enumerate(wrong_answers[:20], start=1):
        qid = item.question_id
        selected_text = (item.selected_option_text or "").strip()
        category = (item.category or "General").strip()

        q_db = None
        if qid is not None and qid < 100000:
            q_db = db.query(Question).filter(Question.id == qid).first()

        if q_db:
            correct_opt = next((o for o in q_db.options if o.is_correct), None)
            selected_opt = None
            if item.selected_option_id is not None:
                selected_opt = next((o for o in q_db.options if o.id == item.selected_option_id), None)
            if not selected_opt and selected_text:
                selected_opt = next((o for o in q_db.options if (o.text or "").strip() == selected_text), None)

            correct_text = (correct_opt.text if correct_opt else item.correct_option_text or "").strip()
            selected_final = (selected_opt.text if selected_opt else selected_text or "No answer selected").strip()
            explanation = (q_db.explanation or item.explanation or "").strip()
            confidence = "verified_db"
            question_text = (q_db.text or item.question_text or "").strip()
        else:
            correct_text = (item.correct_option_text or "").strip()
            selected_final = selected_text or "No answer selected"
            explanation = (item.explanation or "").strip()
            confidence = "generated_payload"
            question_text = (item.question_text or "").strip()

        if not question_text or not correct_text:
            continue

        why_wrong = (
            f"You chose '{selected_final}', but the correct answer is '{correct_text}'. "
            "Your selected option does not apply the required security control for this scenario."
        )
        why_correct = (
            explanation
            if explanation
            else "The correct option directly fixes the insecure data flow/sink behavior, not just the symptom."
        )
        next_step = (
            f"Retry a similar {category} question and explain in one sentence why '{correct_text}' is safer."
        )

        review.append(
            {
                "index": idx,
                "question": question_text,
                "category": category,
                "selected_answer": selected_final,
                "correct_answer": correct_text,
                "why_wrong": why_wrong,
                "why_correct": why_correct,
                "next_step": next_step,
                "confidence": confidence,
            }
        )

    if not review:
        raise HTTPException(status_code=400, detail="Could not build tutor review from submitted answers.")

    return {
        "total_wrong_reviewed": len(review),
        "review": review,
        "grounding": {
            "db_verified_items": sum(1 for r in review if r.get("confidence") == "verified_db"),
            "generated_items": sum(1 for r in review if r.get("confidence") == "generated_payload"),
        },
    }


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
    if body.due_date:
        title = f"{title} (due {body.due_date})"

    assign = QuizAssignment(
        title=title,
        instructor_id=user.id,
        question_ids=",".join(map(str, selected_ids)),
        assigned_student_ids=",".join(map(str, body.student_ids)),
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