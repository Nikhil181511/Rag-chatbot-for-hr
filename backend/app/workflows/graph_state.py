import uuid
from typing import TypedDict, Optional, List, Dict, Any


class RAGState(TypedDict, total=False):
    # Identifiers & Context
    conversation_id: Optional[uuid.UUID]
    request_id: str
    trace_id: str
    
    # Query & Conversation History
    original_query: str
    conversation_history: List[Dict[str, str]]
    
    # Intent & Routing
    intent: Optional[str]  # "hr_question" | "greeting" | "out_of_domain" | "injection_attempt"
    domain: Optional[str]  # "leave" | "benefits" | "onboarding" | "wfh" | "general"
    rewritten_queries: List[str]
    filters: Dict[str, Any]
    
    # Retrieval Pipeline State
    retrieved_candidates: List[Dict[str, Any]]
    fused_candidates: List[Dict[str, Any]]
    reranked_candidates: List[Dict[str, Any]]
    selected_context: List[Dict[str, Any]]
    retrieval_quality: str  # "sufficient" | "insufficient" | "empty"
    _raw_dense: List[Any]
    _raw_sparse: List[Any]
    _raw_reranked: List[Any]
    
    # Generation & Evaluation State
    draft_answer: str
    citations: List[Dict[str, Any]]
    groundedness_result: str  # "grounded" | "hallucination" | "abstention"
    guardrail_result: str     # "passed" | "redacted" | "blocked"
    retry_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    node_durations: Dict[str, float]
    
    # Final Output
    final_answer: str
    final_answer_status: str  # "SUCCESS" | "ABSTENTION" | "ERROR" | "GUARDRAIL_BLOCKED"
    error_detail: Optional[str]
