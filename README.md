# ProofLens AI — Evidence-First Document Intelligence

ProofLens AI is a high-reliability, evidence-first document intelligence platform. It ingests multi-page PDF documents, indexes text with 1-based page-level provenance, performs vector similarity retrieval, and generates strictly grounded answers backed by verifiable source citations. When evidence is insufficient, it honestly abstains rather than hallucinating answers.

---

## ⚡ Core Features

- **Evidence-First Ingestion**: PDF text extraction preserving 1-based page numbers and source provenance. Detects empty or scanned image-only PDFs without text.
- **Hierarchical Chunking**: Splits document text with paragraph and sentence priority while retaining page span boundaries and document metadata.
- **Dialect-Aware Vector Storage**: Production-ready for PostgreSQL with `pgvector` (`Vector(768)`). Includes seamless in-memory SQLite cosine similarity calculation for instant zero-dependency local development and automated testing.
- **Deterministic Citation Validation**: 5-stage verification policy matching citations to retrieved evidence passages, computing confidence scores, and validating exact quotes.
- **Explicit Uncertainty & Honest Abstention**: Automatically engages an evidence guardrail (`insufficient_evidence: true`) when the query cannot be grounded in indexed document content.
- **Discrepancy Detection**: Surfaces contradictory statements across document versions or different pages.
- **Cross-Document Comparison Matrix**: Multi-document comparative analysis identifying agreements, discrepancies, and omissions across contracts or reports.
- **Document Summaries & Suggested Inquiries**: Executive summaries and recommended questions generated on-demand.
- **Audit Logging**: Full audit trail of past queries, retrieved passages, model responses, and validated citations.
- **RAG Benchmark Evaluation Suite**: Measures retrieval recall, citation precision, abstention accuracy, and hallucination rate.

---

## 🏗️ Architecture & Technology Stack

- **Backend**: Python 3.14 + FastAPI + SQLAlchemy 2.0 (asyncio) + Pydantic v2
- **Frontend**: Next.js 14 (App Router) + TypeScript + TailwindCSS + Lucide Icons
- **Database**: PostgreSQL with `pgvector` (production) / SQLite fallback (local test)
- **AI & Embedding Models**:
  - Embedding: Google Gemini `models/gemini-embedding-2` (768 dimensions)
  - LLM: Google Gemini `gemini-2.5-flash`
  - Mock Provider: Deterministic 768-dim mock adapter for offline and zero-cost CI testing

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+ (Python 3.14 supported)
- Node.js 18+ and npm
- (Optional) PostgreSQL with pgvector extension enabled

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (or copy from .env.example)
copy .env.example .env

# Run FastAPI backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be live at:
- **API Base**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

The frontend will be accessible at:
- **Web App**: `http://localhost:3000`

---

## 🧪 Running Automated Tests

Run the complete backend test suite (including vector similarity, RAG pipeline, and API routers):

```bash
cd backend
.venv\Scripts\python.exe -m pytest -o pythonpath=backend backend/tests -v
```

All 11 automated test suites run completely offline using deterministic test adapters with **zero external API calls or paid credentials required**.

---

## ⚙️ Environment Configuration

Backend environment variables in `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./test_prooflens.db` | PostgreSQL connection string (`postgresql+asyncpg://...`) or SQLite URL |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key. If unset, deterministic mock adapter is used automatically |
| `EMBEDDING_PROVIDER` | `gemini` | `gemini` or `mock` |
| `LLM_PROVIDER` | `gemini` | `gemini` or `mock` |
| `EMBEDDING_MODEL` | `models/gemini-embedding-2` | Gemini embedding model |
| `LLM_MODEL` | `gemini-2.5-flash` | Gemini generation model |
| `EMBEDDING_DIMENSIONS` | `768` | Dimension count for vector embeddings |
| `STORAGE_DIR` | `data/uploads` | Path for uploaded original PDF storage |
| `DAILY_REQUEST_QUOTA` | `1000` | In-memory workspace daily query guardrail |

---

## 🔒 Security & Provenance Integrity

1. **Workspace Boundary**: Every chunk, query, summary, and comparison query strictly enforces workspace isolation on the database level.
2. **Untrusted PDF Input**: Document contents are encapsulated within strict prompt boundaries preventing prompt injection from overriding system instructions.
3. **Cascade Deletion**: Deleting a document immediately cascades to its extracted text, chunks, embeddings, cached summaries, and query citations.
