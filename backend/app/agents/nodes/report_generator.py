import time
import json
from langchain_core.messages import SystemMessage
from app.agents.state import InvestigationState
from app.agents.nodes.base import BaseNode

class ReportGeneratorNode(BaseNode):
    def __init__(self):
        super().__init__("ReportGenerationAgent", "report_generator.txt")

    def __call__(self, state: InvestigationState) -> InvestigationState:
        start_time = time.time()
        try:
            metadata = state.get("execution_metadata", {})
            reasoning_intel = metadata.get("reasoning_intel", {})
            
            prompt = self.prompt_template.format(
                ml_analysis=metadata.get("transaction_intel", "N/A"),
                aml_analysis=metadata.get("aml_intel", "N/A"),
                graph_analysis=metadata.get("graph_intel", "N/A"),
                customer_analysis=metadata.get("customer_intel", "N/A"),
                regulatory_analysis=state.get("regulatory_summary", "N/A"),
                reasoning=reasoning_intel.get("overall_assessment", "N/A"),
                recommendations=json.dumps(state.get("recommendations", []))
            )
            
            response = self.llm.invoke([SystemMessage(content=prompt)])
            
            # The prompt requests pure markdown, no JSON wrapping
            state["report_markdown"] = response.content.strip()
            
            return self._record_execution(state, start_time, response.content)
            
        except Exception as e:
            return self._record_execution(state, start_time, "", str(e))
