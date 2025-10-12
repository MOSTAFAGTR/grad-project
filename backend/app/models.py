from sqlalchemy import Column, Integer, String
from .db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True) # Specify length
    hashed_password = Column(String(255)) # Specify length

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(255), index=True) # Specify length

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True) # Specify length
    description = Column(String(255), index=True) # Specify length