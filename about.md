# 📘 About This Project — HR RAG Knowledge Assistant

A deep-dive technical walkthrough of every layer of this system — what it does, why we built it this way, and how all the pieces connect.

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Frontend — How the UI Works](#2-frontend--how-the-ui-works)
3. [RAG Pipeline — The Brain of the System](#3-rag-pipeline--the-brain-of-the-system)
4. [Backend — FastAPI Server](#4-backend--fastapi-server)
5. [Jenkins CI/CD — Automated Quality Gates](#5-jenkins-cicd--automated-quality-gates)
6. [Docker & Kubernetes — Container Strategy](#6-docker--kubernetes--container-strategy)
7. [MCP Server — AI Tool Protocol](#7-mcp-server--ai-tool-protocol)

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                 │
│              React 18 + Vite + TypeScript + TailwindCSS              │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  HTTP POST + SSE Stream
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        NGINX (port 80/3000)                          │
│   Serves static React files + proxies /api/* → backend:8000          │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (port 8000)                        │
│  ┌──────────────┐   ┌───────────────────┐   ┌────────────────────┐  │
│  │  Ingestion   │   │  LangGraph RAG    │   │  Guardrails Layer  │  │
│  │  Pipeline    │   │  (13-node graph)  │   │  (PII + Domain)    │  │
│  └──────┬───────┘   └────────┬──────────┘   └────────────────────┘  │
└─────────│───────────────────│──────────────────────────────────────┘
          │                   │
          ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│              POSTGRESQL 16 + pgvector extension                       │
│    documents table  │  document_chunks  │  vector embeddings (768d)  │
└──────────────────────────────────────────────────────────────────────┘

     LLM: Gemini 1.5 Flash    Embeddings: Gemini text-embedding-004
     Reranker: BGE-reranker-v2-m3 (local model, no API call needed)
```

---

## 2. Frontend — How the UI Works

### Component Architecture

```
App.tsx
 ├── Header.tsx          ← Title bar + Upload button trigger
 ├── Sidebar.tsx         ← Conversation history list (past chats)
 ├── MessageList.tsx     ← Scrollable list of all chat messages
 │    └── MessageBubble.tsx  ← Single user/bot message with citations
 ├── CitationPanel.tsx   ← Slide-in panel showing source documents
 ├── ChatInput.tsx       ← Text box + Send button + Stop button
 ├── DocumentModal.tsx   ← File upload modal (drag & drop)
 └── EmptyState.tsx      ← "Ask me anything about HR" placeholder
```

### Custom Hooks (State Logic)

```
useDocuments.ts          useChat.ts (inferred)
   │                        │
   ├── fetchDocuments()     ├── streamChat()      ← calls SSE stream
   ├── uploadFiles()        ├── stopStreaming()   ← abort controller
   └── deleteDocument()     └── handleCitations() ← updates UI
```

### How a Chat Message Flows Through the Frontend

```
1. USER TYPES a question and hits Send
        │
        ▼
2. ChatInput.tsx calls api.streamChat(query, conversationId, callbacks)
        │
        ▼
3. api.ts opens a FETCH request to POST /api/v1/chat/stream
   ↳ Response is a raw ReadableStream (SSE)
        │
        ▼
4. api.ts reads chunks in a WHILE LOOP:
   reader.read() → decode bytes → split on "\n\n" → parse JSON
        │
        ├── data.type === "token"      → onToken()  → appends to message bubble word-by-word
        ├── data.type === "citations"  → onCitations() → shows source docs panel
        ├── data.type === "done"       → onDone()   → shows latency badge
        ├── data.type === "abstention" → onAbstention() → shows "I can't answer that"
        └── data.type === "error"      → onError()  → shows error message
        │
        ▼
5. MessageBubble.tsx renders the streaming text character-by-character
   CitationPanel.tsx shows the source chunks with page numbers
```

### Why SSE (Server-Sent Events) instead of WebSockets?

| SSE | WebSocket |
|---|---|
| One-directional (server → client) | Bi-directional |
| Works over plain HTTP/1.1 | Requires upgrade handshake |
| Simpler, auto-reconnects | More complex |
| ✅ Perfect for streaming LLM tokens | Overkill for this use case |

### Document Upload Flow

```
User drags file into DocumentModal.tsx
        │
        ▼
api.uploadDocuments(files) → FormData POST /api/v1/documents/upload
        │
        ▼
Backend ingestion pipeline runs (async):
  PDF/DOCX/XLSX → parse → chunk (512 tokens) → embed → store in pgvector
        │
        ▼
useDocuments.fetchDocuments() refreshes the document list automatically
```

---

## 3. RAG Pipeline — The Brain of the System

### What is RAG and Why Do We Use It?

**Problem:** A plain LLM like Gemini doesn't know your company's specific HR policies. If you ask "What is our leave policy?", it will hallucinate a generic answer.

**Solution — RAG (Retrieval-Augmented Generation):**
1. Pre-load company HR documents into a searchable database
2. When user asks a question → FIND the relevant document chunks first
3. Feed those chunks as context to the LLM → LLM answers using REAL company data
4. Cite exactly which document the answer came from

**Advantage:** The LLM never makes up policies. It can only answer based on what's in your uploaded documents. If the answer isn't in any document, it says "I don't know."

---

### Our LangGraph RAG Pipeline — 13 Nodes

```
                    USER QUERY
                        │
                        ▼
              ┌─────────────────────┐
              │  1. validate_request │  ← Check query not empty/too long
              └─────────┬───────────┘
                        │
                        ▼
              ┌──────────────────────────────┐
              │  2. load_conversation_context │  ← Load last N messages from DB
              └─────────┬────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  3. classify_intent  │  ← Gemini classifies the query intent
              └─────────┬───────────┘
                        │
          ┌─────────────┼──────────────────┐
          │             │                  │
          ▼             ▼                  ▼
    "greeting"    "hr_question"    "injection_attempt"
          │             │                  │
          ▼             ▼                  ▼
    Respond         Continue          handle_abstention
    directly           │               (block it)
                       │
                       ▼
              ┌─────────────────────┐
              │  4. process_query    │  ← Query rewriting + domain filter
              └─────────┬───────────┘     ("leave" | "benefits" | "wfh")
                        │
                        ▼
              ┌──────────────────────────┐
              │  5. retrieve_candidates   │  ← HYBRID SEARCH (see below)
              └─────────┬────────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │  6. fuse_and_rerank   │  ← RRF fusion + BGE reranker
              └─────────┬────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  7. select_context   │  ← Pick top 5 chunks
              └─────────┬───────────┘
                        │
              ┌─────────┴──────────┐
              │ Enough context?     │
              │                     │
           YES│                  NO │
              ▼                     ▼
   ┌──────────────────────┐    handle_abstention
   │ 8. generate_draft    │    "I don't have enough info"
   │    _answer           │
   └─────────┬────────────┘
             │
             ▼
   ┌──────────────────────┐
   │  9. extract_citations │  ← Link answer sentences to source chunks
   └─────────┬────────────┘
             │
             ▼
   ┌───────────────────────────┐
   │ 10. validate_groundedness  │  ← Is the answer supported by sources?
   └─────────┬─────────────────┘
             │
   ┌─────────┴──────────┐
   │ Grounded?           │
   │                     │
 YES│                 NO │
   ▼                     ▼
   ┌────────────────┐    handle_abstention
   │ 11. apply_      │    "Answer not supported by docs"
   │    guardrails   │  ← Strip salary numbers, PII redaction
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────────┐
   │ 12. format_final_       │  ← Package: answer + citations + metadata
   │     response            │
   └─────────────────────────┘
            │
            ▼
       STREAM TO USER (SSE)
```

### Why 13 Nodes? Why Not Just "Ask Gemini Directly"?

| Simple LLM Call | Our 13-Node RAG Pipeline |
|---|---|
| Hallucinated answers | Only answers from real documents |
| No citations | Shows exact source + page number |
| No domain control | Blocks off-topic / HR-only |
| No safety checks | Strips salary data, blocks injection |
| Retries on failure? No | Auto-retry with rephrased query |
| Context from history? No | Loads last 20 messages |

---

### Hybrid Retrieval — Why We Use TWO Search Methods

When you ask "what is the maternity leave policy?", we run TWO searches simultaneously:

```
USER QUERY: "maternity leave policy"
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
  DENSE SEARCH (pgvector)              SPARSE SEARCH (tsvector)
  ─────────────────────────            ────────────────────────
  Convert query to 768-dim             PostgreSQL full-text search
  vector via Gemini embedding          BM25-style keyword matching
  
  Finds semantically similar           Finds documents with exact
  docs even if different words:        keyword matches:
  "parental benefit" matches           "maternity" "leave" "policy"
  "maternity leave"                    must appear in document
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
              RECIPROCAL RANK FUSION (RRF)
              ─────────────────────────────
              Merges both result lists using
              the formula: score = Σ 1/(rank + 60)
              Documents appearing in BOTH lists
              get boosted scores
                        │
                        ▼
              BGE RERANKER (local ML model)
              ─────────────────────────────
              Cross-encoder model re-scores
              each candidate against the query
              Much more accurate than embedding
              similarity alone
                        │
                        ▼
              TOP 5 CHUNKS → fed to Gemini
```

**Why Hybrid?**
- Dense alone misses exact keyword matches ("policy number BEN-2024")
- Sparse alone misses semantic meaning ("parental benefit" ≠ "maternity leave")
- Together they cover both — consistently better results

---

## 4. Backend — FastAPI Server

### Folder Structure and What Each Layer Does

```
backend/app/
├── api/v1/          ← HTTP Endpoints (the public interface)
│   ├── chat.py      ← POST /chat/stream → runs RAG pipeline → SSE stream
│   ├── documents.py ← POST /upload, GET /documents, DELETE /documents/{id}
│   ├── health.py    ← GET /health, GET /ready (Kubernetes probes)
│   ├── conversations.py  ← GET/DELETE conversation history
│   ├── suggestions.py    ← GET suggested questions
│   └── knowledge_base.py ← GET stats (chunk count, doc count)
│
├── workflows/       ← LangGraph RAG graph (the 13 nodes described above)
│   ├── rag_graph.py ← Wires all nodes into a StateGraph
│   ├── graph_state.py ← RAGState TypedDict (shared state across all nodes)
│   └── nodes/       ← One file per node (validate, classify, retrieve, etc.)
│
├── retrieval/       ← Search engine layer
│   ├── hybrid_retriever.py  ← Runs dense + sparse searches
│   ├── fusion.py           ← Reciprocal Rank Fusion algorithm
│   ├── bge_reranker.py     ← BGE cross-encoder reranker (local)
│   ├── cohere_reranker.py  ← Cohere API reranker (optional)
│   └── embedding_factory.py ← Creates the right embedding provider
│
├── ingestion/       ← Document processing pipeline
│   ├── parsers/     ← PDF→text, DOCX→text, XLSX→rows
│   └── chunker.py   ← Splits text into 512-token overlapping chunks
│
├── models/          ← SQLAlchemy ORM (database table definitions)
│   ├── document.py  ← documents table
│   ├── chunk.py     ← document_chunks table + vector column
│   └── conversation.py ← conversations + messages tables
│
├── guardrails/      ← Safety layer
│   ├── domain_filter.py   ← Blocks non-HR questions
│   ├── injection_guard.py ← Detects prompt injection attempts
│   └── pii_redactor.py    ← Masks salary numbers, personal data
│
├── config/
│   ├── settings.py  ← Reads all env vars (GEMINI_API_KEY, DB URL, etc.)
│   └── logging.py   ← Structured JSON logging with request/trace IDs
│
├── init_db.py       ← Creates all DB tables + pgvector extension on startup
└── main.py          ← FastAPI app: mounts routers, lifespan, CORS, error handlers
```

### Document Ingestion Flow

```
User uploads "leave_policy.pdf"
        │
        ▼
POST /api/v1/documents/upload
        │
        ▼
Parse PDF using pdfplumber
→ Extract text page by page, preserve tables
        │
        ▼
Chunker splits into 512-token chunks
with 80-token overlap (so context isn't lost at boundaries)
        │
        ▼
For each chunk:
  Gemini text-embedding-004 → 768-dimension vector
        │
        ▼
Store in PostgreSQL:
  document_chunks table:
    id, content, page_number, section,
    embedding (vector(768)),   ← pgvector column
    tsvector_content           ← full-text search index
        │
        ▼
Document available for search immediately
```

---

## 5. Jenkins CI/CD — Automated Quality Gates

### What is Jenkins and Why Use It?

Without CI/CD, the deployment process is:
1. Developer writes code
2. Developer manually runs tests
3. Developer manually builds Docker images
4. Developer manually deploys to Kubernetes
5. Something breaks because step 2 was skipped 😬

With Jenkins, every `git push` to `main` automatically runs everything — no human error.

### Pipeline Flow (5 Stages)

```
git push → GitHub
      │
      │  (Jenkins polls GitHub every 5 min OR via webhook)
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 1: CHECKOUT                                   │
│  Jenkins fetches latest code from GitHub (main)      │
│  Creates a fresh workspace in the Jenkins container  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 2: LINT & TYPE CHECK (runs in PARALLEL)       │
│                                                      │
│  Backend (simultaneous):    Frontend (simultaneous): │
│  ─────────────────────      ──────────────────────── │
│  pip install ruff mypy      npm ci                   │
│  ruff check .               npm run lint             │
│  mypy app/                                           │
│                                                      │
│  Catches: unused imports,   Catches: TypeScript       │
│  wrong types, code style    errors, ESLint rules     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 3: TEST (via deployment/jenkins/test.sh)      │
│                                                      │
│  Backend:                   Frontend:                │
│  ──────────────────         ────────────────────     │
│  pip install pytest         npm ci                   │
│  pytest tests/unit/ -v      npm run build            │
│                             (tsc + vite build)       │
│                                                      │
│  Tests: health endpoints,   Tests: TypeScript        │
│  embedding logic, DB ops    compiles cleanly,        │
│                             Vite bundles correctly   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 4: BUILD DOCKER IMAGES (runs in PARALLEL)     │
│                                                      │
│  docker build → hr-rag-backend:abc1234               │
│  docker build → hr-rag-frontend:abc1234              │
│                                                      │
│  Tagged with git short SHA (e.g., abc1234) so        │
│  every build is traceable to an exact commit         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 5: DEPLOY TO STAGING (Kubernetes)             │
│                                                      │
│  kubectl apply all manifests in order:               │
│    1. namespace.yaml     ← create hr-rag namespace   │
│    2. configmap.yaml     ← env vars (non-secret)     │
│    3. postgres.yaml      ← PostgreSQL StatefulSet    │
│    4. backend-deployment ← 2 replicas of backend     │
│    5. frontend-deployment← 2 replicas of frontend    │
│    6. ingress.yaml       ← HTTP routing rules        │
│                                                      │
│  Then waits for rollout:                             │
│    kubectl rollout status ← confirms pods are Ready  │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  POST ACTIONS   │
              │  always: cleanWs│  ← Delete workspace files
              │  success: echo  │  ← "Pipeline succeeded: abc1234"
              │  failure: echo  │  ← "Pipeline failed!"
              └─────────────────┘
```

---

## 6. Docker & Kubernetes — Container Strategy

### Why Docker?

Without Docker, running this on any machine requires:
- Install Python 3.12
- Install Node 20
- Install PostgreSQL 16
- Install pgvector extension
- Set up all environment variables
- ...different on every OS

With Docker:
```
docker-compose up
```
Everything runs the same everywhere.

### Two Ways to Run the Stack

#### Mode A: Docker Compose (Development / Demo)

```
docker-compose up --build
        │
        ├── hr-rag-postgres container   (pgvector/pgvector:pg15 image)
        │   port: 5432
        │
        ├── hr-rag-backend container    (built from backend/Dockerfile)
        │   port: 8000
        │   uses nginx.compose.conf for Docker DNS (127.0.0.11)
        │
        └── hr-rag-frontend container   (built from frontend/Dockerfile)
            port: 3000 → 80 (Nginx serves React + proxies /api/)
```

#### Mode B: Kubernetes (Production-like, local via Docker Desktop)

```
Docker Desktop Kubernetes
  └── Namespace: hr-rag
        │
        ├── StatefulSet: hr-rag-postgres   (1 pod + PVC for data)
        │   Service: ClusterIP :5432
        │
        ├── Deployment: hr-rag-backend     (2 replicas)
        │   Service: ClusterIP :8000
        │   ConfigMap: env vars            ← configmap.yaml
        │   Secret: API keys               ← secret.yaml (gitignored)
        │   LivenessProbe:  GET /api/v1/health
        │   ReadinessProbe: GET /api/v1/ready
        │   HPA: auto-scale 2-10 pods based on CPU
        │
        ├── Deployment: hr-rag-frontend    (2 replicas)
        │   Service: ClusterIP :80
        │   uses nginx.conf (K8s DNS: 10.96.0.10)
        │
        └── Ingress: routes external traffic to services
```

### Why 2 Replicas of Backend and Frontend?

```
USER REQUEST
     │
     ▼
Kubernetes Load Balancer
     │
     ├──► hr-rag-backend pod 1  (if one crashes, traffic reroutes)
     └──► hr-rag-backend pod 2  (zero downtime)

If pod 1 crashes → Kubernetes auto-restarts it
Meanwhile pod 2 serves all traffic → no downtime for users
```

### Dockerfile Strategy — Multi-stage Build

```
backend/Dockerfile:

  Stage 1 (builder):         Stage 2 (runtime):
  ─────────────────          ──────────────────
  python:3.12-slim           python:3.12-slim (fresh)
  Install build tools        Only copy installed packages
  pip install all deps       Copy app code
  Build wheels               No build tools = smaller image
  
  ~2GB (with build tools)    ~800MB (runtime only)
```

---

## 7. MCP Server — AI Tool Protocol

### What is MCP?

**Model Context Protocol (MCP)** is an open protocol (by Anthropic) that lets AI assistants (like Claude, Gemini, or custom agents) call external tools in a standardized way.

Think of it like a USB standard — instead of every AI needing a custom plugin for every tool, MCP provides one universal plug format.

```
Without MCP:                    With MCP:
───────────────                 ─────────────────────────────────
Claude plugin A  ─┐             Any MCP-compatible AI client
GPT plugin B     ─┤ custom ──►  ─────────────────────────────────
Gemini plugin C  ─┘ code each   connects to our MCP server
                                and instantly has access to:
                                  ✅ list_uploaded_documents()
                                  ✅ read_document_excerpt()
```

### Our MCP Implementation

```
backend/app/mcp/
├── server.py   ← FastAPI router that exposes MCP-compatible endpoints
└── tools.py    ← The actual tool implementations:

    HRDocumentMCPTools:
    
    list_uploaded_documents()
    ─────────────────────────
    Scans storage/uploads/ directory
    Returns: [{file_name, file_size, path}, ...]
    
    read_document_excerpt(file_name, max_chars=2000)
    ────────────────────────────────────────────────
    Safely reads first 2000 chars of any uploaded file
    Has directory traversal protection (os.path.basename)
    Returns: {file_name, excerpt}
```

### How Could Claude Use This?

```
Claude Desktop (with MCP configured):
         │
         │ "What HR documents are available?"
         │
         ▼
    MCP client calls: list_uploaded_documents()
         │
         ▼
    Our server returns: ["leave_policy.pdf", "benefits_2024.xlsx", ...]
         │
         ▼
    Claude: "I can see you have these HR documents:
             1. leave_policy.pdf
             2. benefits_2024.xlsx
             Would you like me to search any of them?"
```

### Enable MCP (currently disabled by default)

```env
# In .env file:
MCP_ENABLED=true
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8001
```

Then configure Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "hr-rag": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

---

## Summary — Why Each Technology Was Chosen

| Technology | Why We Chose It |
|---|---|
| **FastAPI** | Async-native, auto Swagger docs, fast, type-safe with Pydantic |
| **LangGraph** | Stateful multi-step agent with conditional branching — not possible with simple chains |
| **pgvector** | Vector search inside the same PostgreSQL DB — no separate vector DB needed |
| **Hybrid Search (Dense + Sparse)** | Better recall than either alone — catches both semantic and keyword matches |
| **BGE Reranker** | Local cross-encoder, no API cost, significantly improves precision |
| **Gemini** | Generous free tier, fast responses, good instruction following |
| **SSE Streaming** | Users see the answer appear word-by-word — feels instant, better UX |
| **React + Vite** | Fast build, TypeScript safety, excellent DX |
| **Docker Compose** | Zero-config local setup — one command starts everything |
| **Kubernetes** | Production resilience — auto-restart, load balancing, HPA scaling |
| **Jenkins** | Self-hosted CI/CD — full control, runs locally, no cloud dependency |
| **MCP** | Future-proof — any MCP-compatible AI agent can use our RAG system |
