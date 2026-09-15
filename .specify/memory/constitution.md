<!--
SYNC IMPACT REPORT (remove before committing)
=============================================
Version change: [TEMPLATE STUB] → 1.0.0 (initial adoption)
Added sections:
  - Core Principles (I–VIII)
  - Security & Guardrail Standards
  - Development Workflow & Quality Gates
  - Governance
Modified principles: N/A (first version)
Removed sections: N/A (first version)
Deferred TODOs:
  - RATIFICATION_DATE: Set to 2026-09-15 (today, first adoption).
    Update if team formally ratifies on a different date.
  - No other placeholders deferred.
=============================================
-->

# HR Knowledge Assistant Constitution

## Core Principles

### I. Code Quality & Maintainability (NON-NEGOTIABLE)

Every module in the HR Knowledge Assistant MUST be written to be
maintainable, readable, and independently testable. Code quality is not
optional and cannot be deferred.

- **Separation of concerns is mandatory.** The codebase MUST maintain
  clear boundaries between: Frontend, Backend API, LangGraph orchestration,
  Document ingestion, Retrieval, Reranking, Knowledge storage,
  LLM/embedding providers, Guardrails, Evaluation, and Observability.
- **Provider abstractions are required.** Every external provider
  (LLM, embeddings, reranker, vector store, MCP tools) MUST be accessed
  through a clean interface/abstraction. No business logic may depend
  directly on a provider-specific SDK call.
- **No hardcoded secrets.** All API keys, database credentials, and
  environment-specific values MUST come from environment variables.
  Committing real secrets is a critical violation.
- **No stack traces in user-facing responses.** Internal errors MUST be
  logged with full detail; users MUST receive only safe, friendly error
  messages.
- **Configuration over code.** Retrieval parameters (TOP_K, OVERLAP,
  thresholds), model selections, reranker choices, and domain rules MUST
  be configurable via environment variables or config files — not hardcoded.
- **YAGNI + avoid over-engineering.** Implement only the abstractions the
  project actually requires. Provider interfaces MUST remain clean and
  replaceable; unnecessary layers MUST NOT be added speculatively.
- **Async by default on the backend.** The FastAPI application MUST use
  async I/O. Blocking calls MUST NOT occur in the API event loop. Long-
  running ingestion MUST be decoupled from the API (background task or
  worker pattern).
- **Structured, typed schemas everywhere.** All API request/response bodies
  MUST be defined with Pydantic models. All LangGraph state MUST use an
  explicit, typed TypedDict-based state schema.

### II. Testing Standards (NON-NEGOTIABLE)

A feature is not complete until it is tested. Testing is a first-class
engineering activity, not an afterthought.

- **Unit tests are required** for all non-trivial logic: file validation,
  content hashing, document loaders, chunking strategies, RRF fusion,
  reranker adapters, context selection, citation validation, guardrail
  logic, API schema models, and configuration loading.
- **Integration tests are required** for every major pipeline boundary:
  Upload > Parse > Chunk > Embed > Index; PostgreSQL persistence; dense,
  sparse, and hybrid retrieval; RRF fusion; reranking; LangGraph graph
  execution; citation validation; document deletion; reprocessing;
  streaming; Docker service connectivity; and MCP integration.
- **End-to-end tests MUST cover the full user journey**: upload an HR PDF,
  wait for indexing, ask a question, verify a streamed cited answer, ask a
  question with no answer and verify abstention, upload Excel, ask a
  spreadsheet question, upload DOCX, compare documents, delete a document,
  verify the deleted content is no longer retrieved.
- **Guardrail tests are required**: prompt injection via PDF, DOCX, Excel
  cells, and user query; oversized files; unsupported file types; malformed
  files; excessively long queries; out-of-domain questions; citation
  fabrication attempts; and MCP tool injection attempts.
- **Regression testing is triggered** whenever chunking, embeddings,
  retrievers, rerankers, prompts, LLM configuration, context selection,
  guardrails, or domain metadata change. Regression runs MUST use the HR
  golden evaluation dataset.
