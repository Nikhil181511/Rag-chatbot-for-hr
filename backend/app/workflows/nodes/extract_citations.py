from typing import Dict, Any, List
from app.workflows.graph_state import RAGState


async def extract_citations_node(state: RAGState) -> Dict[str, Any]:
    selected_context = state.get("selected_context", [])
    citations: List[Dict[str, Any]] = []

    for chunk in selected_context:
        citations.append({
            "document_id": chunk["document_id"],
            "chunk_id": chunk["chunk_id"],
            "document_name": chunk["document_name"],
            "page_number": chunk.get("page_number"),
            "section": chunk.get("section"),
            "sheet_name": chunk.get("sheet_name"),
            "row_start": chunk.get("row_start"),
            "row_end": chunk.get("row_end"),
            "excerpt": chunk.get("excerpt", chunk["content"][:200]),
        })

    return {"citations": citations}
