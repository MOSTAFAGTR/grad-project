from pydantic import BaseModel

# --- User Schemas (already exist) ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

# --- Add the new Question Schema ---
class Question(BaseModel):
    id: int
    text: str
    type: str # e.g., 'MCQ' or 'T-F'
    answer: str
    explanation: str

    class Config:
        orm_mode = True