from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.guardrails.output_validator import OutputValidator


async def handle_abstention_node(state: RAGState) -> Dict[str, Any]:
    reason = state.get("error_detail")
    intent = state.get("intent")

    if intent == "injection_attempt":
        msg = "I cannot fulfill this request. I am designed to assist with verified HR policy inquiries."
    else:
        msg = OutputValidator.STANDARD_ABSTENTION

    return {
        "final_answer": msg,
        "final_answer_status": "ABSTENTION",
        "citations": [],
    }
