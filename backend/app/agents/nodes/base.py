import os
import json
import time
from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError
from app.agents.state import InvestigationState
from app.agents.llm_provider import get_llm_provider

class BaseNode:
    def __init__(self, node_name: str, prompt_file: str):
        self.node_name = node_name
        self.llm = get_llm_provider(temperature=0.0)
        self.prompt_template = self._load_prompt(prompt_file)

    def _load_prompt(self, prompt_file: str) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', prompt_file)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _record_execution(self, state: InvestigationState, start_time: float, output: str, error: str = None) -> InvestigationState:
        end_time = time.time()
        execution_record = {
            "agent_name": self.node_name,
            "prompt_version": "v1.0", # Simplified version tracking
            "model_version": self.llm.model if hasattr(self.llm, 'model') else "unknown",
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "latency_ms": int((end_time - start_time) * 1000),
            "status": "FAILED" if error else "SUCCESS",
            "output_summary": {"response": output[:500] + "..." if len(output) > 500 else output} if output else None,
            "error_details": error
        }
        
        if "processing_log" not in state or state["processing_log"] is None:
            state["processing_log"] = []
        state["processing_log"].append(execution_record)
        
        if error:
            import traceback
            traceback.print_exc()
            if "errors" not in state or state["errors"] is None:
                state["errors"] = []
            state["errors"].append({"agent": self.node_name, "error": error})
            
        return state

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Safely extract JSON from an LLM response that might have Markdown wrappers."""
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
