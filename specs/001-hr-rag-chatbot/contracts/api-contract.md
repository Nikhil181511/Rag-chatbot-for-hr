# API Contract: HR Knowledge Assistant Backend

**Version**: v1 | **Base path**: `/api/v1` | **Date**: 2026-09-15

All requests and responses use `application/json` unless noted.
All endpoints include `X-Request-ID` in response headers.
Errors follow a consistent structure: `{"error": {"code": "...", "message": "..."}}`.

---

## Health

### GET /health
Returns system liveness status.

**Response 200**:
```json
{ "status": "ok", "timestamp": "2026-09-15T13:00:00Z" }
```

### GET /ready
Returns readiness: database reachable, vector index accessible.

**Response 200**:
```json
{ "status": "ready", "database": "ok", "vector_index": "ok" }
```
**Response 503** (not ready):
```json
{ "status": "not_ready", "database": "ok", "vector_index": "error", "message": "Vector index unavailable" }
```

---

## Chat

### POST /api/v1/chat
Non-streaming chat request. Returns complete answer.

**Request**:
```json
{
  "conversation_id": "uuid | null",
  "query": "What is the sick leave policy?",
  "reranker": "bge | cohere | none | null"
}
```

**Response 200**:
```json
{
  "request_id": "uuid",
  "conversation_id": "uuid",
  "answer": "According to the Employee Handbook...",
  "citations": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "document_name": "employee-handbook.pdf",
      "page_number": 12,
      "section": "Leave Policy",
      "excerpt": "Employees are entitled to..."
    }
  ],
  "is_abstention": false,
  "groundedness": "grounded",
  "latency_ms": 2340
}
```

### POST /api/v1/chat/stream
Streaming chat via SSE. See `streaming-contract.md` for event format.

**Request**: Same as POST /api/v1/chat

**Response**: `Content-Type: text/event-stream`

### DELETE /api/v1/chat/stream/{request_id}
Stop an in-progress streaming response.

**Response 204**: Generation cancelled.
**Response 404**: Request ID not found or already completed.

---

## Conversations

### POST /api/v1/conversations
Create a new conversation.

**Response 201**:
```json
{ "id": "uuid", "title": null, "created_at": "2026-09-15T..." }
```

### GET /api/v1/conversations
List all conversations, newest first.

**Response 200**:
```json
{
  "conversations": [
    { "id": "uuid", "title": "What is the leave policy?", "message_count": 4, "updated_at": "..." }
  ]
}
```

### GET /api/v1/conversations/{conversation_id}
Get a conversation with all its messages.

**Response 200**:
```json
{
  "id": "uuid",
  "title": "...",
  "messages": [
    { "id": "uuid", "role": "user", "content": "...", "created_at": "..." },
    { "id": "uuid", "role": "assistant", "content": "...", "rag_run_id": "uuid", "created_at": "..." }
  ]
}
```

### DELETE /api/v1/conversations/{conversation_id}
Delete a conversation and all its messages.

**Response 204**: Deleted.

---

## Documents

### POST /api/v1/documents/upload
Upload one or more HR documents. `multipart/form-data`.

**Form fields**:
- `files`: One or more files (required)

**Response 202** (accepted for processing):
```json
{
  "documents": [
    { "id": "uuid", "file_name": "leave-policy.pdf", "status": "PENDING", "file_size": 204800 }
  ]
}
```

**Response 400** (validation failure):
```json
{ "error": { "code": "INVALID_FILE", "message": "File type .exe is not allowed." } }
```

**Response 409** (duplicate):
```json
{ "error": { "code": "DUPLICATE_DOCUMENT", "message": "A document with this content already exists." } }
```

### GET /api/v1/documents
List all non-deleted documents.

**Response 200**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "file_name": "employee-handbook.pdf",
      "file_type": "pdf",
      "file_size": 204800,
      "status": "READY",
      "title": "Employee Handbook",
      "chunk_count": 142,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 1
}
```

### GET /api/v1/documents/{document_id}
Get a single document with its current version metadata.

### DELETE /api/v1/documents/{document_id}
Delete a document and all its chunks. Sets status to DELETED.

**Response 204**: Deleted.
**Response 409**: Document is currently being processed (cannot delete mid-processing).

### POST /api/v1/documents/{document_id}/reprocess
Trigger reprocessing. Status transitions: any → PENDING → PROCESSING → ...

**Response 202**:
```json
{ "id": "uuid", "status": "PENDING" }
```

### GET /api/v1/documents/{document_id}/status
Poll document processing status.

**Response 200**:
```json
{
  "id": "uuid",
  "status": "INDEXING",
  "error_message": null,
  "updated_at": "..."
}
```

---

## Knowledge Base

### GET /api/v1/knowledge-base/stats
Returns aggregate knowledge base statistics.

**Response 200**:
```json
{
  "document_count": 5,
  "ready_count": 4,
  "failed_count": 1,
  "total_chunks": 892,
  "last_indexed_at": "2026-09-15T..."
}
```

### GET /api/v1/knowledge-base/health
Returns index health (HNSW index reachable, tsvector index reachable).

---

## Suggestions

### GET /api/v1/suggestions?q={query}&limit=5
Returns debounced autocomplete suggestions. Minimum query length: 3 chars.

**Response 200**:
```json
{
  "suggestions": [
    "What is the annual leave entitlement?",
    "What is the leave encashment policy?"
  ]
}
```

### POST /api/v1/suggestions/generate
Generate document-derived suggestions for the empty chat state.

**Response 200**:
```json
{ "suggestions": ["What is the sick leave policy?", "What are the working hours?"] }
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE` | 400 | File type or size not allowed |
| `DUPLICATE_DOCUMENT` | 409 | Content hash collision |
| `DOCUMENT_NOT_FOUND` | 404 | Document ID does not exist |
| `DOCUMENT_PROCESSING` | 409 | Conflicting operation while processing |
| `EMPTY_KNOWLEDGE_BASE` | 422 | Query attempted with no indexed documents |
| `QUERY_TOO_LONG` | 422 | Query exceeds max input length |
| `PROVIDER_UNAVAILABLE` | 503 | LLM or reranker provider timeout |
| `INTERNAL_ERROR` | 500 | Unexpected error (details in server logs only) |
