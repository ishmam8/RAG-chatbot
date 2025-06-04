from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List


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


# # ----- Chat / Document schemas (unchanged from before) -----

# class Message(BaseModel):
#     role: str  # "user" or "assistant"
#     content: str


# class ChatRequest(BaseModel):
#     message: str
#     history: Optional[List[Message]] = None


# class ChatResponse(BaseModel):
#     answer: str
#     sources: Optional[List[str]] = None


# class DocumentUploadResponse(BaseModel):
#     success: bool
#     document_id: Optional[str] = None
#     chunks_indexed: Optional[int] = None
#     error: Optional[str] = None
