import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class AMLInvestigatorNode(BaseNode):
    def __init__(self):
        super().__init__("AMLInvestigatorAgent", "aml_investigator.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            aml_findings_str = json.dumps(state.get("aml_findings", []), indent=2)
            prompt = self.prompt_template.format(
                aml_findings=aml_findings_str
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            state["execution_metadata"] = state.get("execution_metadata", {})
            state["execution_metadata"]["aml_intel"] = response.content
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
