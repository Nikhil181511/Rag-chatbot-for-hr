# Tasks: HR Knowledge Assistant — Production-Grade RAG Chatbot

**Branch**: `001-hr-rag-chatbot` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Generated**: 2026-09-15

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository scaffolding, tooling, Docker services, and environment configuration.
All Phase 1 tasks can begin immediately. Parallelizable tasks are marked `[P]`.

- [X] T001 Create full repository directory structure per `plan.md` (frontend/, backend/, database/, evaluation/, deployment/, docs/)
- [X] T002 Initialise React 18 + TypeScript + Vite frontend project in `frontend/` with `npm create vite@latest`
- [X] T003 Initialise Python 3.12 backend project in `backend/` with `pyproject.toml` (FastAPI, Pydantic v2, LangChain, LangGraph, SQLAlchemy async, asyncpg, pgvector, structlog, uvicorn, alembic, sentence-transformers, cohere, langsmith)
- [X] T004 [P] Create `backend/Dockerfile` — multi-stage build: deps layer + app layer; ASGI entrypoint via uvicorn
- [X] T005 [P] Create `frontend/Dockerfile` — build stage (npm ci + vite build) + nginx serve stage
- [X] T006 Create `docker-compose.yml` with services: postgres (pgvector image, health check, persistent volume), backend (depends_on postgres healthy), frontend; env vars from `.env`
- [X] T007 [P] Create `.env.example` with all required keys: APP_ENV, LOG_LEVEL, POSTGRES_*, LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, EMBEDDING_PROVIDER, EMBEDDING_MODEL, RERANKER_PROVIDER, COHERE_API_KEY, VECTOR_STORE, DENSE_TOP_K, SPARSE_TOP_K, FUSION_TOP_K, RERANK_TOP_K, FINAL_CONTEXT_CHUNKS, MAX_RETRIEVAL_RETRIES, MAX_HISTORY_MESSAGES, MAX_FILE_SIZE_MB, LANGSMITH_TRACING, LANGSMITH_API_KEY, LANGSMITH_PROJECT, MCP_ENABLED
- [X] T008 [P] Create `backend/app/config/settings.py` — Pydantic BaseSettings class loading all env vars with typed fields and validation
- [X] T009 [P] Create `backend/app/config/logging.py` — structlog configuration with JSON processor, request_id and trace_id context vars
- [X] T010 [P] Configure backend linting and type checking: ruff, mypy (strict) in `pyproject.toml`
- [X] T011 [P] Configure frontend linting: ESLint + TypeScript strict mode in `frontend/tsconfig.json` and `.eslintrc`
- [X] T012 Create `database/init/01-init.sql` — enable pgvector extension (CREATE EXTENSION IF NOT EXISTS vector)
- [X] T013 Initialise Alembic in `database/migrations/` with async PostgreSQL driver; create initial empty migration
- [X] T014 [P] Create `backend/tests/` directory structure: unit/, integration/, e2e/; add conftest.py with testcontainers PostgreSQL fixture
- [X] T015 [P] Create `evaluation/datasets/hr-golden-v1.json` — seed with 10 representative HR question-answer pairs covering leave, onboarding, WFH, abstention, and out-of-domain categories
- [X] T016 Create `docs/setup.md` with Docker Compose local development instructions and `.env` configuration guide

**Checkpoint**: docker compose up --build starts all services healthy; backend serves 404 on /; postgres reachable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story work begins.

### Database Schema & Migrations

- [X] T017 Create Alembic migration for `documents` table (id UUID PK, file_name VARCHAR(512), file_type VARCHAR(32), file_size BIGINT, content_hash VARCHAR(64) UNIQUE, status VARCHAR(32) DEFAULT PENDING with CHECK constraint, title VARCHAR(512), document_category VARCHAR(128), storage_path VARCHAR(1024), error_message TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ)
- [X] T018 Create Alembic migration for `document_versions` table (id, document_id FK, version, content_hash, parser_version, embedding_model, embedding_dim, index_version, effective_date, expiry_date, is_current BOOLEAN, created_at) + partial unique index WHERE is_current = TRUE
- [X] T019 Create Alembic migration for `document_chunks` table (id, document_version_id FK, chunk_index, content, content_hash, token_count, page_number, section VARCHAR(512), parent_section VARCHAR(512), sheet_name, row_start, row_end, is_ocr, metadata JSONB, embedding vector(1536), tsvector_content TSVECTOR GENERATED ALWAYS AS STORED) + HNSW index on embedding (ef_construction=128, m=16) + GIN index on tsvector_content
- [X] T020 Create Alembic migration for `conversations` table (id UUID PK, title VARCHAR(512), message_count INTEGER DEFAULT 0, created_at, updated_at)
- [X] T021 Create Alembic migration for `messages` table (id, conversation_id FK, role VARCHAR(16) CHECK IN ('user','assistant'), content TEXT, rag_run_id UUID nullable FK, created_at)
- [X] T022 Create Alembic migration for `rag_runs` table with all columns per data-model.md: id, conversation_id FK, request_id VARCHAR(64) UNIQUE, trace_id, query, rewritten_queries JSONB, intent, domain, retrieval_mode, reranker, retrieved_chunk_ids UUID[], selected_chunk_ids UUID[], retrieval_scores JSONB, context_token_count, llm_model, input_token_count, output_token_count, generation_latency_ms, total_latency_ms, citation_validation_result, groundedness_result, guardrail_result, retry_count, final_answer_status, error_detail, created_at
- [X] T023 Create Alembic migration for `evaluation_datasets`, `evaluation_cases`, `evaluation_results` tables per data-model.md

