import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class TransactionIntelNode(BaseNode):
    def __init__(self):
        super().__init__("TransactionIntelligenceAgent", "transaction_intel.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            prompt = self.prompt_template.format(
                ml_score=state.get("ml_score", 0.0)
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            state["execution_metadata"] = state.get("execution_metadata", {})
            state["execution_metadata"]["transaction_intel"] = response.content
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
