"""ProofLens AI — FastAPI Application Entry Point."""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.errors import ProofLensException, generic_exception_handler, prooflens_exception_handler
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing ProofLens AI backend...")
    # Initialize tables
    async with engine.begin() as conn:
        # If running on PostgreSQL, enable vector extension
        if "postgresql" in settings.DATABASE_URL:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension automatically: {e}")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
    yield
    await engine.dispose()
    logger.info("ProofLens AI backend shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception Handlers
app.add_exception_handler(ProofLensException, prooflens_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Health and Readiness Probes
@app.get("/api/v1/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/v1/ready", tags=["system"])
async def readiness_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
        return {
            "status": "ready",
            "database": "connected",
            "environment": settings.ENVIRONMENT,
        }
    except Exception as exc:
        return {
            "status": "unready",
            "database": "disconnected",
            "error": str(exc),
        }


# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
