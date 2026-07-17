from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TransactionBase(BaseModel):
    source_account_id: Optional[UUID] = None
    destination_account_id: Optional[UUID] = None
    merchant_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    amount: float
    currency: str
    transaction_type: str
    status: str
    timestamp: datetime
    location_country: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: UUID
    # Intentionally EXCLUDING is_suspicious_ground_truth and suspicious_pattern_type
    # to prevent data leakage to the UI/Investigation agents.

    class Config:
        from_attributes = True

class TransactionList(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
