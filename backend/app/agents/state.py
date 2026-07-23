from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel

class InvestigationState(TypedDict, total=False):
    # Context IDs
    investigation_id: str
    transaction_id: str
    customer_id: str
    alert_id: Optional[str]
    risk_analysis_id: Optional[str]
    trigger_source: str # 'AUTO' or 'MANUAL'
    
    # Input Evidence
    ml_score: float
    aml_findings: List[Dict[str, Any]]
    graph_findings: Dict[str, Any]
    customer_summary: Dict[str, Any]
    
    # Placeholder for Phase 6
    regulatory_summary: Optional[str]
    
    # Generated Outputs
    evidence: str
    recommendations: List[str]
    confidence_score: float
    report_markdown: str
    
    # Execution Metadata
    processing_log: List[Dict[str, Any]] # Stores AgentExecution details
    execution_metadata: Dict[str, Any]
    errors: List[Dict[str, Any]]
