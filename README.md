# 🤖 HR Knowledge Assistant — RAG Chatbot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/LangGraph-Agentic_RAG-orange" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-336791?logo=postgresql" />
  <img src="https://img.shields.io/badge/Kubernetes-Docker_Desktop-326CE5?logo=kubernetes" />
  <img src="https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?logo=jenkins" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

> **Enterprise-grade HR Knowledge Assistant** powered by Hybrid Retrieval-Augmented Generation (RAG), LangGraph agentic workflows, Gemini LLM, pgvector semantic search, and a full Kubernetes + Jenkins CI/CD pipeline.

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Quick Start (Local Dev)](#-quick-start-local-dev)
- [🐳 Docker Compose](#-docker-compose)
- [⚙️ Configuration](#️-configuration)
- [☸️ Kubernetes Deployment](#️-kubernetes-deployment)
- [🔧 Jenkins CI/CD Pipeline](#-jenkins-cicd-pipeline)
- [📡 API Reference](#-api-reference)
- [🧪 Testing](#-testing)
- [🗂️ Database & Migrations](#️-database--migrations)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Hybrid Retrieval** | Dense pgvector + Sparse PostgreSQL tsvector + Reciprocal Rank Fusion (RRF) |
| 🧠 **Agentic RAG Pipeline** | LangGraph state machine: intent classification → retrieval → grading → self-correction → generation |
| 📄 **Multi-format Ingestion** | PDF, DOCX, XLSX, TXT, MD, CSV with table and structure preservation |
| 🛡️ **HR Guardrails** | Anti-prompt injection, salary PII redaction, domain enforcement |
| 🎯 **Reranking** | Optional (configurable: none / BGE / Cohere; defaults to `none` for fast latency) |
| 📊 **Hallucination Checks** | Faithfulness scoring and answer relevance validation before response |
| 💬 **Streaming UI** | React 18 + Vite + Server-Sent Events (SSE) streaming chat |
| 📌 **Citations** | Source citations with document name, page, and confidence badges |
| 🔭 **Observability** | Structured structlog logging + optional LangSmith tracing |
| 🔌 **MCP Server** | Optional Model Context Protocol (MCP) server endpoint |
| ⚕️ **Health & Readiness** | `/api/v1/health` and `/api/v1/ready` probes for Kubernetes |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite)                    │
│              Streaming Chat  │  Document Upload  │  History      │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTP / SSE
┌────────────────────────▼────────────────────────────────────────┐
│                     FastAPI Backend (Python 3.12)               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Ingestion  │  │  RAG Agent   │  │   Guardrails Layer   │   │
│  │  Pipeline   │  │  (LangGraph) │  │   (HR Domain only)   │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────────────────┘   │
│         │                │                                       │
│  ┌──────▼────────────────▼──────────────────────────────────┐   │
│  │              Hybrid Retrieval Engine                      │   │
│  │  Dense Search (pgvector) + Sparse (tsvector BM25)        │   │
│  │      Reciprocal Rank Fusion (RRF)                        │   │
│  └──────────────────────┬───────────────────────────────────┘   │
└─────────────────────────│───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│         PostgreSQL 16 + pgvector Extension                      │
│   document_chunks table  │  1536-dimensional float vectors      │
└─────────────────────────────────────────────────────────────────┘

         LLM: Google Gemini 2.5 Flash
         Embeddings: Google gemini-embedding-002 (1536 dimensions)
         Reranker: None (direct Reciprocal Rank Fusion)
```

### LangGraph RAG Workflow

```
User Query
    │
    ▼
Query Rewriting ──► Intent Classification
                            │
            ┌───────────────┴───────────────┐
            │                               │
      HR Domain?                     Out-of-scope?
            │                               │
            ▼                               ▼
    Hybrid Retrieval              Polite Rejection
     (Dense + Sparse)
            │
            ▼
    Document Grading
    (Relevance check)
            │
       Enough docs?
       ┌────┴────┐
      NO        YES
       │          │
       ▼          ▼
  Retry/Rephrase  Hallucination Check
                       │
                  Faithful?
                  ┌─────┴─────┐
                 NO           YES
                  │             │
                  ▼             ▼
             Re-generate   Stream Answer + Citations
```

---

## 🧰 Tech Stack

### Backend

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.111+ with async support |
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Google gemini-embedding-002 (1536 dimensions) |
| Agent Orchestration | LangGraph, LangChain |
| Vector Database | PostgreSQL 16 + pgvector extension |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic |
| Reranker | Optional (`none` / BGE-reranker-v2-m3 / Cohere) |
| Document Parsing | pdfplumber, python-docx, openpyxl, pandas |
| Logging | structlog (structured JSON logs) |
| Tracing | LangSmith (optional) |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Styling | TailwindCSS |
| HTTP / Streaming | Fetch API with SSE streaming |
| Production Server | Nginx Alpine with dynamic DNS resolver |

### Infrastructure & DevOps

| Component | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes (Docker Desktop local cluster) |
| CI/CD | Jenkins (Docker-based, local) |
| Lint / Type Check | Ruff, mypy (backend) · ESLint, TypeScript (frontend) |
| Tests | pytest + pytest-asyncio + pytest-cov |

---

## 📁 Project Structure

```
rag-system/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/             # Route handlers (chat, documents, health, …)
│   │   ├── config/             # Settings & logging config
│   │   ├── guardrails/         # HR domain guardrails & PII filters
│   │   ├── ingestion/          # Document parsers & chunk pipeline
│   │   ├── mcp/                # Model Context Protocol server
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # DB access layer
│   │   ├── retrieval/          # Hybrid search engine + reranker
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic
│   │   ├── workflows/          # LangGraph RAG pipeline
│   │   ├── init_db.py          # Auto schema initializer on startup
│   │   └── main.py             # FastAPI app entry point & lifespan
│   ├── tests/                  # pytest unit & integration tests
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/         # UI components (Chat, Upload, Citations…)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client + SSE streaming
│   │   └── types/              # TypeScript interfaces
│   ├── nginx.conf              # Production Nginx config with dynamic DNS
│   ├── Dockerfile
│   └── package.json
│
├── database/
│   └── migrations/             # Alembic migration scripts
│
├── deployment/
│   ├── jenkins/
│   │   ├── Jenkinsfile         # Full CI/CD pipeline definition
│   │   ├── Dockerfile.jenkins  # Jenkins image with Docker + kubectl
│   │   ├── test.sh             # Automated test runner script
│   │   └── docker-compose.jenkins.yml
│   └── kubernetes/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secret.example.yaml # Template — copy & fill values
│       ├── postgres.yaml       # StatefulSet + PVC for PostgreSQL
│       ├── backend-deployment.yaml
│       ├── frontend-deployment.yaml
│       ├── ingress.yaml
│       └── hpa.yaml            # Horizontal Pod Autoscaler
│
├── docs/                       # Architecture diagrams & design docs
├── evaluation/                 # RAG evaluation scripts
├── docker-compose.yml          # Full local stack via Docker Compose
├── .env.example                # Environment variable template
└── README.md
```

---

## 🚀 Quick Start (Local Dev)

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 with the `pgvector` extension enabled
- Google Gemini API key — [Get one free here](https://aistudio.google.com/)

### 1. Clone & configure

```bash
git clone https://github.com/Nikhil181511/Rag-chatbot-for-hr.git
cd rag-system
cp .env.example .env
# Open .env and fill in your GEMINI_API_KEY and DB credentials
```

### 2. Start the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

- API server: **http://localhost:8000**
- Swagger docs: **http://localhost:8000/docs**

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: **http://localhost:3000**

---

## 🐳 Docker Compose

Run the entire stack (PostgreSQL + backend + frontend) locally with one command:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure the key variables:

```env
# LLM
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpassword
POSTGRES_DB=hr_rag_db

# Embedding
EMBEDDING_PROVIDER=gemini          # gemini | openai
EMBEDDING_MODEL=gemini-embedding-002
EMBEDDING_DIMENSION=1536

# Reranker
RERANKER_PROVIDER=none             # none | bge | cohere

# Retrieval tuning
DENSE_TOP_K=30
SPARSE_TOP_K=30
RERANK_TOP_K=10
FINAL_CONTEXT_CHUNKS=5

# Observability (optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` configured and pointing to your local cluster

### 1. Create your secrets file

```bash
cp deployment/kubernetes/secret.example.yaml deployment/kubernetes/secret.yaml
# Edit secret.yaml — set GEMINI_API_KEY, POSTGRES_USER, POSTGRES_PASSWORD
kubectl apply -f deployment/kubernetes/secret.yaml
```

> ⚠️ **Never commit `secret.yaml` with real keys.** It is listed in `.gitignore`.

### 2. Build Docker images

```bash
docker build -t hr-rag-backend:latest -f backend/Dockerfile backend/
docker build -t hr-rag-frontend:v1    -f frontend/Dockerfile frontend/
```

### 3. Apply all manifests

```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/postgres.yaml
kubectl apply -f deployment/kubernetes/backend-deployment.yaml
kubectl apply -f deployment/kubernetes/frontend-deployment.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml
```

### 4. Verify pods are running

```bash
kubectl get pods -n hr-rag
```

Expected output:

```
NAME                               READY   STATUS    RESTARTS   AGE
hr-rag-backend-xxx-aaa             1/1     Running   0          2m
hr-rag-backend-xxx-bbb             1/1     Running   0          2m
hr-rag-frontend-xxx-aaa            1/1     Running   0          1m
hr-rag-frontend-xxx-bbb            1/1     Running   0          1m
hr-rag-postgres-0                  1/1     Running   0          5m
```

### 5. Access the frontend

```bash
kubectl port-forward svc/hr-rag-frontend 8081:80 -n hr-rag
# Open http://localhost:8081
```

---

## 🔧 Jenkins CI/CD Pipeline

The full pipeline is defined in [`deployment/jenkins/Jenkinsfile`](deployment/jenkins/Jenkinsfile).

It runs automatically on every push to the `main` branch:

| Stage | What it does |
|---|---|
| **Checkout** | Fetches latest code from GitHub `main` branch |
| **Lint & Type Check** | `ruff` + `mypy` on backend; ESLint on frontend (parallel) |
| **Test** | pytest with coverage + TypeScript build validation via `test.sh` |
| **Build Docker Images** | Builds `hr-rag-backend:latest` and `hr-rag-frontend:v1` |
| **Deploy to Staging** | Applies all Kubernetes manifests and monitors rollout health |

### Start Jenkins locally

```bash
cd deployment/jenkins
docker-compose -f docker-compose.jenkins.yml up -d
# Jenkins UI: http://localhost:8080
```

Create a **Pipeline** job in Jenkins, choose _Pipeline script from SCM_, set the repo URL and branch to `main`, and the script path to `deployment/jenkins/Jenkinsfile`.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness probe |
| `GET` | `/api/v1/ready` | Readiness probe (checks DB connectivity) |
| `POST` | `/api/v1/chat` | Send a chat message — returns SSE stream |
| `GET` | `/api/v1/conversations` | List all conversations |
| `GET` | `/api/v1/conversations/{id}` | Get conversation history |
| `POST` | `/api/v1/documents/upload` | Upload HR documents (PDF, DOCX, etc.) |
| `GET` | `/api/v1/documents` | List all ingested documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document and its chunks |
| `GET` | `/api/v1/knowledge-base/stats` | Knowledge base statistics |
| `GET` | `/api/v1/suggestions` | Get suggested questions |

Full interactive docs: **http://localhost:8000/docs**

---

## 🧪 Testing

```bash
cd backend
pip install -e ".[dev]"

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_health.py -v
```

Frontend checks:

```bash
cd frontend
npm run build   # TypeScript compile + Vite production build
npm run lint    # ESLint check
```

---

## 🗂️ Database & Migrations

The database schema is **automatically initialized** on backend startup (`app/init_db.py`). The `pgvector` extension and all required tables are created if they do not already exist.

To run Alembic migrations manually:

```bash
cd backend
alembic upgrade head                              # Apply all pending migrations
alembic revision --autogenerate -m "description" # Auto-generate a new migration
alembic downgrade -1                              # Roll back one migration
```

---

## 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/Nikhil181511">Nikhil Savita</a>
</p>
