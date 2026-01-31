from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import random

app = FastAPI()

class AIGenerationRequest(BaseModel):
    topic: str
    count: int
    difficulty: str
    skill_focus: str

class OptionSchema(BaseModel):
    text: str
    is_correct: bool

class QuestionSchema(BaseModel):
    text: str
    type: str = "MCQ"
    topic: str
    difficulty: str
    skill_focus: str
    explanation: str
    options: List[OptionSchema]

@app.post("/generate", response_model=List[QuestionSchema])
def generate_questions(req: AIGenerationRequest):
    generated = []
    
    # --- SMART TEMPLATES ---
    contexts = [
        "In a legacy PHP application,", "While auditing a Python Flask API,", 
        "During a code review of a React frontend,", "In a banking system's database layer,",
        "When configuring a WAF rule,", "Inside a Docker container environment,"
    ]
    
    scenarios = [
        "a developer forgot to sanitize input", "the system uses default credentials",
        "user input is concatenated directly into a query", "headers are not being validated",
        "error messages are too verbose"
    ]
    
    impacts = [
        "leading to potential data exfiltration.", "causing a denial of service.",
        "allowing privilege escalation.", "exposing session tokens.",
        "bypassing authentication checks."
    ]

    for i in range(req.count):
        context = random.choice(contexts)
        scenario = random.choice(scenarios)
        impact = random.choice(impacts)
        
        # Build Unique Text
        q_text = f"[AI] {context} {scenario}, {impact} regarding {req.topic}. What is the best {req.skill_focus} step?"
        
        # Logic for Options
        if "sql" in req.topic.lower():
            correct = "Use parameterized queries (Prepared Statements)"
            wrongs = ["Strip quotes", "Use Base64", "Blacklist keywords", "Disable DB"]
        elif "xss" in req.topic.lower():
            correct = "Context-aware Output Encoding"
            wrongs = ["Disable HTML", "Use HTTPS", "Encrypt DB", "Filter script tags"]
        else:
            correct = f"Implement secure {req.topic} controls"
            wrongs = ["Ignore risk", "Restart server", "Use MD5", "Trust client"]

        wrong_opts = random.sample(wrongs, 3)
        options = [OptionSchema(text=correct, is_correct=True)] + [OptionSchema(text=w, is_correct=False) for w in wrong_opts]
        random.shuffle(options)

        q = QuestionSchema(
            text=q_text,
            topic=req.topic,
            difficulty=req.difficulty,
            skill_focus=req.skill_focus,
            explanation=f"The correct approach is {correct}.",
            options=options
        )
        generated.append(q)
        
    return generated