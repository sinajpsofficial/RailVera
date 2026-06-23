from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserRegister(BaseModel):
    employee_id: str
    name: str
    email: str
    password: str
    role: Optional[str] = "employee"
    division: Optional[str] = None
    department: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    employee_id: Optional[str]
    name: str
    email: str
    role: str
    division: Optional[str]
    department: Optional[str]
    is_active: bool
    created_at: datetime


    class Config:
        from_attributes = True