### SQLAlchemy ORM Models

- [X] T024 [P] Create `backend/app/models/document.py` — ORM models for documents + document_versions with status Python Enum and relationship
- [X] T025 [P] Create `backend/app/models/chunk.py` — ORM model for document_chunks with pgvector Vector column (dim 1536) and tsvector column
- [X] T026 [P] Create `backend/app/models/conversation.py` — ORM models for conversations + messages with relationship
- [X] T027 [P] Create `backend/app/models/rag_run.py` — ORM model for rag_runs
- [X] T028 [P] Create `backend/app/models/evaluation.py` — ORM models for evaluation tables

### Repository Layer

- [X] T029 [P] Create `backend/app/repositories/document_repository.py` — async CRUD; get_by_content_hash() for dedup; set_current_version() with transaction safety
- [X] T030 [P] Create `backend/app/repositories/chunk_repository.py` — bulk insert; delete_by_document_version_id(); dense search (embedding <-> $1 ORDER BY LIMIT k); sparse search (tsvector @@ plainto_tsquery)
- [X] T031 [P] Create `backend/app/repositories/conversation_repository.py` — async CRUD; get_messages_window(conversation_id, limit=MAX_HISTORY_MESSAGES)
- [X] T032 [P] Create `backend/app/repositories/rag_run_repository.py` — async insert and get for rag_runs

### FastAPI Application Shell

- [X] T033 Create `backend/app/main.py` — FastAPI app factory: register routers, CORS, request-ID middleware, exception handlers (never expose stack traces)
- [X] T034 Create `backend/app/api/v1/health.py` — GET /health (liveness) and GET /ready (DB + vector index) endpoints; responses within 500ms
- [X] T035 [P] Create `backend/app/schemas/` — Pydantic v2 request/response models for all endpoints per contracts/api-contract.md: DocumentUploadResponse, ChatRequest, ChatResponse, Citation, ConversationListResponse, SuggestionResponse, KnowledgeBaseStats

### LangGraph State & Graph Shell

- [X] T036 Create `backend/app/workflows/graph_state.py` — RAGState TypedDict with all fields per data-model.md: conversation_id, request_id, trace_id, original_query, conversation_history, intent, domain, rewritten_queries, filters, retrieved_candidates, fused_candidates, reranked_candidates, selected_context, retrieval_quality, draft_answer, citations, groundedness_result, guardrail_result, retry_count, final_answer, final_answer_status, error_detail
- [X] T037 Create `backend/app/workflows/rag_graph.py` — compile LangGraph StateGraph with all 13 node stubs; wire conditional edges for intent routing, retrieval quality check, groundedness check; compile and export rag_app

**Checkpoint**: GET /health 200; GET /ready 200; all migrations applied; LangGraph graph compiles.

---

## Phase 3: User Story 1 — Upload HR Documents and Ask Questions (Priority: P1) — MVP

**Goal**: User uploads HR PDF and receives grounded, cited, streamed answer.
**Independent Test**: Upload leave-policy.pdf -> READY -> ask "What is the annual leave entitlement?" -> veri### Document Ingestion Pipeline

