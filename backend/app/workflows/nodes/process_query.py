from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.ingestion.metadata import MetadataEnricher


async def process_query_node(state: RAGState) -> Dict[str, Any]:
    query = state.get("original_query", "")
    metadata = MetadataEnricher.enrich_document(title="", content=query)
    
    filters: Dict[str, Any] = {}
    if metadata.get("document_category"):
        filters["document_category"] = metadata["document_category"]

    return {
        "rewritten_queries": [query],
        "domain": metadata.get("document_category") or "general",
        "filters": filters,
    }
