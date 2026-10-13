# ProofLens AI — Evidence-First Document Intelligence

ProofLens AI is a hardened, evidence-first document intelligence platform. It ingests multi-page PDF documents, indexes text with 1-based page-level provenance, performs vector similarity retrieval, and generates strictly grounded answers backed by verifiable source citations. When evidence is insufficient, it honestly abstains rather than hallucinating answers.

---

## ⚡ Core Hardened Capabilities

- **Strict Identity & Workspace Isolation**: Explicit server-side user authentication (`User` model, API keys, Bearer tokens) and workspace ownership scoping. Queries and operations fail closed with HTTP 404/401 across tenant boundaries without leaking metadata.
- **Evidence-First Ingestion**: Bounded streaming upload with strict 10MB memory-safety enforcement, `%PDF-` binary signature check, and page-by-page text extraction preserving 1-based page numbers and source provenance.
- **Dialect-Aware Vector Storage**: Production-ready for PostgreSQL with `pgvector` (`Vector(768)`) using in-database cosine distance (`<=>`), with an in-memory SQLite cosine similarity calculation for local zero-dependency development and testing.
- **Versioned Database Migrations**: Schema managed through versioned Alembic migrations (`alembic upgrade head`) with automatic SQLite foreign key cascade PRAGMAs.
- **Deterministic Multi-Stage Citation Semantics**: Clearly separates Reference Validity, Excerpt Validity, Claim Support, and Answer Sufficiency. Repaired excerpts are explicitly marked (`is_repaired=True`) and never falsely marked as verified quotes.
- **Explicit Uncertainty & Truthful Abstention**: Engages evidence guardrails (`evidence_status: "insufficient_evidence"`) when the query cannot be grounded in indexed document content.
- **Genuine RAG Evaluation Benchmark**: Zero fabricated metrics. Measures retrieval recall, citation validity, and abstention accuracy against a version-controlled 25-case benchmark corpus (`backend/tests/evaluation/dataset.json`). Unexecuted workspaces report honest 0.0 metrics.
- **Cross-Document Comparison Matrix**: Multi-document comparative analysis identifying agreements, discrepancies, and scope omissions across contracts or reports.
- **Audit Logging & Provenance**: Audit trail of queries, retrieved passages, model responses, and validated citations with true multi-document source resolution.
- **Modern Styled UI**: Fully compiled Next.js 14 App Router frontend with Tailwind CSS and responsive glassmorphic aesthetic.

---

## 🏗️ Architecture & Technology Stack

- **Backend**: Python 3.14 + FastAPI + SQLAlchemy 2.0 (asyncio) + Alembic + Pydantic v2
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + Lucide Icons
- **Database**: PostgreSQL 16 with `pgvector` (production) / SQLite fallback (local test)
- **AI & Embedding Models**:
  - Embedding: Google Gemini `models/gemini-embedding-2` (768 dimensions)
  - LLM: Google Gemini `gemini-2.5-flash`
  - Mock Provider: Deterministic 768-dim mock adapter for offline and zero-cost local testing

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+ (Python 3.14 tested and verified)
- Node.js 18+ and npm
- (Optional) Docker for PostgreSQL + pgvector

### 2. Database (Optional Docker Compose for PostgreSQL 16 + pgvector)

```bash
docker-compose up -d
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env

# Run database migrations
.\.venv\Scripts\alembic.exe upgrade head

# Run FastAPI backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API is live at:
- **API Base**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev

# Or test production build
npm run build
```

The frontend will be accessible at `http://localhost:3000`.

---

## 🧪 Running Automated Tests

Run the complete test suite (23/23 tests passing across unit, integration, isolation, and evaluation):

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -o pythonpath=backend backend/tests -v
```

### Test Coverage Highlights:
- **Authentication & Isolation (`test_auth_and_isolation.py`)**: Verifies authorized access, cross-user workspace rejection (404), cross-user document retrieval isolation, cross-user history privacy, unauthorized deletions, forged IDs, and production 401 enforcement.
- **Citation Semantics (`test_citation_semantics.py`)**: Verifies correct claims, irrelevant evidence rejection, fabricated excerpt detection (never marked as verified), repaired excerpt provenance, and truthful abstention on empty evidence.
- **RAG Evaluation Benchmarks (`test_rag_benchmarks.py`)**: Tests 25 version-controlled benchmark scenarios, proving metrics are dynamically calculated and unexecuted workspaces report honest 0.0 metrics.
- **Full End-to-End Lifecycle (`test_api_endpoints.py`)**: Validates workspace creation, bounded streaming upload, chunking, grounded Q&A, abstention, query history, summary generation, comparison matrix, and document deletion cascades.

---

## ⚙️ Environment Configuration

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime mode (`development`, `production`) | `development` |
| `DATABASE_URL` | Async database connection URL | `sqlite+aiosqlite:///./data/prooflens.db` |
| `STORAGE_DIR` | PDF file storage directory | `./data/storage` |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum PDF upload size | `10485760` (10 MB) |
| `EMBEDDING_PROVIDER` | Embedding provider (`mock`, `gemini`) | `mock` |
| `LLM_PROVIDER` | LLM generation provider (`mock`, `gemini`) | `mock` |
| `GEMINI_API_KEY` | Google Gemini API Key | `""` |
| `EMBEDDING_MODEL` | Gemini embedding model | `models/gemini-embedding-2` |
| `LLM_MODEL` | Gemini generation model | `gemini-2.5-flash` |
| `RATE_LIMIT_PER_MINUTE` | Maximum queries per minute per workspace | `15` |
| `MAX_DAILY_QUERIES` | Maximum queries per day per workspace | `200` |
