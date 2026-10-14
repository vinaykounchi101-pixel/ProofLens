# ProofLens AI — Cloud Deployment Environment Configuration

This reference guide contains the exact environment variables and configuration settings required to deploy the **ProofLens AI Backend on Render** and the **ProofLens AI Frontend on Vercel**.

---

## 1. Backend Deployment on Render (FastAPI)

### Render Service Settings
* **Service Type:** Web Service
* **Language / Runtime:** `Python 3`
* **Root Directory:** `backend`
* **Build Command:**
  ```bash
  pip install -r requirements.txt && alembic upgrade head
  ```
* **Start Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

---

### Render Environment Variables (Copy & Paste Block)

Paste the following block into Render's **Environment** tab using **"Add from .env"** or enter each key manually:

```ini
ENVIRONMENT=production
PROJECT_NAME="ProofLens AI"
API_V1_STR=/api/v1
SECRET_KEY=replace-with-a-random-32-byte-hex-string
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[YOUR-REGION].pooler.supabase.com:5432/postgres
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
ALLOWED_ORIGINS=https://your-frontend-app.vercel.app,http://localhost:3000
STORAGE_DIR=data/storage
MAX_UPLOAD_SIZE_BYTES=15728640
MAX_PAGES_PER_DOCUMENT=50
GEMINI_API_KEY=your-gemini-api-key-here
EMBEDDING_PROVIDER=gemini
LLM_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-2
LLM_MODEL=gemini-3-flash-preview
EMBEDDING_DIMENSIONS=768
EMBEDDING_BATCH_SIZE=16
RETRIEVAL_TOP_K=5
RETRIEVAL_SIMILARITY_THRESHOLD=0.65
RATE_LIMIT_PER_MINUTE=15
MAX_DAILY_QUERIES=200
```

---

### Backend Variables Reference Table

| Variable Name | Required | Default / Recommended Value | Description |
|---|:---:|---|---|
| `ENVIRONMENT` | **Yes** | `production` | Enables production mode and fails closed if insecure secrets are used. |
| `SECRET_KEY` | **Yes** | *32-byte random hex* | Cryptographic salt used for session tokens and signatures. |
| `DATABASE_URL` | **Yes** | `postgresql+asyncpg://...` | Connection URL to your Supabase or Render PostgreSQL database with pgvector. |
| `ALLOWED_ORIGINS` | **Yes** | `https://your-app.vercel.app` | Comma-separated domains allowed to make cross-origin requests to the API. |
| `GEMINI_API_KEY` | **Yes** | `AQ.Ab8...` | Google Gemini API key used for query embeddings and grounded Q&A generation. |
| `EMBEDDING_PROVIDER` | Optional | `gemini` | Embeddings adapter (`gemini` for live, `mock` for zero-cost offline test). |
| `LLM_PROVIDER` | Optional | `gemini` | LLM generation adapter (`gemini` for live, `mock` for offline test). |
| `EMBEDDING_MODEL` | Optional | `gemini-embedding-2` | Google model for vector embeddings (768 dimensions). |
| `LLM_MODEL` | Optional | `gemini-3-flash-preview` | Google model for grounded generation with auto-failover. |
| `STORAGE_DIR` | Optional | `data/storage` | Local directory inside the Render service for temporarily storing PDFs. |
| `MAX_UPLOAD_SIZE_BYTES`| Optional | `15728640` | Max PDF file size (15 MB). |
| `RETRIEVAL_TOP_K` | Optional | `5` | Number of candidate document chunks retrieved per query. |
| `RATE_LIMIT_PER_MINUTE`| Optional | `15` | Per-workspace query rate limiter guardrail. |
| `MAX_DAILY_QUERIES` | Optional | `200` | Daily workspace quota cap. |

---

## 2. Frontend Deployment on Vercel (Next.js 14)

### Vercel Project Settings
* **Framework Preset:** `Next.js`
* **Root Directory:** `frontend`
* **Build Command:** `next build` (default)
* **Output Directory:** `.next` (default)
* **Install Command:** `npm install` (default)

---

### Vercel Environment Variables (Copy & Paste Block)

Add the following variable under **Project Settings > Environment Variables** in Vercel:

```ini
NEXT_PUBLIC_API_URL=https://your-backend-service.onrender.com/api/v1
```

---

### Frontend Variables Reference Table

| Variable Name | Required | Example Value | Description |
|---|:---:|---|---|
| `NEXT_PUBLIC_API_URL` | **Yes** | `https://prooflens-backend.onrender.com/api/v1` | Public URL of your deployed Render backend ending in `/api/v1`. |

---

## 3. Recommended Step-by-Step Deployment Order

To avoid CORS errors and connection failures:

1. **Step 1 — Deploy Backend on Render First:**
   * Create a new **Web Service** on Render connected to this repository.
   * Set **Root Directory** to `backend`.
   * Set **Build Command** to `pip install -r requirements.txt && alembic upgrade head`.
   * Set **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   * Paste the backend environment variables above into the Render Environment tab.
   * Deploy the service and copy the generated Render URL (e.g., `https://prooflens-api.onrender.com`).

2. **Step 2 — Deploy Frontend on Vercel:**
   * Import this repository into Vercel.
   * Select `frontend` as the **Root Directory**.
   * Add the environment variable:
     `NEXT_PUBLIC_API_URL = https://prooflens-api.onrender.com/api/v1`
   * Click **Deploy** and copy your generated Vercel production URL (e.g., `https://prooflens.vercel.app`).

3. **Step 3 — Link Vercel Domain in Render CORS (`ALLOWED_ORIGINS`):**
   * Return to your Render backend service > **Environment**.
   * Update `ALLOWED_ORIGINS` to include your live Vercel URL:
     ```
     ALLOWED_ORIGINS=https://prooflens.vercel.app,http://localhost:3000
     ```
   * Save changes (Render will automatically reload the backend with the new allowed origin).
