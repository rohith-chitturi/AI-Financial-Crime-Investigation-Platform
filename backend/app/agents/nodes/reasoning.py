import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class ReasoningNode(BaseNode):
    def __init__(self):
        super().__init__("InvestigationReasoningAgent", "reasoning.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            metadata = state.get("execution_metadata", {})
            
            prompt = self.prompt_template.format(
                ml_analysis=metadata.get("transaction_intel", "N/A"),
                aml_analysis=metadata.get("aml_intel", "N/A"),
                graph_analysis=metadata.get("graph_intel", "N/A"),
                customer_analysis=metadata.get("customer_intel", "N/A"),
                regulatory_analysis=state.get("regulatory_summary", "N/A")
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            
            # Parse JSON
            parsed = self.parse_json_response(response.content)
            
            state["evidence"] = parsed.get("evidence_summary", "")
            state["confidence_score"] = float(parsed.get("confidence_score", 0.0))
            
            metadata["reasoning_intel"] = parsed
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
