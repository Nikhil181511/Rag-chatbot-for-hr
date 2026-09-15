from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.config.settings import settings


async def load_conversation_context_node(state: RAGState) -> Dict[str, Any]:
    history = state.get("conversation_history", [])
    # Limit to MAX_HISTORY_MESSAGES
    truncated_history = history[-settings.MAX_HISTORY_MESSAGES :] if history else []
    return {"conversation_history": truncated_history}
