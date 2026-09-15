# Data Model: HR Knowledge Assistant

**Phase 1 output for**: `specs/001-hr-rag-chatbot/plan.md`
**Date**: 2026-09-15

---

## Entities & Relationships

```
documents (1) ──< document_versions (1) ──< document_chunks
documents (1) ──< rag_runs (many, via conversation)
conversations (1) ──< messages
conversations (1) ──< rag_runs
rag_runs (1) ──> evaluation_results (via evaluation_cases)
evaluation_datasets (1) ──< evaluation_cases (1) ──< evaluation_results
```

---

## Table: `documents`

Represents an uploaded HR source file. One document may have many versions.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default gen_random_uuid() | Stable document identifier |
| `file_name` | VARCHAR(512) | NOT NULL | Original filename |
| `file_type` | VARCHAR(32) | NOT NULL | pdf, docx, xlsx, txt, md, csv |
| `file_size` | BIGINT | NOT NULL | Bytes |
| `content_hash` | VARCHAR(64) | NOT NULL, UNIQUE | SHA-256 of raw file bytes; dedup key |
| `status` | VARCHAR(32) | NOT NULL, DEFAULT 'PENDING' | PENDING\|UPLOADING\|PROCESSING\|INDEXING\|READY\|FAILED\|DELETED |
| `title` | VARCHAR(512) | NULLABLE | Extracted or user-provided title |
| `document_category` | VARCHAR(128) | NULLABLE | HR category (leave_policy, handbook, etc.) |
| `storage_path` | VARCHAR(1024) | NOT NULL | Relative path to stored original file |
| `error_message` | TEXT | NULLABLE | Set when status = FAILED |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Updated on every status change |

**State transitions** (validated at service layer):
- PENDING → UPLOADING → PROCESSING → INDEXING → READY
- Any state → FAILED (on pipeline error)
- FAILED → PENDING (on user-triggered reprocess)
- READY → DELETED (on user-triggered delete)
- DELETED is terminal; no further transitions permitted

**Validation rules**:
- `status` MUST be one of the 7 defined values (application-level enum + DB CHECK constraint)
- `content_hash` uniqueness enforced; duplicate upload rejected at service layer
- `file_type` MUST match allowed extension allowlist

---

## Table: `document_versions`

A specific parsed and indexed snapshot of a document. Created each time a document
is successfully processed (initial or reprocess).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `document_id` | UUID | FK → documents.id, NOT NULL | |
| `version` | VARCHAR(32) | NOT NULL | Monotonic version string e.g. "v1", "v2" |
| `content_hash` | VARCHAR(64) | NOT NULL | Hash of extracted + cleaned text |
| `parser_version` | VARCHAR(64) | NOT NULL | Ingestion pipeline semver |
| `embedding_model` | VARCHAR(128) | NOT NULL | Provider + model name (e.g. "openai/text-embedding-3-small") |
| `embedding_dim` | INTEGER | NOT NULL | Vector dimension |
| `index_version` | VARCHAR(64) | NOT NULL | Index schema version |
| `effective_date` | DATE | NULLABLE | Policy effective date (from metadata) |
| `expiry_date` | DATE | NULLABLE | Policy expiry date (from metadata); stored but not auto-enforced in v1 |
| `is_current` | BOOLEAN | NOT NULL, DEFAULT TRUE | Only one version per document may be current |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Validation rules**:
- Only one `is_current = TRUE` per `document_id` (enforced via partial unique index)
- On reprocess: existing `is_current` version set to FALSE; new version created as `is_current = TRUE`
- Stale chunks (linked to non-current version) MUST be purged after reprocess completes

---

## Table: `document_chunks`

