from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, index=True)
    destination_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String, default="USD")
    transaction_type = Column(String, nullable=False) # 'transfer', 'deposit', 'withdrawal', 'payment'
    status = Column(String, default="completed")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    location_country = Column(String, nullable=True)

    # --- Ground Truth (Isolated for ML Training / Evaluation ONLY) ---
    is_suspicious_ground_truth = Column(Boolean, default=False)
    suspicious_pattern_type = Column(String, nullable=True) # e.g., 'STRUCTURING', 'MULE_NETWORK'

    # Relationships
    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="transactions_sent")
    destination_account = relationship("Account", foreign_keys=[destination_account_id], back_populates="transactions_received")
    merchant = relationship("Merchant", back_populates="transactions")
    organization = relationship("Organization", back_populates="transactions")
