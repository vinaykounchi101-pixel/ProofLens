"""Unit tests for database URL normalization and JDBC resilience."""

import pytest
from app.core.config import Settings
from sqlalchemy.engine.url import make_url


def test_normalize_standard_postgresql():
    url = "postgresql://postgres:secret@localhost:5432/prooflens"
    normalized = Settings.normalize_database_url(url)
    assert normalized.startswith("postgresql+asyncpg://")
    u = make_url(normalized)
    assert u.username == "postgres"
    assert u.password == "secret"
    assert u.host == "localhost"
    assert u.port == 5432
    assert u.database == "prooflens"


def test_normalize_postgres_heroku_scheme():
    url = "postgres://usr:pwd@host.internal:5432/mydb"
    normalized = Settings.normalize_database_url(url)
    assert normalized.startswith("postgresql+asyncpg://")
    u = make_url(normalized)
    assert u.username == "usr"
    assert u.password == "pwd"


def test_normalize_supabase_jdbc_query_params():
    raw_jdbc = "jdbc:postgresql://aws-0-ap-south-1.pooler.supabase.com:6543/postgres?user=postgres.myproject&password=SuperSecretPassword123"
    normalized = Settings.normalize_database_url(raw_jdbc)
    assert normalized.startswith("postgresql+asyncpg://")
    assert "jdbc:" not in normalized
    u = make_url(normalized)
    assert u.username == "postgres.myproject"
    assert u.password == "SuperSecretPassword123"
    assert u.host == "aws-0-ap-south-1.pooler.supabase.com"
    assert u.port == 6543
    assert u.database == "postgres"


def test_normalize_supabase_jdbc_with_special_characters_in_password():
    raw_jdbc = "jdbc:postgresql://aws-0-ap-south-1.pooler.supabase.com:6543/postgres?user=postgres.myproj&password=Complex#Pass%Word"
    normalized = Settings.normalize_database_url(raw_jdbc)
    assert normalized.startswith("postgresql+asyncpg://")
    u = make_url(normalized)
    assert u.username == "postgres.myproj"
    assert u.password == "Complex#Pass%Word"
