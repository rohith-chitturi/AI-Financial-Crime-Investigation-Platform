from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False) # e.g., 'retail', 'software', 'groceries'
    country = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("now()"))

    # Transactions sent to this merchant (we can map this by destination account or by merchant_id directly on transaction)
    # Often, merchants have accounts, but for synthetic data, it's easier to link transaction -> merchant directly
    transactions = relationship("Transaction", back_populates="merchant")
