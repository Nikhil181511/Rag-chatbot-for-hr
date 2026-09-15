from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.guardrails.salary_redaction import SensitiveDataRedactor


async def apply_guardrails_node(state: RAGState) -> Dict[str, Any]:
    draft_answer = state.get("draft_answer", "")
    sanitized_answer, was_redacted = SensitiveDataRedactor.redact(draft_answer)

    return {
        "draft_answer": sanitized_answer,
        "guardrail_result": "redacted" if was_redacted else "passed",
    }
