"""Centralized application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application & Environment
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "ProofLens AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "prooflens-insecure-dev-secret-key-change-in-prod"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database
    # Default to local postgresql, or fallback to sqlite for environments without postgres
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/prooflens.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Local Document File Storage
    STORAGE_DIR: Path = Path("./data/storage")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    MAX_PAGES_PER_DOCUMENT: int = 50

    # AI Provider: Embeddings (gemini-embedding-2 verified active)
    EMBEDDING_PROVIDER: str = "mock"  # "gemini" or "mock"
    EMBEDDING_API_KEY: SecretStr = SecretStr("")
    EMBEDDING_MODEL: str = "models/gemini-embedding-2"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_BATCH_SIZE: int = 16

    # AI Provider: LLM Generation (gemini-2.5-flash verified active)
    LLM_PROVIDER: str = "mock"  # "gemini" or "mock"
    LLM_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT_SECONDS: int = 30

    # Retrieval and Grounding Parameters
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.65

    # Usage and Rate Limit Controls (FR-14)
    RATE_LIMIT_PER_MINUTE: int = 15
    MAX_DAILY_QUERIES: int = 200

    @field_validator("STORAGE_DIR", mode="after")
    @classmethod
    def ensure_storage_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


settings = Settings()