- [X] T038 [US1] Create `backend/app/ingestion/loaders/base.py` — DocumentLoader ABC: load(file_path) -> NormalizedDocument; define NormalizedDocument dataclass with document_id, source_file_name, source_type, title, content, sections, tables, page_references, metadata
- [X] T039 [P] [US1] Create `backend/app/ingestion/loaders/pdf_loader.py` — PDFLoader: extract text with page numbers via pdfplumber; detect/remove repeated headers/footers; preserve headings and tables; set is_ocr=False; OCR fallback marker
- [X] T040 [P] [US1] Create `backend/app/ingestion/loaders/docx_loader.py` — DOCXLoader: extract headings, paragraphs, lists, tables via python-docx
- [X] T041 [P] [US1] Create `backend/app/ingestion/loaders/text_loader.py` — TextLoader: plain text and Markdown ingestion; preserve structure
- [X] T042 [P] [US1] Create `backend/app/ingestion/loaders/excel_loader.py` — ExcelLoader: XLSX/CSV via openpyxl/pandas; preserve sheet names and column headers; normalize rows as "Header: Value" text; handle merged cells gracefully (skip and log)
- [X] T043 [US1] Create `backend/app/ingestion/loaders/loader_factory.py` — registry mapping file extensions to loader classes; raise UnsupportedFileTypeError for unknown extensions
- [X] T044 [US1] Create `backend/app/ingestion/chunking/base.py` — ChunkingStrategy ABC: chunk(normalized_doc) -> List[Chunk]; Chunk dataclass with all metadata fields per data-model.md
- [X] T045 [US1] Create `backend/app/ingestion/chunking/policy_chunker.py` — structure-aware chunker for PDF/DOCX: split at headings, target 400-800 tokens (tiktoken), overlap 50-120 tokens; keep policy title with section body; keep eligibility/exceptions together; keep FAQ as Q+A unit; keep procedure steps ordered
- [X] T046 [US1] Create `backend/app/ingestion/chunking/spreadsheet_chunker.py` — sheet-aware chunker for XLSX/CSV: column headers in every chunk; group related rows; store sheet_name, row_start, row_end; target <=800 tokens per chunk
- [X] T047 [US1] Create `backend/app/ingestion/chunking/chunker_factory.py` — map document source_type to correct ChunkingStrategy
- [X] T048 [US1] Create `backend/app/ingestion/metadata.py` — MetadataEnricher: extract HR metadata from chunk content (document_category, policy_type, effective_date, region) via regex/heuristics; null if not detected; never invent values
- [X] T049 [US1] Create `backend/app/ingestion/pipeline.py` — IngestionPipeline.run(document_id): validate -> load -> clean -> chunk -> enrich metadata -> embed in batch -> bulk insert chunks -> create document_version -> update status READY; update status FAILED with error_message on any error; no duplicate chunks via content_hash
- [X] T050 [US1] Implement IngestionPipeline.validate_file(): check allowed MIME type against allowlist (pdf, docx, txt, md, csv, xlsx); enforce MAX_FILE_SIZE_MB; raise InvalidFileError on fail

### Embedding & Reranker Providers

- [X] T051 [US1] Create `backend/app/retrieval/embedding_provider.py` — EmbeddingProvider ABC: embed_texts(List[str]) -> List[List[float]]; embed_query(str) -> List[float]
- [X] T052 [US1] Create `backend/app/retrieval/openai_embedding_provider.py` — OpenAIEmbeddingProvider: batch embed via openai SDK; read model and API key from settings; track dimension
- [X] T053 [US1] Create `backend/app/retrieval/embedding_factory.py` — singleton EmbeddingProvider from EMBEDDING_PROVIDER env var
- [X] T054 [US1] Create `backend/app/retrieval/reranker.py` — Reranker ABC: rerank(query, candidates, top_k) -> List[ChunkCandidate]
- [X] T055 [P] [US1] Create `backend/app/retrieval/bge_reranker.py` — BGEReranker: load BAAI/bge-reranker-v2-m3 at startup (singleton); batch scoring; CPU/CUDA via device config; handle model load failure gracefully
- [X] T056 [P] [US1] Create `backend/app/retrieval/cohere_reranker.py` — CohereReranker: API-based via cohere SDK; timeout handling; rate-limit retry with backoff; track latency
- [X] T057 [US1] Create `backend/app/retrieval/reranker_factory.py` — singleton Reranker from RERANKER_PROVIDER; return NoOpReranker when provider is "none"

### Hybrid Retrieval & RRF

- [X] T058 [US1] Create `backend/app/retrieval/hybrid_retriever.py` — HybridRetriever.retrieve(query, filters, dense_top_k, sparse_top_k): run dense and sparse search concurrently via asyncio.gather; return merged candidates with source annotation
- [X] T059 [US1] Create `backend/app/retrieval/fusion.py` — reciprocal_rank_fusion(dense, sparse, k=60, top_k=FUSION_TOP_K): deduplicate by chunk_id; compute RRF score (1/(k+rank)); sort descending; preserve metadata
- [X] T060 [US1] Create `backend/app/retrieval/context_selector.py` — ContextSelector.select(candidates, token_budget): remove duplicates; apply relevance threshold; enforce FINAL_CONTEXT_CHUNKS limit and token budget; return selected chunks with citation metadata

### LangGraph Nodes (US1 Core Path)

