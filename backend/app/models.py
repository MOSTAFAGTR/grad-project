from sqlalchemy import Column, Integer, String, Text
from .db.database import Base

# Main, secure user table
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default='user')

# Table for Quizzes
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(255), index=True)

# Table for Challenges (general info)
class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(String(255), index=True)

# --- NEW: Table for XSS Attack Simulation ---
class XSSComment(Base):
    __tablename__ = "xss_comments"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(255))
    content = Column(Text) # Text type to allow long scripts