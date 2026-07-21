import time
from app.agents.state import InvestigationState

def regulatory_node(state: InvestigationState) -> InvestigationState:
    """
    Placeholder for Phase 6.
    Returns static placeholder for now.
    """
    start_time = time.time()
    
    placeholder = "No regulatory retrieval configured."
    state["regulatory_summary"] = placeholder
    
    end_time = time.time()
    execution_record = {
        "agent_name": "RegulatoryIntelligenceAgent",
        "prompt_version": "v1.0",
        "model_version": "placeholder",
        "start_time": start_time,
        "end_time": end_time,
        "latency_ms": int((end_time - start_time) * 1000),
        "status": "SUCCESS",
        "output_summary": {"response": placeholder},
        "error_details": None
    }
    
    if "processing_log" not in state or state["processing_log"] is None:
        state["processing_log"] = []
    state["processing_log"].append(execution_record)
    
    return state
