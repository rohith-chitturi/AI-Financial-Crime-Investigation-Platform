from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, unique=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    
    unified_risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False) # 'High', 'Critical'
    
    triggered_aml_rules = Column(JSONB, default=list) # List of rule IDs/names
    model_version = Column(String, nullable=False)
    
    status = Column(String, default="NEW", nullable=False) # 'NEW', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED', 'CLOSED'
    assigned_analyst = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction")
    customer = relationship("Customer")
