"""Centralized application configuration using Pydantic Settings."""

import os
import urllib.parse
from pathlib import Path
from typing import List, Union, Any
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            ".env",
        ),
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
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_BATCH_SIZE: int = 16

    # AI Provider: LLM Generation (gemini-3-flash-preview verified active with free quota)
    LLM_PROVIDER: str = "mock"  # "gemini" or "mock"
    LLM_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL: str = "gemini-3-flash-preview"
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT_SECONDS: int = 30

    # Retrieval and Grounding Parameters
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.65

    # Usage and Rate Limit Controls (FR-14)
    RATE_LIMIT_PER_MINUTE: int = 15
    MAX_DAILY_QUERIES: int = 200

    # Development & Auth Configuration
    DEFAULT_DEV_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEFAULT_DEV_USER_EMAIL: str = "dev@prooflens.local"
    DEFAULT_DEV_API_KEY: str = "prooflens_dev_api_key_test_12345"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            clean = v.strip().strip('"').strip("'")
            if clean.startswith("[") and clean.endswith("]"):
                try:
                    import json
                    parsed = json.loads(clean)
                    if isinstance(parsed, list):
                        return [str(item).strip().strip('"').strip("'") for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [part.strip().strip('"').strip("'") for part in clean.replace("\n", ",").split(",") if part.strip()]
        if isinstance(v, list):
            return [str(item).strip().strip('"').strip("'") for item in v if str(item).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("EMBEDDING_MODEL", mode="before")
    @classmethod
    def normalize_embedding_model(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip().strip('"').strip("'").lower()
            if clean in ("", "gemini", "default", "models/gemini"):
                return "gemini-embedding-2"
            if clean.startswith("models/"):
                return clean[len("models/"):]
            return clean
        return "gemini-embedding-2"

    @field_validator("LLM_MODEL", mode="before")
    @classmethod
    def normalize_llm_model(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip().strip('"').strip("'").lower()
            if clean in (
                "",
                "gemini",
                "default",
                "models/gemini",
                "gemini-2.5-flash",
                "models/gemini-2.5-flash",
                "gemini-3.5-flash",
                "models/gemini-3.5-flash",
                "gemini-3.6-flash",
                "models/gemini-3.6-flash",
            ):
                return "gemini-3-flash-preview"
            if clean.startswith("models/"):
                return clean[len("models/"):]
            return clean
        return "gemini-3-flash-preview"

    @field_validator("DEFAULT_DEV_USER_ID", mode="before")
    @classmethod
    def ensure_dev_user_id_length(cls, v: str) -> str:
        if isinstance(v, str) and len(v) > 36:
            if "00000000-" in v:
                return v[v.index("00000000-"):]
            return v[:36]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip('"').strip("'")
            # Strip accidental repeated prefix (e.g. DATABASE_URL=DATABASE_URL=...)
            while v.startswith("DATABASE_URL="):
                v = v[len("DATABASE_URL="):].strip().strip('"').strip("'")
            # Strip JDBC prefix if provided by mistake (e.g. from Supabase dashboard JDBC tab)
            if v.startswith("jdbc:"):
                v = v[len("jdbc:"):].strip()

            # Render / Heroku inject 'postgres://' which SQLAlchemy 2.0 rejects
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            # Standard 'postgresql://' without async driver specification
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

            # If JDBC-style query parameters were passed (e.g. ?user=...&password=...)
            if "?" in v:
                base, query_str = v.split("?", 1)
                if "@" not in base:
                    parsed_q = urllib.parse.parse_qs(query_str)
                    user = parsed_q.get("user", [None])[0]
                    password = parsed_q.get("password", [None])[0]
                    if user:
                        remaining = {k: val for k, val in parsed_q.items() if k not in ("user", "password")}
                        user_enc = urllib.parse.quote(user, safe="")
                        pass_enc = urllib.parse.quote(password, safe="") if password else ""
                        auth_part = f"{user_enc}:{pass_enc}@" if pass_enc else f"{user_enc}@"
                        if "://" in base:
                            scheme, rest = base.split("://", 1)
                            new_base = f"{scheme}://{auth_part}{rest}"
                        else:
                            new_base = f"{auth_part}{base}"
                        rem_query = urllib.parse.urlencode(remaining, doseq=True)
                        v = f"{new_base}?{rem_query}" if rem_query else new_base
        return v

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