- **RAG evaluation is required.** The project MUST maintain an HR golden
  dataset (target: 50-100 questions). Retrieval metrics (Recall@K,
  Precision@K, MRR, NDCG@K) and generation metrics (faithfulness,
  answer relevance, citation correctness, abstention quality, hallucination
  rate) MUST be measured before and after every reranker or retrieval
  configuration change.
- **Test isolation.** Tests MUST NOT depend on production data, external
  paid APIs (unless integration tests with explicit opt-in flags), or
  shared mutable state. Use fixtures, mocks, and test containers.

### III. Groundedness & Answer Integrity (NON-NEGOTIABLE)

The HR Knowledge Assistant MUST prioritize accurate, grounded answers over
confident-sounding responses.

- **Answers MUST be grounded in retrieved, approved HR documents.** The LLM
  MUST NOT invent HR policies, leave balances, dates, benefits, rules, or
  citations.
- **Abstention is required** when retrieved context is insufficient, no
  relevant documents are found, documents conflict irresolvably, or the
  question is outside the HR domain or requires a personal employment/legal
  decision. Abstention is always preferred over fabrication.
- **Citation validation is mandatory.** Every citation in a generated
  answer MUST be verified against the actual retrieved chunks in the current
  RAG run. LLM-generated citation identifiers MUST NOT be trusted without
  backend validation.
- **Retrieved documents are untrusted content.** The LLM MUST treat all
  retrieved document text as data, not as instructions. Content inside
  documents that conflicts with system instructions MUST be ignored.
- **Conversation history is not authoritative policy.** Prior assistant
  answers in conversation history MUST NOT be treated as established facts.
  Every factual HR question MUST retrieve fresh evidence.

### IV. User Experience Consistency (NON-NEGOTIABLE)

The frontend MUST deliver a consistent, professional, and accessible HR
assistant experience across all interaction states.

- **Streaming is mandatory.** The frontend MUST display streamed assistant
  responses via SSE or equivalent. A "completed" state MUST NOT be shown
  before the backend confirms completion.
- **All processing states MUST be visible.** The document upload interface
  MUST display PENDING, UPLOADING, PROCESSING, INDEXING, READY, FAILED,
  and DELETED states clearly and distinctly.
- **Source citations MUST be displayed** in every assistant response that
  uses retrieved knowledge. Citations MUST include: document name, page
  number (when available), section name (when available), and a citation
  identifier. Fabricated citations MUST NOT be displayed.
- **Error states are required for every user-facing operation.** Upload
  errors, indexing failures, retrieval failures, LLM timeouts, and network
  errors MUST all surface a clear, actionable message to the user. Stack
  traces and internal error details MUST NOT be shown.
- **Loading and empty states MUST exist.** The chat interface MUST provide
  an empty state with example HR questions. Every async operation MUST
  show a loading indicator.
- **Autocomplete MUST be efficient and safe.** Suggestions MUST be debounced,
  cached, bounded in count, and protected from exposing sensitive document
  content or private employee data. Expensive LLM calls MUST NOT be triggered
  on every keystroke.
- **Accessibility.** All interactive controls MUST have unique, descriptive
  IDs. Keyboard navigation MUST work for autocomplete and suggestion lists.
  The interface MUST be responsive (desktop-first, mobile-capable).

### V. Retrieval Quality (NON-NEGOTIABLE)

Dense-only retrieval is insufficient for HR knowledge. The retrieval
architecture MUST be hybrid and reranked by default.

- **Hybrid retrieval is the default.** The system MUST combine dense
  (semantic) and sparse (keyword/BM25-equivalent) retrieval using
  Reciprocal Rank Fusion (RRF). Dense-only retrieval is not acceptable
  as the production configuration.
- **Reranking is mandatory.** The pipeline MUST support BAAI BGE Reranker
  v2 M3 and Cohere Rerank. The reranker MUST be selected via configuration,
  not hardcoded. Reranking quality MUST be benchmarked against no-reranker
  and cross-reranker baselines.
