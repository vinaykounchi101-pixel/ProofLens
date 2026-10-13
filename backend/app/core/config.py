"""Centralized application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import List, Union, Any
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

    # Unified Gemini API Key (populates both embedding and LLM keys if set)
    GEMINI_API_KEY: SecretStr = SecretStr("")

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

    # Development & Auth Configuration
    DEFAULT_DEV_USER_ID: str = "dev-user-00000000-0000-0000-0000-000000000001"
    DEFAULT_DEV_USER_EMAIL: str = "dev@prooflens.local"
    DEFAULT_DEV_API_KEY: str = "prooflens_dev_api_key_test_12345"

    @field_validator("STORAGE_DIR", mode="after")
    @classmethod
    def ensure_storage_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    def model_post_init(self, __context: Any) -> None:
        # If GEMINI_API_KEY is provided, automatically populate providers and keys
        gemini_key = self.GEMINI_API_KEY.get_secret_value()
        if gemini_key:
            if not self.EMBEDDING_API_KEY.get_secret_value():
                self.EMBEDDING_API_KEY = SecretStr(gemini_key)
                self.EMBEDDING_PROVIDER = "gemini"
            if not self.LLM_API_KEY.get_secret_value():
                self.LLM_API_KEY = SecretStr(gemini_key)
                self.LLM_PROVIDER = "gemini"

        # Production safety guard: reject insecure default secret
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY.startswith("prooflens-insecure"):
                raise ValueError("Production mode requires configuring a secure, non-default SECRET_KEY.")


settings = Settings()
