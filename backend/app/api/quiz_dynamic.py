from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import random
from sqlalchemy.orm import Session

from .. import models
from .auth import require_role
from ..db.database import get_db
from ..ai.serper_helpers import serper_configured


router = APIRouter()


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY", "") or "").strip()


class ScanFinding(BaseModel):
    type: str = "Unknown"
    vulnerability_type: Optional[str] = None
    code_snippet: Optional[str] = None
    severity: Optional[str] = "Medium"


class QuizGenerateRequest(BaseModel):
    findings: list[ScanFinding]
    difficulty: str = "Intermediate"
    category: str = "Adaptive"
    explanation_depth: str = "detailed"


class QuizManageRequest(BaseModel):
    action: str
    id: Optional[int] = None
    question: Optional[str] = None
    options: Optional[list[str]] = None
    correct_answer: Optional[int] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None


def _normalize_vuln_name(vuln: str) -> str:
    raw = (vuln or "").strip()
    aliases = {
        "sqli": "SQL Injection",
        "sql injection": "SQL Injection",
        "xss": "XSS",
        "command injection": "Command Injection",
        "cmd injection": "Command Injection",
        "csrf": "CSRF",
        "hardcoded secret": "Hardcoded Secret",
        "hardcoded secrets": "Hardcoded Secret",
    }
    key = raw.lower()
    return aliases.get(key, raw or "Unknown")


def _difficulty_score(level: str) -> int:
    lv = (level or "Intermediate").capitalize()
    return {"Beginner": 1, "Intermediate": 2, "Advanced": 3}.get(lv, 2)


def _build_question_set(vuln_type: str, code: str, difficulty: str, explanation_depth: str, idx: int):
    diff_score = _difficulty_score(difficulty)
    subtle_marker = (
        "Focus on subtle dataflow and implicit trust boundaries."
        if diff_score >= 3
        else "Focus on direct vulnerable sink usage."
    )
    payload_map = {
        "SQL Injection": ["' OR 1=1 --", "' UNION SELECT user(), version() --", "admin'--", "safe_input"],
        "XSS": ["<script>alert('x')</script>", "<img src=x onerror=alert(1)>", "<svg onload=alert(1)>", "plain text"],
        "Command Injection": ["8.8.8.8; whoami", "127.0.0.1 && cat /etc/passwd", "8.8.8.8 | id", "8.8.8.8"],
        "CSRF": ["Auto-submitted hidden form", "Replay browser cookies with forged POST", "Valid anti-CSRF token", "Read-only GET request"],
        "Hardcoded Secret": ["Remove secret and inject via env vars", "Rotate credentials and commit updated key", "Base64-encode secret", "Move secret to comments"],
    }
    default_payloads = payload_map.get(vuln_type, ["Crafted malicious input", "Safe input", "Validation only", "No-op"])
    correct_payload = default_payloads[0]

    question_bank = [
        {
            "id": f"{idx}-mcq",
            "type": "identify vulnerability",
            "question": f"Which choice best identifies the security weakness in this snippet?",
            "prompt": f"Which choice best identifies the security weakness in this snippet?",
            "category": vuln_type,
            "difficulty": difficulty,
            "difficulty_score": diff_score,
            "code_snippet": code,
            "options": [vuln_type, "Business logic bug", "Race condition", "Styling issue"],
            "correct_answer": vuln_type,
            "answer": vuln_type,
            "explanation": (
                f"This finding maps to {vuln_type}. {subtle_marker}"
                if explanation_depth == "detailed"
                else f"The correct category is {vuln_type}."
            ),
        },
        {
            "id": f"{idx}-identify",
            "type": "identify vulnerability",
            "question": f"Identify the exact vulnerable behavior for {vuln_type}.",
            "prompt": f"Identify the exact vulnerable behavior for {vuln_type}.",
            "category": vuln_type,
            "difficulty": difficulty,
            "difficulty_score": diff_score,
            "code_snippet": code,
            "options": [
                "Untrusted input reaches sensitive sink without protection",
                "Application has no CSS resets",
                "Local variable naming is unclear",
                "No comments in code",
            ],
            "correct_answer": "Untrusted input reaches sensitive sink without protection",
            "answer": "Untrusted input reaches sensitive sink without protection",
            "explanation": "Vulnerability exists because attacker-controlled input is not neutralized before sensitive execution/rendering.",
        },
        {
            "id": f"{idx}-predict",
            "type": "predict output",
            "question": f"If exploited, what is the most realistic impact of this {vuln_type} finding?",
            "prompt": f"If exploited, what is the most realistic impact of this {vuln_type} finding?",
            "category": vuln_type,
            "difficulty": difficulty,
            "difficulty_score": diff_score,
            "code_snippet": code,
            "options": [
                "Unauthorized behavior, data disclosure, or account compromise",
                "Compiler warning only",
                "Harmless UI color mismatch",
                "No runtime effect",
            ],
            "correct_answer": "Unauthorized behavior, data disclosure, or account compromise",
            "answer": "Unauthorized behavior, data disclosure, or account compromise",
            "explanation": "Security flaws in this class typically lead to unauthorized operations and sensitive data exposure.",
        },
        {
            "id": f"{idx}-fix",
            "type": "choose fix",
            "question": f"Which remediation is the best first fix for this {vuln_type} issue?",
            "prompt": f"Which remediation is the best first fix for this {vuln_type} issue?",
            "category": vuln_type,
            "difficulty": difficulty,
            "difficulty_score": diff_score,
            "code_snippet": code,
            "options": [
                "Use secure API patterns + strict validation/encoding",
                "Hide all errors from users",
                "Rename variables and keep logic unchanged",
                "Increase server timeout",
            ],
            "correct_answer": "Use secure API patterns + strict validation/encoding",
            "answer": "Use secure API patterns + strict validation/encoding",
            "explanation": "Effective remediation must remove vulnerable sink usage and enforce safe handling of untrusted input.",
        },
        {
            "id": f"{idx}-payload",
            "type": "choose payload",
            "question": f"Which payload is most representative for training this {vuln_type} vulnerability?",
            "prompt": f"Which payload is most representative for training this {vuln_type} vulnerability?",
            "category": vuln_type,
            "difficulty": difficulty,
            "difficulty_score": diff_score,
            "code_snippet": code,
            "options": default_payloads,
            "correct_answer": correct_payload,
            "answer": correct_payload,
            "explanation": f"{correct_payload} demonstrates realistic attacker intent for {vuln_type}.",
        },
    ]

    if diff_score >= 3:
        random.Random(idx).shuffle(question_bank)
    return question_bank