A bounded piece of text extracted from a specific document version, with its
embedding and rich metadata.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `document_version_id` | UUID | FK → document_versions.id, NOT NULL | |
| `chunk_index` | INTEGER | NOT NULL | Ordinal position within the document |
| `content` | TEXT | NOT NULL | Chunk text content |
| `content_hash` | VARCHAR(64) | NOT NULL | SHA-256 of content; dedup within version |
| `token_count` | INTEGER | NOT NULL | Token count using the configured tokenizer |
| `page_number` | INTEGER | NULLABLE | Source page (PDF/DOCX) |
| `section` | VARCHAR(512) | NULLABLE | Immediate section heading |
| `parent_section` | VARCHAR(512) | NULLABLE | Parent section heading |
| `sheet_name` | VARCHAR(256) | NULLABLE | Source sheet (XLSX/CSV) |
| `row_start` | INTEGER | NULLABLE | Starting row (XLSX/CSV) |
| `row_end` | INTEGER | NULLABLE | Ending row (XLSX/CSV) |
| `is_ocr` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether content was OCR-derived |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | HR metadata: policy_type, region, effective_date, etc. |
| `embedding` | vector(1536) | NOT NULL | Dense vector; dimension matches embedding_model |
| `tsvector_content` | TSVECTOR | GENERATED ALWAYS AS ... STORED | For full-text search |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- HNSW on `embedding` (`ef_construction=128, m=16`) — dense search
- GIN on `tsvector_content` — sparse/full-text search
- B-tree on `document_version_id` — join performance
- B-tree on `(document_version_id, chunk_index)` — ordered retrieval

**Validation rules**:
- `token_count` MUST be > 0 and ≤ configured MAX_CHUNK_TOKENS
- Empty chunks (content.strip() == "") MUST be rejected at ingestion
- Duplicate chunks within a version (same content_hash) MUST be deduplicated

---

## Table: `conversations`

A named session grouping a sequence of user-assistant message turns.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `title` | VARCHAR(512) | NULLABLE | Auto-generated from first user message (truncated) |
| `message_count` | INTEGER | NOT NULL, DEFAULT 0 | Maintained via trigger or service layer |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Updated on every new message |

---

## Table: `messages`

A single turn within a conversation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `conversation_id` | UUID | FK → conversations.id, NOT NULL | |
| `role` | VARCHAR(16) | NOT NULL | "user" or "assistant" |
| `content` | TEXT | NOT NULL | Message content |
| `rag_run_id` | UUID | FK → rag_runs.id, NULLABLE | Links assistant message to its RAG run |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Validation rules**:
- `role` MUST be "user" or "assistant" (CHECK constraint)
- History truncation: the RAG workflow loads at most MAX_HISTORY_MESSAGES (config,
  default 20) messages per conversation to prevent unbounded LLM context growth

---

## Table: `rag_runs`

A complete trace record for a single query execution. Persisted after every chat request.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | Also used as the SSE stream request_id |
| `conversation_id` | UUID | FK → conversations.id, NULLABLE | |
| `request_id` | VARCHAR(64) | NOT NULL, UNIQUE | Client-visible request identifier |
| `trace_id` | VARCHAR(128) | NULLABLE | LangSmith or external trace ID |
| `query` | TEXT | NOT NULL | Original user query |
| `rewritten_queries` | JSONB | NULLABLE | List of rewritten queries |
| `intent` | VARCHAR(64) | NULLABLE | Classified intent |
| `domain` | VARCHAR(64) | NULLABLE | Classified domain |
| `retrieval_mode` | VARCHAR(32) | NULLABLE | dense\|sparse\|hybrid |
| `reranker` | VARCHAR(64) | NULLABLE | bge\|cohere\|none |
| `retrieved_chunk_ids` | UUID[] | NULLABLE | Dense + sparse candidates |
| `selected_chunk_ids` | UUID[] | NULLABLE | Context-selected chunks |
| `retrieval_scores` | JSONB | NULLABLE | Per-chunk scores at each stage |
| `context_token_count` | INTEGER | NULLABLE | |
| `llm_model` | VARCHAR(128) | NULLABLE | |
| `input_token_count` | INTEGER | NULLABLE | |
| `output_token_count` | INTEGER | NULLABLE | |
| `generation_latency_ms` | INTEGER | NULLABLE | |
| `total_latency_ms` | INTEGER | NULLABLE | |
| `citation_validation_result` | VARCHAR(32) | NULLABLE | passed\|failed\|skipped |
| `groundedness_result` | VARCHAR(32) | NULLABLE | grounded\|abstained\|qualified |
| `guardrail_result` | VARCHAR(32) | NULLABLE | passed\|blocked |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | |
| `final_answer_status` | VARCHAR(32) | NULLABLE | success\|abstention\|error |
| `error_detail` | TEXT | NULLABLE | Internal error (not user-facing) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

