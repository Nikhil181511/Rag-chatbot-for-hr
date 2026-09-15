# Research: HR Knowledge Assistant — RAG Chatbot

**Phase 0 output for**: `specs/001-hr-rag-chatbot/plan.md`
**Date**: 2026-09-15

---

## 1. RAG Orchestration Framework

**Decision**: LangGraph (required by spec)

**Rationale**: LangGraph provides typed, stateful, conditional graph-based orchestration
ideal for controlled RAG workflows. It supports explicit node definitions, conditional
routing (intent → retrieval → reranking → generation → guardrails), retry limits, and
streaming. Unlike plain LangChain chains, LangGraph makes control flow explicit and
testable. LangSmith integration is native for tracing.

**Alternatives considered**:
- Plain LangChain LCEL chains: less control over state, harder to enforce retry limits
- Custom orchestration: more flexible but far more code to maintain

---

## 2. Hybrid Retrieval Architecture

**Decision**: pgvector (HNSW index) for dense + PostgreSQL tsvector/tsquery for sparse;
fused with Reciprocal Rank Fusion (RRF, k=60)

**Rationale**:
- pgvector with HNSW index provides fast approximate nearest-neighbour search suitable
  for ≤10,000 chunks on local hardware. HNSW is preferred over IVFFlat at this scale
  because it avoids the training/cluster-size tuning step.
- PostgreSQL full-text search (tsvector + GIN index) handles exact HR terminology
  (leave types, policy names, acronyms, notice periods) that semantic search may miss.
- Using a single PostgreSQL instance for both dense and sparse search avoids the
  operational complexity of a separate search engine.
- RRF formula: score(d) = Σ [1 / (k + rank_r(d))], k=60 (standard default). RRF is
  rank-based, not score-based, so it is robust to different scale ranges between dense
  and sparse scores.

**Alternatives considered**:
- Elasticsearch: better sparse retrieval but adds significant operational overhead for
  a local-first single-user deployment
- Dedicated vector DB (Weaviate, Qdrant): unnecessary operational complexity when
  pgvector meets the scale requirements

---

## 3. Reranking

**Decision**: Pluggable via `Reranker` abstract base class; two concrete implementations:
- **BGEReranker**: BAAI/bge-reranker-v2-m3 via sentence-transformers; local CPU/CUDA inference
- **CohereReranker**: Cohere Rerank API via cohere SDK; selected by RERANKER_PROVIDER env var

**Rationale**:
- BGE Reranker v2 M3 supports multilingual cross-encoding and achieves strong performance
  on diverse HR text without API costs. It must be loaded at startup (singleton) to avoid
  per-request model loading latency (~10-30 s).
- Cohere Rerank is an API-based fallback that requires no local GPU. It adds cost but
  eliminates hardware constraints.
- The abstraction allows benchmarking both options against the HR golden dataset (SC-010).

**Benchmarking plan**: Run evaluation pipeline with three configurations:
1. No reranker (baseline)
2. BGE Reranker v2 M3
3. Cohere Rerank
Measure Recall@10, MRR, NDCG@10, answer faithfulness, and end-to-end latency.

---

## 4. Document Chunking Strategy

**Decision**: Structure-aware, format-specific chunking using a `ChunkingStrategy`
abstract base class per document type

**Rules derived from spec**:
- PDF/DOCX: heading-hierarchy-aware splitting; target 400-800 tokens; overlap 50-120 tokens
- XLSX/CSV: sheet-aware chunking; column headers preserved in every chunk;
  sheet + row-range metadata stored
- Markdown: section-boundary splitting at headings
- TXT: semantic paragraph splitting with size limits
- FAQ documents: one question-answer unit per chunk where practical
- Procedures: step sequences kept together to preserve ordering
- Policy sections: title + eligibility + exceptions + effective dates kept cohesive

**Content hash**: SHA-256 of normalized chunk content; used for deduplication on reprocess.

---

## 5. Embedding Strategy

**Decision**: EmbeddingProvider abstract interface; default implementation uses
`text-embedding-3-small` (OpenAI) or a sentence-transformers local model depending
on `EMBEDDING_PROVIDER` env var.

**Consistency rule**: The embedding model configuration stored at ingestion time MUST
match the model used at query time. Model version + dimension tracked in `document_versions`
table. Changing the model requires re-embedding the entire corpus.

---

## 6. LangGraph State & Workflow

