from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None
    country: str
    risk_score: float = 0.0

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerList(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    size: int
