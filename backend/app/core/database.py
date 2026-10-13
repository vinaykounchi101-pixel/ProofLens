"""Database engine, session management, and dialect-aware Vector column definition."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import TypeDecorator, JSON, event
from app.core.config import settings

from sqlalchemy.pool import NullPool

# Engine setup
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
    )
elif "pooler" in settings.DATABASE_URL or "supabase" in settings.DATABASE_URL:
    # Disable asyncpg statement caching and use NullPool + pool_pre_ping for Supabase poolers
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Enforce foreign key constraints and cascades in SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


class VectorType(TypeDecorator):
    """
    Dialect-aware vector column.
    Uses pgvector's Vector type when running on PostgreSQL,
    and falls back to JSON on SQLite for local lightweight testing.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSON())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
