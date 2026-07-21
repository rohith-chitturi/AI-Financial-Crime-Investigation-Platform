import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.models.base import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=True, index=True)
    
    trigger_source = Column(String, nullable=False) # 'AUTO', 'MANUAL'
    status = Column(String, default="IN_PROGRESS") # 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    
    # LangGraph Output Data
    summary = Column(String, nullable=True)
    recommendations = Column(JSONB, nullable=True) # list of strings
    confidence_score = Column(Float, nullable=True)
    report_markdown = Column(String, nullable=True)
    errors = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text("now()"))

    transaction = relationship("Transaction")
    customer = relationship("Customer")
    
    # One to Many executions
    agent_executions = relationship("AgentExecution", back_populates="investigation", cascade="all, delete-orphan")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id"), nullable=False, index=True)
    
    agent_name = Column(String, nullable=False, index=True)
    prompt_version = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    status = Column(String, default="SUCCESS") # 'SUCCESS', 'FAILED'
    
    input_summary = Column(JSONB, nullable=True)
    output_summary = Column(JSONB, nullable=True)
    error_details = Column(String, nullable=True)
    token_usage = Column(JSONB, nullable=True)

    investigation = relationship("Investigation", back_populates="agent_executions")
