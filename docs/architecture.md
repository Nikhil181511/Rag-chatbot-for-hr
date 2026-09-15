# System Architecture: HR Knowledge Assistant RAG

## High-Level Architecture Overview

```mermaid
graph TD
    User([Employee / HR Admin]) -->|Browser / React UI| Frontend[React 18 + Vite Frontend]
    Frontend -->|SSE / REST API| Backend[FastAPI Backend Application]
    
    subgraph Ingestion Pipeline
        Uploads[(Document Files)] --> Loader[Loader Factory: PDF, DOCX, XLSX, TXT]
        Loader --> Chunker[Policy & Spreadsheet Chunkers]
        Chunker --> Enricher[HR Metadata Enricher]
        Enricher --> Embedder[Batch Vector Embeddings]
        Embedder --> PGVector[(PostgreSQL 15 + pgvector)]
    end

    subgraph LangGraph RAG Workflow
        Backend --> Validate[1. Validate Request & Injection Screen]
        Validate --> History[2. Load Conversation Context]
        History --> Intent[3. Classify Intent & Domain]
        Intent --> Retrieve[4. Hybrid Retrieve: Dense + Sparse]
        Retrieve --> Fusion[5. Reciprocal Rank Fusion - RRF]
        Fusion --> Rerank[6. BGE / Cohere Reranker]
        Rerank --> Context[7. Context Selector & Token Budget]
        Context --> Generate[8. LLM Answer Generation]
        Generate --> Citations[9. Citations Extractor & Validator]
        Citations --> Groundedness[10. Groundedness & Hallucination Check]
        Groundedness --> Guardrails[11. Salary Redaction & PII Safety]
        Guardrails --> Final[12. Format Final SSE Stream]
    end

    PGVector <--> Retrieve
```

## Hybrid Retrieval & RRF Fusion

1. **Dense Vector Search**: Computes cosine distance using pgvector HNSW index (`ef_construction=128, m=16`).
2. **Sparse Full-Text Search**: Uses PostgreSQL `tsvector` generated column with English dictionary and GIN index with `ts_rank_cd`.
3. **Reciprocal Rank Fusion**: Merges both candidate lists using standard $k=60$ constant:
   $$RRF\_Score(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{60 + rank_m(d)}$$
4. **Cross-Encoder Reranker**: Rescores top candidates with `BAAI/bge-reranker-v2-m3` or `Cohere Rerank v3.5`.