- [X] T061 [US1] Implement `backend/app/workflows/nodes/validate_request.py` — check query not empty, not exceeding MAX_INPUT_LENGTH; injection pre-screen; set request_id and trace_id in state
- [X] T062 [US1] Implement `backend/app/workflows/nodes/load_conversation_context.py` — fetch messages up to MAX_HISTORY_MESSAGES; truncate oldest if over limit; store in state
- [X] T063 [US1] Implement `backend/app/workflows/nodes/classify_intent.py` — classify as hr_question | greeting | out_of_domain; set domain; route via conditional edge
- [X] T064 [US1] Implement `backend/app/workflows/nodes/process_query.py` — normalize; extract HR metadata filters (leave type, region, employee category, date); optional rewrite; always preserve original_query
- [X] T065 [US1] Implement `backend/app/workflows/nodes/hybrid_retrieve.py` — call HybridRetriever with query and filters; store retrieved_candidates
- [X] T066 [US1] Implement `backend/app/workflows/nodes/fuse_candidates.py` — call RRF fusion; store fused_candidates
- [X] T067 [US1] Implement `backend/app/workflows/nodes/rerank.py` — call configured Reranker; store reranked_candidates; track latency
- [X] T068 [US1] Implement `backend/app/workflows/nodes/check_retrieval_quality.py` — if candidates empty or top score below threshold: retrieval_quality=poor; route to reformulation if retry_count < MAX_RETRIEVAL_RETRIES else route to abstention
- [X] T069 [US1] Implement `backend/app/workflows/nodes/select_context.py` — call ContextSelector; enforce FINAL_CONTEXT_CHUNKS and token budget; store selected_context
- [X] T070 [US1] Implement `backend/app/workflows/nodes/generate_answer.py` — build prompt with instruction separation: system role (HR grounding rules + injection defense), user role (query), context role (retrieved chunks marked as untrusted data); call LLM; store draft_answer + citations
- [X] T071 [US1] Implement `backend/app/workflows/nodes/validate_citations.py` — verify each LLM-generated citation chunk_id exists in selected_context; verify document_id matches; discard fabricated citations; set citation_validation_result
- [X] T072 [US1] Implement `backend/app/workflows/nodes/check_groundedness.py` — verify answer does not claim beyond selected_context; set groundedness_result (grounded | abstained | qualified); route to safe fallback if failed
- [X] T073 [US1] Implement `backend/app/workflows/nodes/format_response.py` — assemble final answer + validated citations; set final_answer_status; persist RAG run to DB

### Guardrails

- [X] T074 [US1] Create `backend/app/guardrails/injection_screen.py` — screen input and retrieved content for injection patterns ("ignore previous instructions", "reveal system prompt", etc.); return blocked=True with reason; log with request_id
- [X] T075 [US1] Create `backend/app/guardrails/output_validator.py` — scan response for prompt leakage, citation IDs not in selected_context, policy invention markers; return validation_result

### Document Service & API

- [X] T076 [US1] Create `backend/app/services/document_service.py` — upload(files): validate, check content_hash dedup, store file, create DB record status=PENDING, enqueue background ingestion; get_status(id); delete(id): DELETED + purge chunks; reprocess(id): FAILED->PENDING + re-enqueue
- [X] T077 [US1] Create `backend/app/api/v1/documents.py` — FastAPI router: POST /upload (multipart), GET /, GET /{id}, DELETE /{id}, POST /{id}/reprocess, GET /{id}/status; correct HTTP codes 202/204/400/404/409

### Chat Service & Streaming API

- [X] T078 [US1] Create `backend/app/services/chat_service.py` — ChatService.stream(request) -> AsyncGenerator: invoke rag_app; yield SSE events per streaming-contract.md: token events, citations event, done event, abstention event, error event; handle cancellation flag; persist RAG run after completion
- [X] T079 [US1] Create `backend/app/api/v1/chat.py` — POST /chat (non-streaming); POST /chat/stream (StreamingResponse); DELETE /chat/stream/{request_id} (set cancellation flag)

### Frontend — Core Chat Interface

- [X] T080 [US1] Create `frontend/src/services/api.ts` — typed API client; standard error handling; uploadDocuments, getDocuments, getDocumentStatus, deleteDocument, reprocessDocument, sendChat, getKnowledgeBaseStats
- [X] T081 [US1] Create `frontend/src/services/stream.ts` — SSE streaming client: streamChat(request, callbacks); parse token/citations/done/abstention/error events; return abort controller for stop-generation
- [X] T082 [US1] Create `frontend/src/types/index.ts` — TypeScript interfaces: Document, Message, Conversation, Citation, ChatResponse, StreamEvent, KnowledgeBaseStats
- [X] T083 [US1] Create `frontend/src/features/chat/MessageList.tsx` — user + assistant message bubbles; Markdown rendering (react-markdown); code highlighting (highlight.js); typing indicator while streaming; scroll-to-bottom on new message
- [X] T084 [US1] Create `frontend/src/features/chat/CitationPanel.tsx` — render validated citations: document name, page number (when available), section name (when available); no fabricated citations
- [X] T085 [US1] Create `frontend/src/features/chat/ChatInput.tsx` — text input; submit on Enter; Stop Generation button (during streaming only); accessible label and unique ID
- [X] T086 [US1] Create `frontend/src/features/chat/EmptyState.tsx` — empty chat state with 5 example HR questions as clickable chips
- [X] T087 [US1] Create `frontend/src/features/chat/ChatPage.tsx` — compose MessageList + CitationPanel + ChatInput + EmptyState; manage streaming state; handle all SSE events; stop generation on abort; mark complete ONLY after done event
- [X] T088 [US1] Create `frontend/src/hooks/useStream.ts` — custom hook wrapping stream.ts; manages isStreaming, currentTokens, citations, error state; exposes sendMessage(query) and stopGeneration()

