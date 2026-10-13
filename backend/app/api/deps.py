"""FastAPI reusable dependencies for database sessions, authentication, and workspace authorization."""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AuthenticationException, ResourceNotFoundException, UnauthorizedException
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer token or API Key"),
    x_api_key: Optional[str] = Header(None, description="API Key header"),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolves and verifies the authenticated user.
    Enforces strict token/key verification in production.
    In development, allows convenient fallback to default development user if unauthenticated.
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        token = x_api_key.strip()

    if token:
        # Check by api_key or token
        stmt = select(User).where(User.api_key == token)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        # Also support dev key in development mode
        if not user and settings.ENVIRONMENT.lower() == "development" and token == settings.DEFAULT_DEV_API_KEY:
            user = await _get_or_create_dev_user(session)

        if not user:
            raise AuthenticationException("Invalid authentication credentials.")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive.")

        return user

    # No credentials provided
    if settings.ENVIRONMENT.lower() == "production":
        raise AuthenticationException("Authentication credentials were not provided.")

    # Development mode: fail-safe fallback to configured dev user
    return await _get_or_create_dev_user(session)


async def _get_or_create_dev_user(session: AsyncSession) -> User:
    """Retrieves or creates the local development user."""
    stmt = select(User).where(User.id == settings.DEFAULT_DEV_USER_ID)
    res = await session.execute(stmt)
    dev_user = res.scalar_one_or_none()
    if not dev_user:
        dev_user = User(
            id=settings.DEFAULT_DEV_USER_ID,
            email=settings.DEFAULT_DEV_USER_EMAIL,
            hashed_password="insecure_dev_hash_change_in_production",
            api_key=settings.DEFAULT_DEV_API_KEY,
            is_active=True,
        )
        session.add(dev_user)
        await session.commit()
        await session.refresh(dev_user)
    return dev_user


async def get_authorized_workspace(
    workspace_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    """
    Verifies that the requested workspace exists and is owned by the authenticated user.
    Fails closed with HTTP 404 (without leaking workspace existence across tenant boundaries).
    """
    stmt = select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id,
    )
    res = await session.execute(stmt)
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise ResourceNotFoundException("Workspace not found.")
    return workspace


async def get_authorized_document(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """
    Verifies workspace ownership and document existence within that workspace.
    """
    await get_authorized_workspace(workspace_id=workspace_id, session=session, current_user=current_user)
    stmt = select(Document).where(
        Document.id == document_id,
        Document.workspace_id == workspace_id,
        Document.status != "deleted",
    )
    res = await session.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document not found.")
    return doc


async def get_authorized_document_by_id(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """
    Verifies document existence and workspace ownership directly by document_id.
    """
    stmt = (
        select(Document)
        .join(Workspace, Document.workspace_id == Workspace.id)
        .where(
            Document.id == document_id,
            Workspace.owner_id == current_user.id,
            Document.status != "deleted",
        )
    )
    res = await session.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document not found.")
    return doc


__all__ = [
    "get_db",
    "get_current_user",
    "get_authorized_workspace",
    "get_authorized_document",
    "get_authorized_document_by_id",
]