## Table: `evaluation_datasets`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | VARCHAR(256) | NOT NULL | e.g. "hr-golden-v1" |
| `description` | TEXT | NULLABLE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

## Table: `evaluation_cases`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `dataset_id` | UUID | FK → evaluation_datasets.id, NOT NULL | |
| `question` | TEXT | NOT NULL | HR question |
| `expected_answer` | TEXT | NULLABLE | Reference answer or evaluation criteria |
| `relevant_document_ids` | UUID[] | NULLABLE | Expected document sources |
| `relevant_chunk_ids` | UUID[] | NULLABLE | Expected chunk sources |
| `category` | VARCHAR(128) | NULLABLE | leave_policy, abstention, injection, etc. |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | |

## Table: `evaluation_results`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `evaluation_case_id` | UUID | FK → evaluation_cases.id, NOT NULL | |
| `rag_run_id` | UUID | FK → rag_runs.id, NOT NULL | The run that produced this result |
| `retrieval_metrics` | JSONB | NOT NULL | recall_at_k, precision_at_k, mrr, ndcg_at_k |
| `generation_metrics` | JSONB | NOT NULL | faithfulness, citation_correctness, abstention_quality |
| `latency_metrics` | JSONB | NOT NULL | total_ms, retrieval_ms, reranker_ms, generation_ms |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

## LangGraph State: `RAGState`

```python
class RAGState(TypedDict):
    # Request context
    conversation_id: Optional[str]
    request_id: str
    trace_id: Optional[str]
    original_query: str
    conversation_history: List[Dict[str, str]]   # truncated to MAX_HISTORY_MESSAGES

    # Query processing
    intent: Optional[str]          # hr_question | greeting | out_of_domain
    domain: Optional[str]          # hr | unknown
    rewritten_queries: List[str]
    filters: Dict[str, Any]        # extracted HR metadata filters

    # Retrieval
    retrieved_candidates: List[ChunkCandidate]
    fused_candidates: List[ChunkCandidate]
    reranked_candidates: List[ChunkCandidate]
    selected_context: List[ChunkCandidate]
    retrieval_quality: Optional[str]   # sufficient | poor | empty

    # Generation
    draft_answer: Optional[str]
    citations: List[Citation]
    groundedness_result: Optional[str]   # grounded | abstained | qualified
    guardrail_result: Optional[str]      # passed | blocked

    # Control
    retry_count: int
    final_answer: Optional[str]
    final_answer_status: Optional[str]   # success | abstention | error
    error_detail: Optional[str]
```

---

## Configuration Keys (env vars mapped to Pydantic Settings)

| Key | Default | Description |
|-----|---------|-------------|
| `DENSE_TOP_K` | 30 | Dense retrieval candidates |
| `SPARSE_TOP_K` | 30 | Sparse retrieval candidates |
| `FUSION_TOP_K` | 50 | RRF output size |
| `RERANK_TOP_K` | 10 | Reranker input size |
| `FINAL_CONTEXT_CHUNKS` | 5 | Chunks passed to LLM |
| `MAX_RETRIEVAL_RETRIES` | 2 | Hard retry loop cap |
| `MAX_HISTORY_MESSAGES` | 20 | Conversation history window |
| `MAX_FILE_SIZE_MB` | 50 | Upload size limit |
| `RERANKER_PROVIDER` | bge | bge \| cohere \| none |
| `EMBEDDING_PROVIDER` | openai | openai \| huggingface \| sentence_transformers |
| `TARGET_CHUNK_TOKENS` | 512 | Target chunk size |
| `CHUNK_OVERLAP_TOKENS` | 80 | Chunk overlap |
