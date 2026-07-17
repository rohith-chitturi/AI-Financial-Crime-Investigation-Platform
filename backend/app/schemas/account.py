from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    account_number: str
    account_type: str
    balance: float
    currency: str
    status: str
    customer_id: UUID

class AccountResponse(AccountBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class AccountList(BaseModel):
    items: List[AccountResponse]
    total: int
    page: int
    size: int
