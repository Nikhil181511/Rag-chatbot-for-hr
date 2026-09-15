# Streaming Contract: SSE Chat Protocol

**Version**: v1 | **Date**: 2026-09-15
**Endpoint**: `POST /api/v1/chat/stream`

---

## Transport

- Protocol: HTTP/1.1 Server-Sent Events (SSE)
- Content-Type: `text/event-stream`
- Cache-Control: `no-cache`
- Connection: `keep-alive`
- Each event is a single line: `data: {JSON}\n\n`

---

## Event Types

### Token Event
Emitted once per streamed token or token batch.
```
data: {"type": "token", "content": "According to", "request_id": "uuid"}
```

### Citations Event
Emitted once, after the last token, with validated citations only.
```
data: {
  "type": "citations",
  "request_id": "uuid",
  "citations": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "document_name": "leave-policy.pdf",
      "page_number": 12,
      "section": "Annual Leave",
      "excerpt": "Employees are entitled to 20 days..."
    }
  ]
}
```

### Done Event
Signals generation is fully complete. Frontend MUST NOT show "completed" before this.
```
data: {"type": "done", "request_id": "uuid", "total_latency_ms": 2850}
```

### Abstention Event
Replaces token + done flow when the assistant cannot answer.
```
data: {
  "type": "abstention",
  "request_id": "uuid",
  "message": "I couldn't find enough information in the uploaded HR documents to answer that accurately.",
  "reason": "insufficient_context"
}
```

### Error Event
Emitted on pipeline failure. Frontend shows user-friendly error message from `message` field.
```
data: {
  "type": "error",
  "request_id": "uuid",
  "message": "The configured model provider is temporarily unavailable.",
  "code": "PROVIDER_UNAVAILABLE"
}
```

---

## Event Ordering

```
[token]* → [citations] → [done]
OR
[abstention]
OR
[token]* → [error]
```

Citations event is ALWAYS emitted before done, even if citations list is empty.
Fabricated citations are filtered before emission; the citations list may be empty.

---

## Stop Generation

To cancel an in-progress stream:
```
DELETE /api/v1/chat/stream/{request_id}
```
- Backend sets cancellation flag; SSE connection closes cleanly.
- No additional error event is emitted on user-initiated cancellation.
- Frontend preserves any tokens already received as a partial response.

---

## Frontend Implementation Notes

- Use `EventSource` for standard SSE, or `fetch` + `ReadableStream` for stop-generation support.
- Append token content incrementally to the message bubble on each `token` event.
- Only render citations after the `citations` event is received.
- Only mark the message as "complete" after the `done` event.
- On `error` event: display `message` field; do not display `code` field to the user.
- On `abstention` event: display `message` as the assistant response with a visual distinction.
- Implement connection timeout: if no event received within 30 s, show reconnection or error state.