- **Chunking MUST be structure-aware.** Fixed-size splitting MUST NOT be
  applied uniformly to all document types. Chunking MUST account for
  document structure: headings, sections, tables, FAQs, and procedures.
  HR-specific rules (keep policy title with section, keep eligibility with
  rule, keep exceptions with policy) MUST be applied.
- **Metadata filtering MUST be preserved** through every retrieval and
  fusion stage. Chunk metadata (document ID, version, page, section,
  content hash) MUST never be stripped during candidate processing.
- **Retrieval parameters MUST be configurable** (DENSE_TOP_K, SPARSE_TOP_K,
  FUSION_TOP_K, RERANK_TOP_K, FINAL_CONTEXT_CHUNKS) and MUST be tuned
  using the HR evaluation dataset.

### VI. Security & Prompt Injection Defense (NON-NEGOTIABLE)

Prompt injection is a real and active threat in any RAG system. Defenses
MUST be built into every layer.

- **Instruction separation is mandatory.** System instructions, user queries,
  retrieved context, and MCP tool outputs MUST be structurally separated in
  every LLM call. Retrieved content MUST be marked as untrusted reference
  data.
- **The LLM MUST be instructed** to never follow instructions embedded in
  retrieved documents, never reveal the system prompt, never reveal internal
  configuration or secrets, and never execute arbitrary document text as a
  command.
- **Tool access is restricted.** MCP tools MUST use explicit allowlists,
  validated inputs, restricted scopes, and no raw untrusted content as tool
  arguments. The initial system MUST be read-only for MCP.
- **File upload validation is required.** File type, size, encoding, and
  content MUST be validated by the backend (not just the frontend). Allowed
  extensions and maximum file sizes MUST be enforced.
- **Output validation is required.** Generated responses MUST be checked
  for: unsupported claims, citation mismatch, prompt leakage, unsafe
  instructions, HR policy invention, and unverified personal recommendations.
- **No logging of secrets, API keys, or unnecessary sensitive employee
  information.** Debug mode MUST be explicitly off by default in production.

### VII. Observability & Traceability (NON-NEGOTIABLE)

The system MUST be observable end-to-end. Every RAG run MUST be traceable
from user query through retrieval, reranking, generation, and validation.

- **Structured logging is required** on the backend. Every significant event
  MUST include: timestamp, log level, component, event name, request ID,
  trace ID, and error details where applicable.
- **Every RAG run MUST persist** its trace metadata: original query,
  rewritten queries, intent, domain, retrieved chunk IDs, retrieval scores,
  fusion scores, reranker provider, reranker scores, selected chunk IDs,
  context token count, LLM model, input/output token counts, generation
  latency, citation validation result, groundedness result, guardrail result,
  retry count, total latency, and final answer status.
- **LangSmith tracing is preferred** for LangGraph and LLM span tracking.
  When LangSmith is unavailable, structured request/trace IDs MUST still
  propagate through all backend layers.
- **Latency MUST be measured** at every major pipeline stage: retrieval,
  reranking, generation, and end-to-end. P50 and P95 latency MUST be
  trackable.
- **Health and readiness endpoints MUST exist** (/health, /ready) and MUST
  reflect the true readiness state of the backend (database reachable,
  vector index accessible).

### VIII. Performance Requirements

The system MUST be responsive and resource-efficient under normal local
single-user operation.

- **Ingestion MUST NOT block the API event loop.** Document parsing,
  embedding, and indexing MUST run as background tasks or in a separate
  worker. The API MUST return immediately with a processing status after
  upload.
- **Model instances MUST be reused.** The BGE Reranker MUST not be loaded
  per request. Embedding models MUST use connection pooling or singleton
  patterns appropriate to the provider.
- **Autocomplete MUST use caching and debouncing.** Suggestion requests
  MUST be debounced (minimum input length enforced) and results cached.
  LLM-generated suggestions MUST be bounded in cost and frequency.
