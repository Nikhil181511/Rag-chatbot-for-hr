from typing import Literal
from langgraph.graph import StateGraph, END
from app.workflows.graph_state import RAGState
from app.workflows.nodes.validate_request import validate_request_node
from app.workflows.nodes.load_conversation_context import load_conversation_context_node
from app.workflows.nodes.classify_intent import classify_intent_node
from app.workflows.nodes.process_query import process_query_node
from app.workflows.nodes.retrieve_candidates import retrieve_candidates_node
from app.workflows.nodes.fuse_and_rerank import fuse_and_rerank_node
from app.workflows.nodes.select_context import select_context_node
from app.workflows.nodes.generate_draft_answer import generate_draft_answer_node
from app.workflows.nodes.extract_citations import extract_citations_node
from app.workflows.nodes.validate_groundedness import validate_groundedness_node
from app.workflows.nodes.apply_guardrails import apply_guardrails_node
from app.workflows.nodes.handle_abstention import handle_abstention_node
from app.workflows.nodes.format_final_response import format_final_response_node


def route_after_intent(
    state: RAGState,
) -> Literal["process_query", "handle_abstention", "format_final_response"]:
    intent = state.get("intent", "hr_question")
    if intent in ("greeting", "out_of_domain"):
        return "format_final_response"
    elif intent == "injection_attempt":
        return "handle_abstention"
    return "process_query"


def route_after_selection(
    state: RAGState,
) -> Literal["generate_draft_answer", "handle_abstention"]:
    quality = state.get("retrieval_quality", "sufficient")
    if quality in ("empty", "insufficient"):
        return "handle_abstention"
    return "generate_draft_answer"


def route_after_groundedness(
    state: RAGState,
) -> Literal["apply_guardrails", "handle_abstention"]:
    groundedness = state.get("groundedness_result", "grounded")
    if groundedness == "hallucination":
        return "handle_abstention"
    return "apply_guardrails"


def create_rag_graph() -> StateGraph:
    builder = StateGraph(RAGState)

    # 13 LangGraph Nodes
    builder.add_node("validate_request", validate_request_node)
    builder.add_node("load_conversation_context", load_conversation_context_node)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("process_query", process_query_node)
    builder.add_node("retrieve_candidates", retrieve_candidates_node)
    builder.add_node("fuse_and_rerank", fuse_and_rerank_node)
    builder.add_node("select_context", select_context_node)
    builder.add_node("generate_draft_answer", generate_draft_answer_node)
    builder.add_node("extract_citations", extract_citations_node)
    builder.add_node("validate_groundedness", validate_groundedness_node)
    builder.add_node("apply_guardrails", apply_guardrails_node)
    builder.add_node("handle_abstention", handle_abstention_node)
    builder.add_node("format_final_response", format_final_response_node)

    # Wire Edges
    builder.set_entry_point("validate_request")
    builder.add_edge("validate_request", "load_conversation_context")
    builder.add_edge("load_conversation_context", "classify_intent")

    # Intent routing
    builder.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "process_query": "process_query",
            "format_final_response": "format_final_response",
            "handle_abstention": "handle_abstention",
        },
    )

    builder.add_edge("process_query", "retrieve_candidates")
    builder.add_edge("retrieve_candidates", "fuse_and_rerank")
    builder.add_edge("fuse_and_rerank", "select_context")

    # Context selection routing
    builder.add_conditional_edges(
        "select_context",
        route_after_selection,
        {
            "generate_draft_answer": "generate_draft_answer",
            "handle_abstention": "handle_abstention",
        },
    )

    builder.add_edge("generate_draft_answer", "extract_citations")
    builder.add_edge("extract_citations", "validate_groundedness")

    # Groundedness routing
    builder.add_conditional_edges(
        "validate_groundedness",
        route_after_groundedness,
        {
            "apply_guardrails": "apply_guardrails",
            "handle_abstention": "handle_abstention",
        },
    )

    builder.add_edge("apply_guardrails", "format_final_response")
    builder.add_edge("handle_abstention", END)
    builder.add_edge("format_final_response", END)

    return builder


rag_graph = create_rag_graph()
rag_app = rag_graph.compile()
