# Feature Specification: HR Knowledge Assistant — Production-Grade RAG Chatbot

**Feature Branch**: `001-hr-rag-chatbot`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: "Build an application as per the document info.txt — HR Knowledge Assistant, production-grade RAG chatbot"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload HR Documents and Ask Questions (Priority: P1)

An HR administrator or employee uploads one or more HR policy documents
(PDF, DOCX, XLSX, TXT, or Markdown) to the system. Once processing is
complete, they type a natural-language question about HR policy into the
chat interface and receive a grounded, cited answer in real time via
streamed output.

**Why this priority**: This is the core value proposition of the entire
system. Without the ability to upload documents and receive accurate,
cited answers, no other feature has meaning. This story alone constitutes
a usable MVP.

**Independent Test**: Can be fully tested by uploading a single HR PDF,
waiting for the READY status, typing "What is the annual leave
entitlement?", and verifying that a streamed answer with at least one
valid source citation is returned.

**Acceptance Scenarios**:

1. **Given** no documents have been uploaded, **When** the user opens the
   chat interface, **Then** an empty state with example HR questions is
   displayed and no answer generation occurs.

2. **Given** a valid PDF is uploaded, **When** processing completes,
   **Then** the document status changes to READY and the document appears
   in the knowledge-base panel with its name, type, size, and upload
   timestamp.

3. **Given** a READY document exists, **When** the user types "What is the
   sick leave policy?" and submits, **Then** a streamed answer appears
   token-by-token, includes at least one citation referencing the uploaded
   document by name and page/section, and does not display a completed
   state until the backend confirms generation is done.

4. **Given** a question is asked for which no uploaded document contains an
   answer, **When** the system processes the query, **Then** the assistant
   responds with a clear abstention message and does not fabricate policy content.

---

### User Story 2 - Manage the Document Knowledge Base (Priority: P2)

A user views all uploaded documents, monitors their processing status,
deletes outdated documents, and reprocesses corrected versions from a
dedicated knowledge-base panel within the interface.

**Why this priority**: Without document management, users cannot correct
mistakes, remove stale policies, or track which documents are available
for retrieval.

**Independent Test**: Can be fully tested by uploading a document,
verifying it appears in the knowledge-base panel with READY status,
deleting it, and confirming it no longer appears in the panel or in
subsequent query results.

**Acceptance Scenarios**:

1. **Given** multiple documents have been uploaded, **When** the user opens
   the knowledge-base panel, **Then** all documents are listed with name,
   type, size, status, upload timestamp, and chunk count.

2. **Given** a document is being processed, **When** the user views the
   panel, **Then** the document status is shown as PROCESSING or INDEXING,
   not READY.

3. **Given** a READY document exists, **When** the user deletes it, **Then**
   the document disappears from the panel, its chunks are removed from the
   knowledge base, and subsequent queries no longer return content from it.

4. **Given** a document failed processing, **When** the user triggers
   reprocess, **Then** the document status resets to PENDING and processing
   begins again with no uncontrolled duplicate chunks.

5. **Given** documents are present, **When** the user searches by name in
   the panel, **Then** the list filters in real time to show only matching
   documents.

---

### User Story 3 - Conversation History and Multi-Turn Q&A (Priority: P3)

A user holds a multi-turn conversation with the assistant, navigates back
to previous conversations from a history list, starts a new conversation,
and clears an existing one.

**Why this priority**: Conversation continuity significantly improves
usability for iterative policy research but is not required for the core
retrieval value to work.

**Independent Test**: Can be fully tested by having a two-turn conversation,
navigating away to a new conversation, then returning via the history list
and verifying both messages are restored exactly.

**Acceptance Scenarios**:

1. **Given** a conversation exists with prior messages, **When** the user
   returns to it from the history list, **Then** all prior messages are
   displayed in the correct order.

2. **Given** the user is in an ongoing conversation, **When** they ask a
   follow-up question, **Then** the assistant uses conversation context but
   still retrieves fresh evidence for factual HR claims.

3. **Given** the user clicks "New Conversation", **When** a new conversation
   starts, **Then** no prior messages are visible and the empty state is shown.

4. **Given** the user clicks "Clear Conversation", **When** confirmation is
   accepted, **Then** all messages in the current conversation are removed.

---

### User Story 4 - Intelligent Question Suggestions and Autocomplete (Priority: P4)

When the user has not yet typed a question, the interface shows example HR
questions. As the user starts typing, relevant question suggestions appear
based on uploaded document content, and can be selected with keyboard or mouse.

