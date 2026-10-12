"""Aggregated API v1 Router."""

from fastapi import APIRouter
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.documents import router as documents_router
from app.api.v1.summaries import router as summaries_router
from app.api.v1.qa import router as qa_router
from app.api.v1.history import router as history_router
from app.api.v1.compare import router as compare_router
from app.api.v1.evaluation import router as evaluation_router

api_router = APIRouter()
api_router.include_router(workspaces_router)
api_router.include_router(documents_router)
api_router.include_router(summaries_router)
api_router.include_router(qa_router)
api_router.include_router(history_router)
api_router.include_router(compare_router)
api_router.include_router(evaluation_router)
