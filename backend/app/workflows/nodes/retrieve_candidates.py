from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.config.database import async_session_factory
from app.retrieval.hybrid_retriever import HybridRetriever


async def retrieve_candidates_node(state: RAGState) -> Dict[str, Any]:
    query = state.get("original_query", "")
    filters = state.get("filters", {})

    async with async_session_factory() as session:
        retriever = HybridRetriever(session)
        results = await retriever.retrieve(query=query, filters=filters)

    return {
        "retrieved_candidates": [
            {
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id),
                "document_name": c.document_name,
                "content": c.content,
                "score": c.score,
                "page_number": c.page_number,
                "section": c.section,
                "sheet_name": c.sheet_name,
                "row_start": c.row_start,
                "row_end": c.row_end,
                "source": c.source,
                "metadata": c.metadata,
            }
            for c in (results.get("dense", []) + results.get("sparse", []))
        ],
        "_raw_dense": results.get("dense", []),
        "_raw_sparse": results.get("sparse", []),
    }
