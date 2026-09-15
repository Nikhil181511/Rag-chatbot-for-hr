import re
from typing import Dict, Any
from app.workflows.graph_state import RAGState

GREETING_PATTERNS = [
    r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|howdy|what'?s\s+up)\b",
    r"^who\s+are\s+you\??$",
    r"^what\s+can\s+you\s+do\??$",
]

OUT_OF_DOMAIN_PATTERNS = [
    r"\b(python\s+script|write\s+code|stock\s+price|recipe|movie|weather\s+in|solve\s+math|write\s+a\s+poem|crypto)\b",
]


async def classify_intent_node(state: RAGState) -> Dict[str, Any]:
    if state.get("intent") == "injection_attempt":
        return {"intent": "injection_attempt"}

    query = state.get("original_query", "").lower().strip()

    # Check greeting
    for pat in GREETING_PATTERNS:
        if re.search(pat, query, re.IGNORECASE):
            return {
                "intent": "greeting",
                "draft_answer": "Hello! I am your HR Knowledge Assistant. I can help answer questions regarding company policies, leave entitlements, benefits, onboarding, remote work guidelines, and more. How can I help you today?",
                "final_answer": "Hello! I am your HR Knowledge Assistant. I can help answer questions regarding company policies, leave entitlements, benefits, onboarding, remote work guidelines, and more. How can I help you today?",
                "final_answer_status": "SUCCESS",
            }

    # Check out of domain
    for pat in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pat, query, re.IGNORECASE):
            return {
                "intent": "out_of_domain",
                "draft_answer": "I am an HR Knowledge Assistant specialized exclusively in company HR policies, benefits, and workplace guidelines. I cannot assist with non-HR topics.",
                "final_answer": "I am an HR Knowledge Assistant specialized exclusively in company HR policies, benefits, and workplace guidelines. I cannot assist with non-HR topics.",
                "final_answer_status": "SUCCESS",
            }

    return {"intent": "hr_question"}
