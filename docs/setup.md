# HR Knowledge Assistant — Local Setup Guide

This guide walks you through setting up and running the HR Knowledge Assistant RAG system locally.

## Prerequisites
- Python 3.12+ (or Docker & Docker Compose)
- Node.js 20+ & npm
- PostgreSQL 15+ with pgvector extension (or via Docker)
- OpenAI API Key (or Azure OpenAI / Anthropic)

## Quick Start with Docker Compose

1. **Clone the repository and copy environment configuration**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your API keys in `.env`**:
   ```env
   LLM_API_KEY=sk-...
   LLM_MODEL=gpt-4o-mini
   EMBEDDING_PROVIDER=openai
   EMBEDDING_MODEL=text-embedding-3-small
   ```

3. **Start all services**:
   ```bash
   docker compose up --build -d
   ```

4. **Verify running services**:
   - Backend health check: `http://localhost:8000/api/v1/health`
   - Interactive Swagger API docs: `http://localhost:8000/docs`
   - Frontend Application: `http://localhost:3000`

## Manual Local Development Setup

### 1. Database Setup
Ensure PostgreSQL is running on port 5432 with pgvector:
```bash
docker run -d --name hr-rag-pg -p 5432:5432 -e POSTGRES_USER=raguser -e POSTGRES_PASSWORD=ragpassword -e POSTGRES_DB=hr_rag_db pgvector/pgvector:pg15
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix:
source .venv/bin/activate

pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.
