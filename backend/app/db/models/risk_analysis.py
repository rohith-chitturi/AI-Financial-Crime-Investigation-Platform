from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.models.base import Base

class TransactionRiskAnalysis(Base):
    __tablename__ = "transaction_risk_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, unique=True, index=True)
    
    model_version = Column(String, nullable=False)
    
    ml_score = Column(Float, nullable=False) # 0 to 100
    aml_rule_score = Column(Float, nullable=False) # 0 to 100
    customer_risk_score = Column(Float, nullable=False) # 0 to 100
    unified_risk_score = Column(Float, nullable=False) # 0 to 100
    
    risk_level = Column(String, nullable=False) # 'Low', 'Medium', 'High', 'Critical'
    
    triggered_rules = Column(JSONB, default=list) # List of dictionaries containing rule details
    explanation = Column(String, nullable=False) # Human readable explanation
    
    processing_time_ms = Column(Integer, nullable=True)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    transaction = relationship("Transaction")
