from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.guardrails.output_validator import OutputValidator


async def validate_groundedness_node(state: RAGState) -> Dict[str, Any]:
    draft_answer = state.get("draft_answer", "")
    context_chunks = state.get("selected_context", [])
    citations = state.get("citations", [])

    is_valid, status_code = OutputValidator.validate_answer(
        answer=draft_answer,
        context_chunks=context_chunks,
        citations=citations,
    )

    if not is_valid:
        return {
            "groundedness_result": "hallucination",
            "error_detail": status_code,
        }

    return {"groundedness_result": "grounded"}