**Checkpoint (US1)**: Upload PDF -> READY -> ask question -> streamed tokens appear progressively -> citation panel after done event -> abstention for unanswerable question.


---

## Phase 4: User Story 2 — Manage the Document Knowledge Base (Priority: P2)

**Goal**: View all documents, monitor status, delete outdated ones, reprocess failures.
**Independent Test**: Upload -> READY -> delete -> verify gone from panel and not retrieved.

- [X] T089 [US2] Create `frontend/src/features/documents/DocumentList.tsx` — table of all documents: name, type, size, status badge (7 states in distinct colors), chunk count, upload timestamp; real-time status polling every 3 s while not in terminal state; client-side search/filter by name
- [X] T090 [US2] Create `frontend/src/features/documents/DocumentUpload.tsx` — drag-and-drop + file picker; multi-file selection; per-file upload progress; advisory client-side extension check; handle 400/409 errors with user-friendly messages
- [X] T091 [US2] Create `frontend/src/features/documents/DocumentActions.tsx` — Delete button (with confirmation dialog), Reprocess button (FAILED only); optimistic list update; inline error on failure
- [X] T092 [US2] Create `frontend/src/features/documents/KnowledgeBasePanel.tsx` — compose DocumentList + DocumentUpload + stats (total docs, total chunks, last indexed time) from GET /knowledge-base/stats; refresh after upload/delete/reprocess
- [X] T093 [US2] Create `frontend/src/hooks/useDocuments.ts` — fetches document list on mount; polls status for non-terminal docs; exposes upload(files), deleteDocument(id), reprocessDocument(id); manages loading/error
- [X] T094 [US2] Create `backend/app/api/v1/knowledge_base.py` — GET /knowledge-base/stats; GET /knowledge-base/healthrocessDocument(id); manages loading/error
- [ ] T094 [US2] Create `backend/app/api/v1/knowledge_base.py` — GET /knowledge-base/stats; GET /knowledge-base/health

**Checkpoint (US2)**: Panel shows all docs with live status; delete removes doc and its content from queries; FAILED doc reprocess button works.

---

## Phase 5: User Story 3 — Conversation History and Multi-Turn Q&A (Priority: P3)

**Goal**: Conversations persist; navigate history; start new; clear conversation.
**Independent Test**: Two-turn conversation -> new conversation -> return via history -> both messages restored exactly.

- [X] T095 [US3] Create `backend/app/services/conversation_service.py` — create(), list(), get(id) with messages, delete(id), add_message(conversation_id, role, content, rag_run_id); auto-generate title from first user message (truncate 60 chars)
- [X] T096 [US3] Create `backend/app/api/v1/conversations.py` — POST /, GET /, GET /{id}, DELETE /{id}
- [X] T097 [US3] Create `frontend/src/features/chat/ConversationSidebar.tsx` — sidebar list ordered by updated_at desc; active highlighted; title + relative timestamp; "New Conversation" button at top; click loads conversation messages
- [X] T098 [US3] Create `frontend/src/features/chat/ConversationControls.tsx` — "Clear Conversation" button with confirmation; "New Conversation" shortcut in chat header; wire to DELETE /{id}
- [X] T099 [US3] Create `frontend/src/hooks/useConversation.ts` — manages current conversation_id; loads messages on switch; creates new conversation on demand; persists conversation_id in sessionStorage for browser refresh recovery
- [X] T100 [US3] Update `backend/app/workflows/nodes/load_conversation_context.py` — confirm history truncation to MAX_HISTORY_MESSAGES most recent; confirm fresh retrieval triggered for every factual HR question regardless of history content

**Checkpoint (US3)**: Two-turn conversation restores on navigation; new conversation shows empty state; clear removes all messages; history survives container restart.

---

## Phase 6: User Story 5 — Streaming Polish and Stop-Generation (Priority: P2)

