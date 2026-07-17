from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(String, nullable=False) # e.g., 'checking', 'savings', 'business'
    balance = Column(Numeric(15, 2), default=0.00)
    currency = Column(String, default="USD")
    status = Column(String, default="active") # e.g., 'active', 'dormant', 'suspended'
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("now()"))

    customer = relationship("Customer", back_populates="accounts")
    
    # We will define relationships in Transaction model but can also back_populate here
    transactions_sent = relationship("Transaction", foreign_keys="[Transaction.source_account_id]", back_populates="source_account")
    transactions_received = relationship("Transaction", foreign_keys="[Transaction.destination_account_id]", back_populates="destination_account")
