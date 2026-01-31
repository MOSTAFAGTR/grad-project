from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ===========================
# USER & AUTH SCHEMAS
# ===========================
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = 'user' 

# Specialized schema for Admins creating other Admins (no role selection needed)
class UserCreateAdmin(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    is_approved: bool
    class Config:
        from_attributes = True

class LoginAttempt(BaseModel):
    username: str 
    password: str

# --- USER SEARCH (For Admin) ---
class UserSearchResponse(BaseModel):
    id: int
    email: str
    role: str
    is_approved: bool
    class Config:
        from_attributes = True

# ===========================
# CHALLENGE SCHEMAS
# ===========================
class CodeSubmission(BaseModel):
    code: str

class CommentCreate(BaseModel):
    author: str
    content: str

class CommentResponse(BaseModel):
    id: int
    author: str
    content: str
    class Config:
        from_attributes = True

class ProgressResponse(BaseModel):
    challenge_id: str
    completed_at: datetime
    class Config:
        from_attributes = True

# ===========================
# QUIZ & ASSIGNMENT SCHEMAS
# ===========================

# --- Options ---
class OptionBase(BaseModel):
    text: str
    is_correct: bool

class OptionCreate(OptionBase):
    pass

class OptionResponse(OptionBase):
    id: int
    class Config:
        from_attributes = True

# --- Questions ---
class QuestionBase(BaseModel):
    text: str
    type: str 
    topic: str
    difficulty: str
    skill_focus: str
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    options: List[OptionCreate]

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    explanation: Optional[str] = None

class QuestionResponse(QuestionBase):
    id: int
    options: List[OptionResponse]
    class Config:
        from_attributes = True

# --- Quiz Interaction ---
class QuizRequest(BaseModel):
    topics: List[str]
    count: int
    difficulty: Optional[str] = None
    mode: str = "Practice" 

class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: int

class AnswerResponse(BaseModel):
    correct: bool
    explanation: str

# --- AI ---
class AIGenerationRequest(BaseModel):
    topic: str
    count: int
    difficulty: str
    skill_focus: str = "General"

# --- ASSIGNMENTS ---
class AssignmentCreate(BaseModel):
    title: str
    student_ids: List[int]
    question_ids: List[int]

class AssignmentResponse(BaseModel):
    id: int
    title: str
    instructor_id: int
    created_at: datetime
    class Config:
        from_attributes = True