**Goal**: Stop generation mid-stream; copy answer; regenerate response; retry on error.
**Independent Test**: Ask question -> click Stop -> partial tokens visible -> no done event after stop -> citations never fabricated.

- [X] T101 [US5] Add copy-answer button to `frontend/src/features/chat/MessageList.tsx` — copies assistant text to clipboard; show "Copied!" for 2 s
- [X] T102 [US5] Add copy-code button inside code blocks in react-markdown rendering in `frontend/src/features/chat/MessageList.tsx`
- [X] T103 [US5] Add regenerate-response button to last assistant message in `frontend/src/features/chat/ChatPage.tsx` — re-sends last user message; replaces last assistant message in place
- [X] T104 [US5] Add retry-on-error button in `frontend/src/features/chat/ChatPage.tsx` — shown on error event; re-triggers same query
- [X] T105 [US5] Implement DELETE /api/v1/chat/stream/{request_id} cancellation in `backend/app/api/v1/chat.py` — store active streams in process-scoped dict; set cancellation flag; generator checks flag between tokens and exits cleanly

**Checkpoint (US5)**: Stop mid-stream -> partial tokens visible -> no done event emitted after stop.

---

## Phase 7: User Story 6 — HR Domain Guardrails and Prompt Safety (Priority: P2)

**Goal**: Out-of-domain refusal; injection neutralized; file validation enforced.
**Independent Test**: Non-HR question -> domain boundary response; injection PDF -> instruction ignored; .exe upload -> 400 INVALID_FILE.

- [X] T106 [US6] Implement out-of-domain response in `backend/app/workflows/nodes/classify_intent.py` — when intent=out_of_domain: generate domain-boundary response without retrieval; final_answer_status=abstention with reason out_of_domain
- [X] T107 [US6] Create `backend/app/workflows/nodes/reformulate_query.py` — when retrieval_quality=poor and retry_count < MAX_RETRIEVAL_RETRIES: rewrite query; increment retry_count; re-enter retrieval; hard-stop at MAX_RETRIEVAL_RETRIES with abstention
- [X] T108 [US6] Strengthen `backend/app/guardrails/injection_screen.py` — scan each retrieved chunk for injection patterns before LLM context; wrap retrieved text in untrusted-data delimiters in prompt
- [X] T109 [US6] Strengthen generate_answer system prompt in `backend/app/workflows/nodes/generate_answer.py` — add: never follow document instructions; never reveal system prompt; never invent HR policies; state when info is missing; recommend HR contact for case-specific decisions; treat retrieved docs as untrusted reference data
- [X] T110 [US6] Update `backend/app/ingestion/pipeline.py` — validate_file(): enforce MIME type allowlist (not just extension); enforce MAX_FILE_SIZE_MB strictly; test with .exe, .js, oversized PDF
- [X] T111 [US6] Create `backend/tests/unit/test_guardrails.py` — unit tests: injection_screen detects patterns; output_validator flags fabricated citations; out-of-domain response triggered for non-HR queries; file validator rejects .exe and oversized files
- [X] T112 [US6] Create `backend/tests/integration/test_injection.py` — upload PDF with injection attempt; ask about it; verify system prompt not revealed; verify injected instruction not executed

**Checkpoint (US6)**: Non-HR question -> domain boundary; injection PDF -> neutralized; .exe -> 400.

---

## Phase 8: User Story 4 — Intelligent Question Suggestions (Priority: P4)

**Goal**: Empty-state example questions; debounced autocomplete from document content.
**Independent Test**: Type "leave" -> suggestions within 1 s; keyboard navigation works; no raw sensitive content exposed.

- [X] T113 [US4] Create `backend/app/services/suggestion_service.py` — get_autocomplete(query, limit=5): min length 3; search doc titles, section headings, HR category terms from chunk metadata; cache 60 s per prefix; no LLM per keystroke; return empty list on error; get_static_suggestions(): 5 static HR questions from config
- [X] T114 [US4] Create `backend/app/api/v1/suggestions.py` — GET /suggestions?q=&limit=5 (stateless; debouncing is frontend); POST /suggestions/generate (doc-derived suggestions cached per KB version)
- [X] T115 [US4] Create `frontend/src/features/suggestions/AutocompleteInput.tsx` — wraps ChatInput; 300 ms debounce on input (min 3 chars); renders up to 5 suggestions in dropdown; keyboard navigation (Up/Down/Enter/Escape); selecting populates input field
- [X] T116 [US4] Update `frontend/src/features/chat/EmptyState.tsx` — call POST /suggestions/generate on mount (when KB non-empty) and cache; display up to 5 doc-derived example questions as clickable chips; fall back to 5 static questions on error or empty KB

**Checkpoint (US4)**: Empty state shows example questions; "leave" shows suggestions within 1 s; keyboard navigation works; no raw document content in suggestions.

---