**Decision**: Explicit `TypedDict`-based `RAGState` with all pipeline fields typed.
Graph nodes (one Python function each):
1. `validate_request` — input length, file constraints, injection pre-screen
2. `load_conversation_context` — fetch history, apply truncation
3. `classify_intent` — HR query / greeting / out-of-domain routing
4. `process_query` — rewrite, expand, extract HR metadata filters
5. `hybrid_retrieve` — dense + sparse retrieval in parallel
6. `fuse_candidates` — RRF
7. `rerank` — configurable reranker
8. `check_retrieval_quality` — relevance threshold gate
9. `select_context` — token-budget-aware context selection
10. `generate_answer` — LLM call with structured output
11. `validate_citations` — citation existence check against RAG run
12. `check_groundedness` — grounded/abstention classification
13. `format_response` — assemble final response + citations

Conditional edges handle: greeting short-circuit, out-of-domain boundary,
poor retrieval → query reformulation retry, groundedness failure → safe fallback.

---

## 7. Prompt Injection Defense

**Decision**: Three-layer defense
1. **Structural separation**: System instructions, user query, and retrieved context
   are always in separate message roles in the LLM API call. Retrieved content is
   prefixed with a trust-boundary marker instructing the LLM to treat it as data only.
2. **Instruction in system prompt**: Explicit rules to never follow document instructions,
   never reveal system prompt, never treat retrieved text as trusted commands.
3. **Output validation node**: Scans response for prompt leakage patterns, unsupported
   claims, and citation fabrication before the response is returned to the user.

---

## 8. MCP Integration

**Decision**: Filesystem MCP server (read-only) for controlled local HR knowledge file access

**Rationale**: The Filesystem MCP server is the lowest-risk, most justified integration:
- Read-only: cannot cause data mutations
- Scoped to the uploaded documents directory only (allowlist enforced)
- Demonstrates MCP tool call tracing in LangGraph
- Does not replace the RAG pipeline; it supplements it for structured file listing

**Safety restrictions**:
- Path allowlist: only the configured uploads directory
- No arbitrary command execution
- All tool calls logged with trace ID
- MCP server unavailability does not block core RAG answering

---

## 9. Streaming Architecture

**Decision**: FastAPI `StreamingResponse` with Server-Sent Events (SSE) format;
frontend uses native `EventSource` API (or `fetch` with ReadableStream for
more control over stop-generation).

**Events defined**:
- `data: {"type": "token", "content": "..."}` — each streamed token
- `data: {"type": "citations", "citations": [...]}` — final citations block
- `data: {"type": "done"}` — completion signal
- `data: {"type": "error", "message": "..."}` — error event

**Stop generation**: Frontend sends a separate `DELETE /api/v1/chat/stream/{request_id}`
request; backend sets a cancellation flag on the in-flight request.

---

## 10. Database Schema Decisions

**Decision**: PostgreSQL 15 + pgvector. Key schema choices:
- `document_chunks.embedding` uses `vector(1536)` dimension (adjustable via config)
- HNSW index on `embedding` column: `ef_construction=128, m=16` (tunable)
- GIN index on `tsvector` column for full-text search
- `document_versions.is_current` flag for current-version filtering
- `rag_runs` table stores full trace JSON in a JSONB column
- All sensitive fields (content, query) stored only where operationally necessary

---

## 11. CI/CD Pipeline

**Decision**: Jenkins Declarative Pipeline (Jenkinsfile)

**Stages**:
1. Checkout
2. Install dependencies (backend: pip install; frontend: npm ci)
3. Lint (ruff + ESLint)
4. Type check (mypy + tsc --noEmit)
5. Unit tests (pytest + vitest)
6. Integration tests (pytest against testcontainers PostgreSQL)
7. Build Docker images (backend + frontend)
8. Security scan (optional: trivy image scan)
9. Push images to registry (conditional on main branch)
10. Deploy to Kubernetes (conditional on main branch)
11. Smoke tests

**Secrets management**: Jenkins credentials store; no secrets in Jenkinsfile.

---

## 12. Evaluation Framework

**Decision**: Custom Python evaluation runner using the HR golden dataset (50-100 cases)

**Metrics computed**:
- Retrieval: Recall@K, Precision@K, MRR, NDCG@K
- Generation: faithfulness score (LLM-as-judge with caution), citation correctness,
  citation completeness, abstention rate on no-evidence cases
- Comparison: baseline (dense only) vs. hybrid vs. hybrid+reranker variants

**Trigger**: Evaluation MUST run on any change to chunking, embeddings, retriever,
reranker, prompts, LLM config, context selection, or guardrail logic.
