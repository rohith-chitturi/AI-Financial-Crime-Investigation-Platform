from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.schemas.role import RoleResponse

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    role_id: Optional[UUID] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[UUID] = None

class UserResponse(UserBase):
    id: UUID
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True
