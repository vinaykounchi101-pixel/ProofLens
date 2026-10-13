"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.core.errors import AuthenticationException, ValidationException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    # Check if email is already registered
    stmt = select(User).where(User.email == payload.email.lower().strip())
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        raise ValidationException("An account with this email address already exists.")

    new_user = User(
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.email == payload.email.lower().strip())
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationException("Invalid email address or password.")

    if not user.is_active:
        raise AuthenticationException("User account is inactive.")

    return TokenResponse(
        access_token=user.api_key,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
