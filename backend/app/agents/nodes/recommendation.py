import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class RecommendationNode(BaseNode):
    def __init__(self):
        super().__init__("RecommendationAgent", "recommendation.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            metadata = state.get("execution_metadata", {})
            reasoning_intel = metadata.get("reasoning_intel", {})
            assessment_summary = reasoning_intel.get("overall_assessment", "N/A")
            
            prompt = self.prompt_template.format(
                assessment_summary=assessment_summary,
                confidence_score=state.get("confidence_score", 0.0)
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            
            parsed = self.parse_json_response(response.content)
            state["recommendations"] = parsed.get("recommendations", [])
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
