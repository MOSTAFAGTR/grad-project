from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db.database import Base

# --- USER MODEL ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default='user')
    
    # Gatekeeping field:
    # Students/Admins = True
    # New Instructors = False (Pending)
    is_approved = Column(Boolean, default=True) 

    answers = relationship("UserAnswer", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

# --- PROGRESS MODEL ---
class UserProgress(Base):  # <--- FIXED: Inherits from Base now
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    challenge_id = Column(String(50))
    completed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="progress")

# --- CHALLENGE MODELS ---
class XSSComment(Base):
    __tablename__ = "xss_comments"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(255))
    content = Column(Text)

class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(255))

# --- QUIZ BANK MODELS ---
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    type = Column(String(20)) 
    topic = Column(String(50))
    difficulty = Column(String(20))
    skill_focus = Column(String(50))
    explanation = Column(Text)
    
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("UserAnswer", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option_id = Column(Integer, ForeignKey("question_options.id")) 
    is_correct = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class QuizAssignment(Base):
    __tablename__ = "quiz_assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    
    assigned_student_ids = Column(Text) 
    question_ids = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)