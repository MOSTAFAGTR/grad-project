from pydantic import BaseModel
from typing import Optional # Import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    # Make role an optional field in case it's not provided
    role: Optional[str] = 'user' 

class User(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True

class Question(BaseModel):
    id: int
    text: str
    type: str
    answer: str
    explanation: str

    class Config:
        orm_mode = True