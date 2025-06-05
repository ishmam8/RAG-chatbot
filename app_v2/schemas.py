from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Tuple, Any


# ----- Data returned when a user is created or fetched -----

class UserCreate(BaseModel):
    """
    Fields required for client to create a new user.
    """
    email: EmailStr
    name: str
    password: str


class UserOut(BaseModel):
    """
    Fields we return in response (never send hashed_password).
    """
    id: int
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True  # tell Pydantic to read data from ORM model


# ----- Token schemas -----

class Token(BaseModel):
    access_token: str
    token_type: str  # always "bearer"
    refresh_token: Optional[str] = None  


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class FileUploadResponse(BaseModel):
    detail: str

class ChatQuery(BaseModel):
    question: str
    history: List[Tuple[str, str]]  # e.g. [("Hello", "Hi! How can I help?"), ...]
    top_k: int = 4  # how many docs to retrieve

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]           # e.g. ["[File: xyz.pdf, Page 3]", …]
    updated_history: List[Tuple[str, str]]