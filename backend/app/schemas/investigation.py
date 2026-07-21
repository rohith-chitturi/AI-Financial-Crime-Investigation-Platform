from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class AgentExecutionBase(BaseModel):
    agent_name: str
    prompt_version: Optional[str] = None
    model_version: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    latency_ms: Optional[int] = None
    status: str
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None

class AgentExecutionResponse(AgentExecutionBase):
    id: UUID
    investigation_id: UUID

    model_config = ConfigDict(from_attributes=True)

class InvestigationBase(BaseModel):
    transaction_id: UUID
    customer_id: UUID
    alert_id: Optional[UUID] = None
    trigger_source: str
    status: str
    summary: Optional[str] = None
    recommendations: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    report_markdown: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None

class InvestigationCreate(InvestigationBase):
    pass

class InvestigationResponse(InvestigationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    agent_executions: Optional[List[AgentExecutionResponse]] = []

    model_config = ConfigDict(from_attributes=True)
