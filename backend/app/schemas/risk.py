from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class TriggeredRule(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    severity: str
    risk_contribution: float

class TransactionRiskAnalysisResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    model_version: str
    ml_score: float
    aml_rule_score: float
    customer_risk_score: float
    unified_risk_score: float
    risk_level: str
    triggered_rules: List[Dict[str, Any]]
    explanation: str
    processing_time_ms: Optional[int]
    analysis_timestamp: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    customer_id: UUID
    unified_risk_score: float
    risk_level: str
    triggered_aml_rules: List[Dict[str, Any]]
    model_version: str
    status: str
    assigned_analyst: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    size: int
