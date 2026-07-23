from app.agents.state import InvestigationState
from typing import Dict, Any

def coordinator_node(state: InvestigationState) -> InvestigationState:
    """
    Validates inputs and initializes workflow state.
    """
    # Coordinator is simple, it just ensures the state has necessary arrays initialized
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []
    if "processing_log" not in state or state["processing_log"] is None:
        state["processing_log"] = []
    
    return state
