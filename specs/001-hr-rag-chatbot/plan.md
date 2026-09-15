# Implementation Plan: HR Knowledge Assistant — Production-Grade RAG Chatbot

**Branch**: `001-hr-rag-chatbot` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-hr-rag-chatbot/spec.md`

---

## Summary

Build a production-grade, HR-domain-specific, multimodal RAG chatbot that allows
a user to upload HR-related documents (PDF, DOCX, XLSX, TXT, Markdown) and ask
natural-language questions through a modern streaming chat interface. The system
retrieves relevant content using hybrid dense+sparse retrieval with RRF fusion and
configurable cross-encoder reranking, orchestrates the full RAG pipeline with
LangGraph, generates grounded cited answers, and enforces HR-domain guardrails
including prompt-injection protection. Deployed locally via Docker Compose with
Kubernetes manifests and a Jenkins CI/CD pipeline.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)

**Primary Dependencies**:
- Backend: FastAPI, Pydantic v2, LangChain, LangGraph, SQLAlchemy (async),
  Alembic, asyncpg, pgvector, sentence-transformers (BGE Reranker v2 M3),
  cohere, langsmith, structlog, uvicorn
- Frontend: React 18, TypeScript, Vite, EventSource API (SSE streaming),
  react-markdown, highlight.js

**Storage**: PostgreSQL 15 + pgvector extension (Docker volume-persisted);
  uploaded source files on a Docker bind-mounted volume

**Testing**:
- Backend: pytest + pytest-asyncio, httpx (async test client), testcontainers-python
- Frontend: Vitest, React Testing Library
- E2E: pytest + httpx against full Docker Compose stack

**Target Platform**: Linux container (Docker Compose local); Kubernetes for production

**Performance Goals**:
- First streamed token: < 5 s end-to-end (≤ 100 documents, commodity hardware)
- Health endpoint: < 500 ms response
- Document indexing: ≥ 95% success rate on well-formed files
- Autocomplete suggestions: appear within 1 s of debounce trigger

**Constraints**:
- No blocking calls in the FastAPI async event loop
- No hardcoded secrets (all config via environment variables)
- Token budgets enforced for every LLM call
- MAX_RETRIEVAL_RETRIES hard-capped (config, default 2)
- BGE Reranker loaded once at startup; not per-request

**Scale/Scope**: Single-user local deployment; ≤ 100 HR documents; ≤ 10,000 chunks
  in initial version; architecture must support future multi-user extension

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Code Quality — separation of concerns | ✅ PASS | Architecture separates Frontend / API / LangGraph / Ingestion / Retrieval / Storage / Guardrails / Observability |
| I. Code Quality — provider abstractions | ✅ PASS | LLMProvider, EmbeddingProvider, Reranker, DocumentLoader, VectorStore are all abstracted interfaces |
| I. Code Quality — no hardcoded secrets | ✅ PASS | All config via .env; .env.example provided; .env in .gitignore |
| I. Code Quality — async backend | ✅ PASS | FastAPI + asyncpg + async LangGraph nodes; ingestion decoupled to background worker |
| II. Testing — unit + integration + E2E + guardrail | ✅ PASS | All test categories defined in spec FR + success criteria |
| II. Testing — RAG golden dataset evaluation | ✅ PASS | SC-010 mandates measurable Recall@10 improvement; evaluation pipeline planned |
| III. Groundedness — abstention + citation validation | ✅ PASS | FR-014, FR-015; LangGraph citation validation node |
| IV. UX — streaming mandatory | ✅ PASS | FR-019; SSE streaming; stop-generation action |
| IV. UX — all document states visible | ✅ PASS | FR-004 + FR-022; 7-state lifecycle displayed |
| V. Retrieval — hybrid by default | ✅ PASS | FR-010, FR-011; dense + sparse + RRF |
| V. Retrieval — reranking mandatory | ✅ PASS | FR-012; BGE + Cohere configurable |
| VI. Security — instruction separation | ✅ PASS | FR-026, FR-027; prompt architecture separates system/user/context |
| VII. Observability — structured logs + RAG run persistence | ✅ PASS | FR-031, FR-032; LangSmith optional |
| VIII. Performance — non-blocking ingestion | ✅ PASS | FR-003; background worker pattern |
| VIII. Performance — token budgets + retry limits | ✅ PASS | FR-017, FR-018 |

**Gate result: ALL PASS. Proceeding to Phase 0.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-hr-rag-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api-contract.md
│   └── streaming-contract.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
hr-rag-chatbot/
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Shared UI components
│   │   ├── features/
│   │   │   ├── chat/           # Chat interface, message list, input bar
│   │   │   ├── documents/      # Knowledge-base panel, upload, status
│   │   │   └── suggestions/    # Autocomplete, example questions
│   │   ├── hooks/              # Custom React hooks (useStream, useDocuments)
│   │   ├── services/           # API client, SSE client
│   │   ├── types/              # TypeScript interfaces
│   │   └── utils/
│   ├── public/
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config/
│   │   │   ├── settings.py     # Pydantic Settings (env-based)
│   │   │   └── logging.py      # structlog setup
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── chat.py
│   │   │       ├── documents.py
│   │   │       ├── conversations.py
│   │   │       ├── suggestions.py
│   │   │       └── health.py
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── chat_service.py
│   │   │   ├── document_service.py
│   │   │   ├── ingestion_service.py
│   │   │   └── suggestion_service.py
│   │   ├── workflows/
│   │   │   ├── rag_graph.py    # LangGraph compiled graph
│   │   │   ├── graph_state.py  # TypedDict RAG state
│   │   │   └── nodes/          # One file per graph node
│   │   ├── retrieval/
│   │   │   ├── retriever_factory.py
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── fusion.py       # RRF implementation
│   │   │   ├── reranker.py     # Reranker ABC + BGE + Cohere
│   │   │   └── context_selector.py
│   │   ├── ingestion/
│   │   │   ├── loaders/        # DocumentLoader per file type
│   │   │   ├── parsers/
│   │   │   ├── chunking/       # Structure-aware chunkers
│   │   │   ├── metadata.py
│   │   │   └── pipeline.py
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # DB access layer
│   │   ├── guardrails/         # Injection screening, output validation
│   │   ├── observability/      # Structured log helpers, trace context
│   │   ├── evaluation/         # Golden dataset runner
│   │   ├── mcp/                # MCP client + tool registry
│   │   └── utils/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── database/
│   ├── migrations/             # Alembic migration scripts
│   └── init/                   # pgvector init SQL
│
├── evaluation/
│   ├── datasets/               # HR golden dataset (JSON)
│   ├── scripts/                # Eval runner scripts
│   └── reports/
│
├── deployment/
│   ├── docker/
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.example.yaml
│   │   ├── postgres.yaml
│   │   ├── backend.yaml
│   │   ├── frontend.yaml
│   │   ├── services.yaml
│   │   ├── ingress.yaml
│   │   └── pvc.yaml
│   └── jenkins/
│       └── Jenkinsfile
│
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

**Structure Decision**: Web application layout (Option 2) with separate `frontend/`
and `backend/` packages. Additional top-level directories for `database/`,
`evaluation/`, and `deployment/` match the spec's repository structure requirements.

