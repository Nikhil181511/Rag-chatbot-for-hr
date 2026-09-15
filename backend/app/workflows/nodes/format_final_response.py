from typing import Dict, Any
from app.workflows.graph_state import RAGState


async def format_final_response_node(state: RAGState) -> Dict[str, Any]:
    final_answer = state.get("draft_answer") or state.get("final_answer") or ""
    return {
        "final_answer": final_answer,
        "final_answer_status": state.get("final_answer_status") or "SUCCESS",
    }