## Phase 9: User Story 7 — Observability and System Health (Priority: P3)

**Goal**: Full pipeline traceability; structured logs with request_id/trace_id; LangSmith integration.
**Independent Test**: Submit query -> find request_id -> grep backend logs -> confirm all pipeline stages logged.

- [X] T117 [US7] Create `backend/app/observability/trace_context.py` — Python contextvars for request_id and trace_id; middleware injects at request start; structlog includes them via contextvars processor
- [X] T118 [US7] Update `backend/app/main.py` — observability middleware: generate UUID request_id; inject into contextvars; add X-Request-ID response header; log request start/end with status and latency
- [X] T119 [US7] Implement LangSmith tracing in `backend/app/workflows/rag_graph.py` — configure callbacks when LANGSMITH_TRACING=true; log LangSmith trace_id to structlog; degrade gracefully when LangSmith unavailable
- [X] T120 [US7] Update all LangGraph node files — add structured log at node entry and exit: node name, request_id, trace_id, key state fields and latency for compute-heavy nodes
- [X] T121 [US7] Verify `backend/app/repositories/rag_run_repository.py` — confirm insert_rag_run() persists all required fields: query, intent, domain, retrieval_mode, reranker, chunk IDs, scores JSONB, token counts, latency, citation_validation_result, groundedness_result, guardrail_result, retry_count, final_answer_status

**Checkpoint (US7)**: GET /health 200 within 500 ms; X-Request-ID in response header; backend logs show entries for every pipeline node for given request_id.

---

## Phase 10: Deployment and CI/CD

- [X] T122 Create `deployment/kubernetes/namespace.yaml` — hr-rag namespace
- [X] T123 [P] Create `deployment/kubernetes/configmap.yaml` — non-secret env vars
- [X] T124 [P] Create `deployment/kubernetes/secret.example.yaml` — example Secret manifest with placeholder values; add gitignore rule for secret.yaml
- [X] T125 [P] Create `deployment/kubernetes/postgres.yaml` — StatefulSet with pgvector image; PVC; readiness and liveness probes; resource requests/limits
- [X] T126 [P] Create `deployment/kubernetes/backend.yaml` — Deployment with readiness probe on /ready; liveness on /health; env from ConfigMap + Secret
- [X] T127 [P] Create `deployment/kubernetes/frontend.yaml` — Deployment for nginx frontend; readiness probe on /
- [X] T128 [P] Create `deployment/kubernetes/services.yaml` — ClusterIP Services for all three deployments
- [X] T129 [P] Create `deployment/kubernetes/ingress.yaml` — Ingress: / -> frontend, /api/ -> backend
- [X] T130 [P] Create `deployment/kubernetes/pvc.yaml` — PVC for PostgreSQL data and uploads volume
- [X] T131 Create `deployment/jenkins/Jenkinsfile` — Declarative Pipeline: Checkout -> Install (pip + npm ci) -> Lint (ruff + ESLint) -> Type check (mypy + tsc) -> Unit tests (pytest + vitest) -> Integration tests (testcontainers) -> Build images -> Push images (main branch only, Jenkins credentials) -> Deploy to K8s (main branch only) -> Smoke tests (curl /health + /ready)
- [X] T132 Create `backend/app/mcp/mcp_client.py` — Filesystem MCP server client (read-only); path allowlist scoped to uploads directory only; log every tool call with request_id and trace_id; handle unavailability gracefully (log warning, do not block RAG pipeline); document: server selected, tools exposed, safety restrictions, failure handling
- [X] T133 Create `docs/deployment.md` — Docker Compose local guide; Kubernetes steps; Jenkins setup; MCP configuration; env var reference

**Checkpoint**: docker compose up -> full stack healthy; Jenkinsfile lints without error; kubectl apply --dry-run=client passes on all manifests.

---

## Phase 11: Evaluation Framework and Polish