**Why this priority**: Autocomplete reduces friction for new users but the
system is fully usable without it.

**Independent Test**: Can be fully tested by opening the chat on an empty
state and verifying example HR questions appear, then typing "leave" and
verifying relevant suggestions appear within one second with keyboard
navigation working.

**Acceptance Scenarios**:

1. **Given** the chat input is empty and at least one document is READY,
   **When** the user views the interface, **Then** up to 5 example HR
   questions are displayed.

2. **Given** the user types at least 3 characters, **When** a debounce
   period has elapsed, **Then** up to 5 relevant suggestions appear drawn
   from document titles and HR categories, not raw sensitive content.

3. **Given** suggestions are displayed, **When** the user presses the Down
   arrow key, **Then** focus moves through suggestions; pressing Enter
   selects the highlighted suggestion into the input field.

---

### User Story 5 - Streaming Response with Source Citations (Priority: P2)

The assistant streams its answer in real time. As the response completes,
cited sources are displayed below the answer showing the document name,
page or section, and a citation identifier.

**Why this priority**: Streaming and citation transparency are non-negotiable
per the project constitution and are fundamental to the system's trustworthiness.

**Independent Test**: Can be fully tested by asking any answerable question
and verifying: tokens appear progressively, generation can be stopped,
citations appear at completion with valid document references only.

**Acceptance Scenarios**:

1. **Given** a query is submitted, **When** the backend begins streaming,
   **Then** tokens appear progressively in the assistant message bubble.

2. **Given** a streamed response is in progress, **When** the user clicks
   "Stop Generation", **Then** streaming halts and the partial response is
   preserved.

3. **Given** a completed streamed response includes citations, **When** the
   user reads the answer, **Then** each citation shows document name, page
   number (when available), and section name (when available).

4. **Given** the backend returns a response, **When** citations are
   validated, **Then** only citations referencing actually retrieved
   documents are displayed; fabricated citation IDs are never shown.

---

### User Story 6 - HR Domain Guardrails and Prompt Safety (Priority: P2)

The assistant refuses to answer questions outside the HR domain, does not
invent policies, protects against prompt injection, and directs users to HR
professionals for case-specific matters.

**Why this priority**: Guardrails are non-negotiable per the constitution.
Operating without them could deliver harmful or fabricated HR advice.

**Independent Test**: Can be fully tested by: asking a coding question and
verifying a domain refusal; uploading a PDF with an injection attempt and
verifying it is not executed; asking a personal entitlement question and
verifying a qualifying response.

**Acceptance Scenarios**:

1. **Given** the user asks a non-HR question, **When** the system processes
   the query, **Then** the assistant responds with a domain-boundary message
   and does not attempt retrieval or generation.

2. **Given** an uploaded document contains a prompt injection attempt,
   **When** a query retrieves that content, **Then** the injected text is
   treated as document data, not as an instruction.

3. **Given** the user asks for a personal employment decision, **When** the
   assistant responds, **Then** it declines to make the decision and
   recommends consulting HR.

4. **Given** an uploaded file is oversized or of an unsupported type,
   **When** the user attempts to upload it, **Then** the upload is rejected
   with a clear error message.

---

### User Story 7 - Observability and System Health (Priority: P3)

An operator or developer can verify that the system is healthy via health
and readiness endpoints and can trace any RAG run end-to-end through
structured logs and trace IDs.

**Why this priority**: Observability is non-negotiable per the constitution.
Without it the system cannot be debugged, improved, or trusted operationally.

**Independent Test**: Can be fully tested by hitting /health and /ready
endpoints, verifying 200 OK, submitting a query, then confirming structured
log entries for that request ID exist with full pipeline stage metadata.

**Acceptance Scenarios**:

1. **Given** the system is running, **When** /health is called, **Then** a
   200 response with system status is returned within 500ms.

2. **Given** a query is submitted, **When** the RAG pipeline executes,
   **Then** a structured log entry exists with: request ID, trace ID, intent,
   retrieval mode, chunk counts, reranker used, LLM model, token counts, and
   total latency.

3. **Given** an error occurs during retrieval or generation, **When** the
   user receives an error response, **Then** no stack trace or internal
   configuration is exposed in the user-facing message.

---

### Edge Cases

