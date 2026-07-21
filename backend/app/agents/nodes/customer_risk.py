import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class CustomerRiskNode(BaseNode):
    def __init__(self):
        super().__init__("CustomerRiskAgent", "customer_risk.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            customer_summary_str = json.dumps(state.get("customer_summary", {}), indent=2)
            prompt = self.prompt_template.format(
                customer_summary=customer_summary_str
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            state["execution_metadata"] = state.get("execution_metadata", {})
            state["execution_metadata"]["customer_intel"] = response.content
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
