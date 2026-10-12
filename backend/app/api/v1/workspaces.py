"""Workspace endpoints (FR-01)."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.errors import ResourceNotFoundException
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    session: AsyncSession = Depends(get_db),
):
    workspace = Workspace(name=payload.name, description=payload.description)
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return workspace


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Workspace).order_by(Workspace.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    res = await session.execute(stmt)
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise ResourceNotFoundException("Workspace not found.")
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    res = await session.execute(stmt)
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise ResourceNotFoundException("Workspace not found.")
    
    from app.services.storage_service import storage_service
    storage_service.delete_workspace_files(workspace_id)
    await session.delete(workspace)
    await session.commit()
