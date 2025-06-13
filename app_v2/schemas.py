from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Tuple, Any


class ProjectBase(BaseModel):
    project_id: int
    name: str
    description: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    """
    Fields required for client to create a new user.
    """
    email: EmailStr
    name: str
    password: str  # plaintext (to be hashed later)
    pic: Optional[str] = None
    company: Optional[str] = None
    dark_mode: Optional[bool] = False
    role: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    pic: Optional[str] = None
    company: Optional[str] = None
    dark_mode: Optional[bool] = None
    role: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None


class UserOut(BaseModel):
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
    pic: Optional[str]
    company: Optional[str]
    dark_mode: bool
    role: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    zipcode: Optional[str]

    projects: List[ProjectBase] = []
    
    class Config:
        orm_mode = True  # tell Pydantic to read data from ORM model


class UserOutProjects(BaseModel):
    projects: List[ProjectBase] = []


# ----- Token schemas -----
class Token(BaseModel):
    access_token: str
    token_type: str  # always "bearer"
    refresh_token: Optional[str] = None  


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# Document Upload
class FileUploadResponse(BaseModel):
    detail: str
    project_id: str

# Chat Schemas
class ChatQuery(BaseModel):
    question: str
    history: List[Tuple[str, str]] = []
    file_name: List[str] 
    top_k: int = 4  # how many docs to retrieve
    project_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]           
    updated_history: List[Tuple[str, str]]