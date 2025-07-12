from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: Optional[str] = None

class NoteCreate(BaseModel):
    text: str

class NoteUpdate(BaseModel):
    text: str

class NoteOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    class Config:
        orm_mode = True

