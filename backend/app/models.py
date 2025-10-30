from sqlalchemy import Column, Integer, String, Text
from .db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Question(id={self.id}, text='{self.text[:30]}...')>"


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Challenge(id={self.id}, title='{self.title}')>"