- What happens when the knowledge base is completely empty and a user submits a question? (Expected: abstention with "no documents indexed" message)
- What happens when a PDF is scanned-only (no embedded text)? (Expected: OCR fallback attempted; if unavailable, document is marked FAILED with a clear reason)
- What happens when the same document is uploaded twice? (Expected: content hash is checked; duplicate is rejected or replaced cleanly with no orphaned chunks)
- What happens when the LLM provider is unavailable during generation? (Expected: user receives a friendly unavailability message; conversation is preserved)
- What happens when a document is deleted while a query referencing it is in progress? (Expected: graceful handling with no internal error exposed to user)
- What happens when conversation history grows very long? (Expected: history is summarized or truncated; the current question is always preserved)
- What happens when an Excel file has multiple sheets with merged cells? (Expected: handled gracefully; unparseable cells are skipped and logged, not failing the document)
- What happens when two uploaded policy documents contradict each other? (Expected: assistant surfaces both versions and notes the conflict rather than silently picking one)

---

## Requirements *(mandatory)*

### Functional Requirements

**Document Ingestion**

- **FR-001**: The system MUST accept uploads of PDF, DOCX, TXT, Markdown, CSV, and XLSX files.
- **FR-002**: The system MUST validate file type, size, and encoding on the backend before processing.
- **FR-003**: The system MUST process uploaded documents through an ingestion pipeline (parse, clean, chunk, embed, index) without blocking the upload API response.
- **FR-004**: The system MUST track each document through the states: PENDING, UPLOADING, PROCESSING, INDEXING, READY, FAILED, DELETED.
- **FR-005**: The system MUST store per-chunk metadata including document ID, version, source file name, page number, section, parent section, chunk index, content hash, and creation timestamp.
- **FR-006**: The system MUST support document deletion that removes all associated chunks and embeddings from the knowledge base.
- **FR-007**: The system MUST support document reprocessing that replaces existing chunks without creating uncontrolled duplicates.
- **FR-008**: The system MUST detect and reject duplicate document uploads using content hashing.
- **FR-009**: The system MUST use structure-aware, HR-specific chunking: sections kept with their titles, eligibility conditions kept with their rules, exceptions kept with the policies they modify, FAQ items kept as question-answer units.

**Retrieval & Answer Generation**

- **FR-010**: The system MUST use hybrid retrieval combining dense (semantic) and sparse (keyword) search as the default retrieval mode.
- **FR-011**: The system MUST fuse dense and sparse retrieval candidates using Reciprocal Rank Fusion (RRF).
- **FR-012**: The system MUST support a configurable reranking stage with at minimum two reranker options (local cross-encoder and API-based reranker).
- **FR-013**: The system MUST generate answers grounded exclusively in retrieved HR documents and MUST NOT invent policy content.
- **FR-014**: The system MUST validate every citation in a generated answer against the actual retrieved chunks in that RAG run before including it in the response.
- **FR-015**: The system MUST abstain when retrieved context is insufficient, when no relevant documents are found, or when the question is outside the HR domain.
- **FR-016**: The system MUST classify user intent and route out-of-domain questions to a domain-boundary response without retrieval.
- **FR-017**: The system MUST enforce configurable token budgets for system prompt, conversation history, retrieved context, user query, and output.
- **FR-018**: The system MUST enforce hard limits on retrieval retry loops.

**Frontend & Conversation**

- **FR-019**: The system MUST provide a streaming chat interface where assistant responses are delivered progressively via Server-Sent Events or equivalent.
- **FR-020**: The system MUST display per-document source citations in every answer that uses retrieved knowledge, including document name, page number (when available), and section name (when available).
- **FR-021**: The system MUST support conversation persistence: conversations and messages must survive browser refresh and container restart.
- **FR-022**: The system MUST provide a knowledge-base panel listing all documents with their name, type, size, status, chunk count, and upload timestamp.
- **FR-023**: The system MUST display question suggestions on empty chat and debounced autocomplete as the user types, without exposing sensitive document content.
- **FR-024**: The system MUST allow the user to stop an in-progress streamed response.
- **FR-025**: The system MUST display clear, user-friendly error messages for all failure modes without exposing stack traces or internal configuration.

**Security & Guardrails**

- **FR-026**: The system MUST treat all retrieved document content as untrusted data and structurally separate it from system instructions in every LLM call.
- **FR-027**: The system MUST screen user inputs and retrieved content for prompt injection patterns.
- **FR-028**: The system MUST not expose API keys, database credentials, or system configuration in any response or error message.
- **FR-029**: MCP tool integrations MUST use explicit allowlists and MUST be read-only in the initial version.
- **FR-030**: The system MUST integrate at least one MCP server for controlled external tool access, with full documentation of its capabilities, restrictions, and failure handling.