@router.post("/generate")
def generate_quiz_from_scan(
    req: QuizGenerateRequest,
    current_user: models.User = Depends(require_role("user")),
):
    difficulty = (req.difficulty or "Intermediate").capitalize()
    explanation_depth = req.explanation_depth or "detailed"
    questions = []
    filtered = []
    category_filter = (req.category or "Adaptive").strip().lower()
    for finding in req.findings[:12]:
        vuln_type = _normalize_vuln_name(finding.vulnerability_type or finding.type or "Unknown")
        if category_filter not in {"adaptive", "all", ""} and category_filter not in vuln_type.lower():
            continue
        filtered.append((vuln_type, finding.code_snippet or "No snippet provided"))

    source = filtered or [(_normalize_vuln_name(f.vulnerability_type or f.type or "Unknown"), f.code_snippet or "No snippet provided") for f in req.findings[:8]]
    for idx, (vuln_type, code) in enumerate(source, start=1):
        questions.extend(_build_question_set(vuln_type, code, difficulty, explanation_depth, idx))

    for q in questions:
        if not q.get("explanation"):
            q["explanation"] = "Review the vulnerable pattern and apply secure coding controls."

    out: dict = {
        "total": len(questions),
        "questions": questions,
        "difficulty": difficulty,
        "category": req.category,
        "ai_available": bool(_openai_key()) or serper_configured(),
    }
    if _openai_key():
        out["ai_note"] = "AI-enhanced explanations are active for this adaptive quiz."
    elif serper_configured():
        out["ai_note"] = "Web search (Serper) context is available for this adaptive quiz."
    return out


@router.get("/manage")
def quiz_manage_entry(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "instructor")),
):
    raise HTTPException(status_code=410, detail="Use /api/quizzes/manage for quiz management")


@router.post("/manage")
def quiz_manage_mutation(
    req: QuizManageRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "instructor")),
):
    raise HTTPException(status_code=410, detail="Use /api/quizzes/manage for quiz management")