- **Token budgets are mandatory.** Separate token budgets MUST be configured
  and enforced for: system prompt, conversation history, retrieved context,
  user query, and output response. Unbounded context growth MUST NOT be
  allowed.
- **Retry loops MUST have hard limits.** MAX_RETRIEVAL_RETRIES MUST be
  enforced. Infinite query-rewrite or retrieval loops MUST NOT be possible.
- **Caching MUST be invalidated on document change.** Parsed document,
  embedding, suggestion, and retrieval caches MUST be invalidated when the
  underlying documents are updated, reprocessed, or deleted.
- **Batch operations.** Embedding generation and reranker scoring MUST use
  batch APIs where available. Single-item calls per chunk are not acceptable
  for bulk ingestion.

## Security & Guardrail Standards

All implementation work MUST adhere to these non-negotiable security
standards:

- No hardcoded API keys, database passwords, registry credentials, or
  Kubernetes secrets in source code or committed files. Use `.env.example`
  for documentation and `.gitignore` for `.env` files.
- File uploads MUST enforce: allowed MIME type/extension allowlist,
  maximum file size limit, malformed file graceful rejection.
- The LangGraph RAG workflow MUST include explicit guardrail nodes:
  input validation, prompt injection screening, domain classification,
  retrieved content trust boundary, output validation, citation validation,
  and groundedness check.
- HR-specific prohibitions MUST be enforced at the guardrail layer:
  no inventing employee records, no revealing private employee data, no
  making hiring/firing decisions, no inferring protected characteristics,
  no providing definitive legal or medical advice, no presenting general
  policy as a personalized entitlement without explicit supporting evidence.
- MCP server calls MUST be logged, have timeout handling, and MUST NOT
  prevent core RAG functionality when the MCP server is unavailable.

## Development Workflow & Quality Gates

All code contributions to the HR Knowledge Assistant MUST satisfy these
gates before merge:

1. **Lint passes** (Python: ruff/flake8; TypeScript: ESLint). No lint
   suppressions without documented justification.
2. **Type checks pass** (Python: mypy or pyright; TypeScript: tsc strict
   mode). `any` types MUST be justified.
3. **Unit tests pass** with no regressions.
4. **Integration tests pass** against a local Docker Compose stack.
5. **No secrets committed** (pre-commit secret scan or equivalent).
6. **No new unexplained bracketed TODO tokens** introduced in spec/plan
   documents without an accompanying task.
7. **Changes to retrieval, chunking, embeddings, reranker, prompts, or
   LLM config MUST be accompanied by** an evaluation run against the
   HR golden dataset and a recorded metrics comparison.

Jenkins CI MUST automate steps 1-5 on every pull request. Steps 6-7 are
enforced during code and spec review.

## Governance

This constitution is the primary governance document for the HR Knowledge
Assistant project. It supersedes all other engineering practices, style
guides, and ad-hoc conventions where they conflict.

**Amendment procedure:**

- Principles may be amended through a documented proposal that includes:
  the change rationale, impact on existing components, and a migration plan.
- MAJOR amendments (principle removal or fundamental redefinition) require
  explicit team approval and MUST increment the MAJOR version.
- MINOR amendments (new principle or materially expanded guidance) increment
  MINOR version.
- PATCH amendments (clarifications, wording, typo fixes) increment PATCH.

**Compliance review:**

- All pull requests, plan reviews, and spec documents MUST be checked against
  this constitution. Non-compliant work MUST NOT be merged.
- The constitution MUST be reviewed and confirmed or updated whenever a new
  development phase begins.

**Authority:**

- The constitution is the definitive source of non-negotiable project rules.
  The spec (info.txt) is the source of functional requirements. Where
  requirements are ambiguous, this constitution's principles take precedence
  for governance decisions.

**Version**: 1.0.0 | **Ratified**: 2026-09-15 | **Last Amended**: 2026-09-15
