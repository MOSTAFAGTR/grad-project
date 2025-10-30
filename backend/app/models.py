
from sqlalchemy import Column, Integer, String
from .db.database import Base

# This file now only defines the tables for the main application,
# not the challenge-specific tables.

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))