**Observability & Deployment**

- **FR-031**: The system MUST emit structured logs for every significant event, including request ID and trace ID.
- **FR-032**: The system MUST persist RAG run metadata for every query: query, intent, retrieval scores, reranker used, selected chunks, LLM model, token counts, latency, citation validation result, and groundedness result.
- **FR-033**: The system MUST expose /health and /ready endpoints that reflect the true operational state of the backend.
- **FR-034**: The system MUST run entirely via Docker Compose on a local machine with PostgreSQL, pgvector, backend, and frontend as services.
- **FR-035**: The system MUST include Kubernetes deployment manifests and a Jenkins CI/CD pipeline as deployment artifacts.
- **FR-036**: All configuration MUST be provided via environment variables; no secrets may be hardcoded in source code or committed files.

### Key Entities

- **Document**: An uploaded HR source file. Has a unique ID, file name, type, size, content hash, processing status, title, and category. Versioned over time.
- **Document Version**: A specific parsed and indexed snapshot of a Document. Tracks parser version, embedding model, index version, effective date, and whether it is the current version.
- **Document Chunk**: A bounded piece of text extracted from a Document Version. Has its own ID, index, content, content hash, token count, page/section/sheet references, metadata JSONB, and embedding vector.
- **Conversation**: A named session grouping a sequence of messages between the user and the assistant.
- **Message**: A single turn in a Conversation. Has a role (user/assistant), content, and timestamp.
- **RAG Run**: A record of a single query execution. Links to a conversation and stores the full retrieval and generation trace with latency metrics.
- **Evaluation Case**: A question-answer pair in the HR golden dataset used for regression evaluation.
- **Evaluation Result**: Metrics produced by running the RAG pipeline against an Evaluation Case.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can upload an HR PDF document and receive a first grounded, cited answer to an HR question within 60 seconds of the document reaching READY status.
- **SC-002**: At least 90% of answers to questions with clear document coverage include at least one validated, non-fabricated citation.
- **SC-003**: The system returns an abstention response (rather than a fabricated answer) for at least 95% of questions where no relevant document content exists in the knowledge base.
- **SC-004**: At least 95% of prompt injection attempts embedded in uploaded documents are neutralized (the injected instruction is not executed by the assistant).
- **SC-005**: End-to-end latency from query submission to first streamed token is under 5 seconds for a knowledge base of up to 100 documents on commodity local hardware.
- **SC-006**: The document processing pipeline successfully indexes at least 95% of well-formed PDF, DOCX, XLSX, TXT, and Markdown files without manual intervention.
- **SC-007**: The system correctly routes at least 95% of clearly out-of-domain questions to a domain-boundary response without retrieval.
- **SC-008**: Deleting a document results in 100% of its chunks being removed from retrieval results within one subsequent query cycle.
- **SC-009**: The system passes all Jenkins CI pipeline stages (lint, type check, unit tests, integration tests, image build) for every code change before merge.
- **SC-010**: Retrieval quality (Recall@10) on the HR golden evaluation dataset is measurably higher with hybrid retrieval + reranking than with dense-only retrieval alone.

---

## Assumptions

- The initial deployment is single-user and local-only (Docker Compose). No authentication or multi-tenancy is required in this version, though the architecture must not make future authentication impossible.
- The user has access to at least one LLM provider API key (e.g., OpenAI, Anthropic, or Gemini) configured via environment variable.
- The user's local machine has sufficient RAM and disk to run PostgreSQL with pgvector, the backend, the frontend, and optionally a local reranker model via Docker.
- The BGE Reranker v2 M3 may require CUDA or will fall back to CPU inference; hardware requirements are documented but not guaranteed to be met by every user's machine.
- Enterprise features (SSO, RBAC, multi-tenant isolation, compliance audit logging) are out of scope for this version.
- Real-time collaboration (multiple simultaneous users editing the knowledge base) is out of scope.
- The system does not perform real-time web search; all knowledge comes from user-uploaded documents.
- Mobile browser support is desirable but secondary; the primary target is a desktop browser.
- Automatic policy expiry enforcement is a future enhancement; the initial version stores expiry date metadata but does not auto-retire chunks.
- LangSmith API access is optional; when unavailable, structured request and trace IDs propagate through logs instead.
- The HR golden evaluation dataset is seeded with synthetic examples and expanded as real questions are observed.
