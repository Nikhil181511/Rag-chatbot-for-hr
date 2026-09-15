# API Reference: HR Knowledge Assistant

Base URL: `/api/v1`

## Endpoints

### 1. Health & Liveness
- `GET /api/v1/health` — Returns system liveness.
- `GET /api/v1/ready` — Returns database and pgvector readiness.

### 2. Chat & Streaming
- `POST /api/v1/chat` — Non-streaming chat request with full response JSON.
- `POST /api/v1/chat/stream` — SSE streaming chat returning `token`, `citations`, `done`, `abstention`, or `error` events.
- `DELETE /api/v1/chat/stream/{request_id}` — Stop and cancel an active generation.

### 3. Conversations
- `POST /api/v1/conversations` — Start a new conversation.
- `GET /api/v1/conversations` — List conversation history.
- `GET /api/v1/conversations/{id}` — Fetch conversation details and messages.
- `DELETE /api/v1/conversations/{id}` — Delete conversation.

### 4. Documents & Knowledge Base
- `POST /api/v1/documents/upload` — Upload multipart documents (`.pdf`, `.docx`, `.xlsx`, `.txt`, `.md`, `.csv`).
- `GET /api/v1/documents` — List all non-deleted documents.
- `GET /api/v1/documents/{id}/status` — Poll document processing state.
- `DELETE /api/v1/documents/{id}` — Delete document and cascade delete chunks.
- `POST /api/v1/documents/{id}/reprocess` — Re-index failed document.
- `GET /api/v1/knowledge-base/stats` — Total document, chunk counts and health.

### 5. Suggestions
- `GET /api/v1/suggestions?q={query}` — Autocomplete suggestions.
- `POST /api/v1/suggestions/generate` — Generate empty-state suggestion prompts.