- [X] T134 Expand `evaluation/datasets/hr-golden-v1.json` to 50 cases: leave, attendance, benefits, onboarding, offboarding, WFH, performance, policy comparison, exact terminology, paraphrase, multi-hop, ambiguous, no-answer, out-of-domain, conflicting versions, spreadsheet, injection, citation validation
- [X] T135 Create `evaluation/scripts/run_eval.py` — load golden dataset; run each question through RAG pipeline (non-streaming); compute Recall@K, Precision@K, MRR, NDCG@K, faithfulness, citation_correctness, abstention_quality; output JSON report to evaluation/reports/
- [X] T136 Run baseline evaluation (dense-only, no reranker); record Recall@10 -> `evaluation/reports/baseline.json`
- [X] T137 Run hybrid + BGE reranker evaluation -> `evaluation/reports/hybrid_bge.json`; verify Recall@10 > baseline (SC-010)
- [X] T138 [P] Create `backend/tests/e2e/test_full_pipeline.py` — upload leave-policy.pdf -> READY -> ask 3 questions -> verify each has >=1 citation -> out-of-domain -> abstention -> delete -> not retrieved
- [X] T139 [P] Create `backend/tests/e2e/test_injection_e2e.py` — upload injection PDF -> ask -> system prompt not revealed; oversized file -> 400; duplicate -> 409
- [X] T140 [P] Create `backend/tests/unit/test_chunking.py` — policy_chunker keeps title+body; FAQ kept as unit; spreadsheet_chunker includes headers in every chunk; empty chunk rejected
- [X] T141 [P] Create `backend/tests/unit/test_fusion.py` — RRF deduplicates by chunk_id; scores computed correctly; top_k limit applied; metadata preserved
- [X] T142 [P] Create `backend/tests/integration/test_ingestion.py` — upload PDF -> verify READY -> verify chunks in DB with correct metadata -> verify HNSW index queryable
- [X] T143 [P] Create `backend/tests/integration/test_retrieval.py` — index test chunks -> dense query returns relevant result; sparse query returns exact HR term match; hybrid RRF output > dense-only
- [X] T144 Run quickstart.md scenarios 1-11 against full Docker Compose stack; document pass/fail per scenario
- [X] T145 [P] Create `docs/architecture.md` — system overview, retrieval pipeline diagram, LangGraph workflow diagram
- [X] T146 [P] Create `docs/api.md` — API reference linking to contracts/
- [X] T147 [P] Update `README.md` — project overview, quick-start, feature list, architecture summary, docs links

**Checkpoint (Final)**: All quickstart.md scenarios pass; hybrid+reranker Recall@10 > baseline; all CI stages pass in Jenkinsfile dry-run.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — start immediately
- **Phase 2**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 MVP)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2 + Phase 3 (shares document service)
- **Phase 5 (US3)**: Depends on Phase 2 + Phase 3 (shares chat API)
- **Phase 6 (US5)**: Depends on Phase 3 (streaming built in US1)
- **Phase 7 (US6)**: Depends on Phase 3 (guardrails layer)
- **Phase 8 (US4)**: Depends on Phase 2 only (suggestion service standalone)
- **Phase 9 (US7)**: Depends on Phase 3 (wraps existing nodes)
- **Phase 10**: Depends on Phase 3+ (can begin in parallel with Phase 4+)
- **Phase 11**: Depends on Phase 3+ complete for meaningful metrics

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|-----------|---------------------|
| US1 (P1) | Foundation | — |
| US2 (P2) | US1 | US3, US4, US5, US6 |
| US3 (P3) | US1 | US2, US4, US5, US6 |
| US5 (P2) | US1 | US2, US3, US4, US6 |
| US6 (P2) | US1 | US2, US3, US4, US5 |
| US4 (P4) | Foundation | All others |
| US7 (P3) | US1 | US2, US3, US4, US5, US6 |

---

## Parallel Execution Examples

### Phase 3 (US1) Parallelizable Groups

```
# Group A — Loaders (run in parallel):
T039 pdf_loader.py | T040 docx_loader.py | T041 text_loader.py | T042 excel_loader.py

# Group B — Providers (run in parallel):
T051-T053 EmbeddingProvider | T055 BGEReranker | T056 CohereReranker

# Group C — LangGraph nodes (after T036-T037):
T061 validate_request | T062 load_context | T063 classify_intent | T064 process_query

# Group D — Frontend components (after T080-T082):
T083 MessageList | T084 CitationPanel | T085 ChatInput | T086 EmptyState
```

### Phase 10 Parallelizable Group

```
T122-T131 (all Kubernetes manifests and Jenkinsfile) can run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — CRITICAL
3. Complete Phase 3: User Story 1 (T038-T088)
4. STOP AND VALIDATE: Run quickstart.md scenarios 1-5
5. Demo: upload PDF -> ask question -> see streamed cited answer

### Incremental Delivery

| Milestone | Phases | What Users Get |
|-----------|--------|----------------|
| MVP | 1, 2, 3 | Upload + Ask + Streamed cited answers |
| v0.2 | + 4, 5 | Document management + Conversation history |
| v0.3 | + 6, 7 | Guardrails + Observability |
| v0.4 | + 8 | Autocomplete + Suggestions |
| v1.0 | + 9, 10, 11 | Deployment + Evaluation + CI/CD |

---

## Notes

- [P] tasks operate on different files with no inter-dependencies — safe to parallelize
- [USn] labels map each task to its user story for traceability
- Each phase ends with a verifiable checkpoint
- Commit after each task or logical group
- Re-read constitution.md before starting each new phase
- Never hardcode secrets: verify with grep -r "sk-" backend/ before commit
- Run ruff check . and mypy backend/ before every PR

