# HR Knowledge Assistant — RAG System

Enterprise-grade HR Knowledge Assistant chatbot powered by Hybrid Retrieval-Augmented Generation (RAG).

## Features
- **Multi-format Ingestion**: PDF, DOCX, XLSX, TXT, MD, CSV with table & structure preservation.
- **Hybrid Retrieval**: Dense pgvector + Sparse tsvector + Reciprocal Rank Fusion (RRF) + BGE/Cohere Reranker.
- **LangGraph RAG Pipeline**: Structured state machine with intent classification, hallucination checks, and citations.
- **HR Guardrails**: Anti-prompt injection, salary redaction, domain enforcement.
- **Modern Streaming UI**: React 18 + Vite + SSE streaming + interactive citation viewer.
