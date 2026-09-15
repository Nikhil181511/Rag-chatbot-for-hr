import uuid
from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.guardrails.prompt_injection import PromptInjectionScreen


async def validate_request_node(state: RAGState) -> Dict[str, Any]:
    query = state.get("original_query", "").strip()
    request_id = state.get("request_id") or str(uuid.uuid4())
    trace_id = state.get("trace_id") or str(uuid.uuid4())

    is_injection, reason = PromptInjectionScreen.check_query(query)
    if is_injection:
        return {
            "request_id": request_id,
            "trace_id": trace_id,
            "intent": "injection_attempt",
            "error_detail": reason,
        }

    return {
        "request_id": request_id,
        "trace_id": trace_id,
        "original_query": query,
    }
