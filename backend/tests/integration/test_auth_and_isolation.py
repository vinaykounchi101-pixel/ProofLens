"""Mandatory Authentication and Authorization Isolation Tests (Section 4)."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.database import Base, engine


@pytest.mark.asyncio
async def test_auth_registration_and_login(async_client: AsyncClient):
    # 1. Register User A
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "alice@prooflens.local", "password": "SecurePassword123!"},
    )
    assert reg_res.status_code == 201
    user_a = reg_res.json()
    assert user_a["email"] == "alice@prooflens.local"
    assert "api_key" in user_a

    # 2. Login User A
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@prooflens.local", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token_a = token_data["access_token"]

    # 3. /me endpoint
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "alice@prooflens.local"


@pytest.mark.asyncio
async def test_cross_user_workspace_isolation(async_client: AsyncClient, sample_pdf_bytes: bytes):
    # Register Alice
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "alice_iso@prooflens.local", "password": "SecurePassword123!"},
    )
    token_a = reg_a.json()["api_key"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register Bob
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "bob_iso@prooflens.local", "password": "SecurePassword123!"},
    )
    token_b = reg_b.json()["api_key"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice creates a workspace
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Alice Confidential", "description": "Alice's secrets"},
        headers=headers_a,
    )
    assert ws_res.status_code == 201
    alice_ws_id = ws_res.json()["id"]

    # Alice uploads a document
    doc_res = await async_client.post(
        f"/api/v1/workspaces/{alice_ws_id}/documents/upload",
        files={"file": ("Alice_Contract.pdf", sample_pdf_bytes, "application/pdf")},
        headers=headers_a,
    )
    assert doc_res.status_code == 201
    alice_doc_id = doc_res.json()["id"]

    # Bob attempts to access Alice's workspace -> MUST fail closed with 404
    bob_ws_access = await async_client.get(
        f"/api/v1/workspaces/{alice_ws_id}",
        headers=headers_b,
    )
    assert bob_ws_access.status_code == 404

    # Bob attempts to list Alice's documents -> MUST fail closed with 404
    bob_docs_access = await async_client.get(
        f"/api/v1/workspaces/{alice_ws_id}/documents",
        headers=headers_b,
    )
    assert bob_docs_access.status_code == 404

    # Bob attempts to get Alice's document -> MUST fail closed with 404
    bob_doc_get = await async_client.get(
        f"/api/v1/workspaces/{alice_ws_id}/documents/{alice_doc_id}",
        headers=headers_b,
    )
    assert bob_doc_get.status_code == 404

    # Bob attempts to delete Alice's document -> MUST fail closed with 404
    bob_del_doc = await async_client.delete(
        f"/api/v1/workspaces/{alice_ws_id}/documents/{alice_doc_id}",
        headers=headers_b,
    )
    assert bob_del_doc.status_code == 404

    # Bob attempts to delete Alice's workspace -> MUST fail closed with 404
    bob_del_ws = await async_client.delete(
        f"/api/v1/workspaces/{alice_ws_id}",
        headers=headers_b,
    )
    assert bob_del_ws.status_code == 404

    # Bob attempts cross-workspace document retrieval -> MUST fail closed with 404
    bob_qa = await async_client.post(
        f"/api/v1/workspaces/{alice_ws_id}/qa",
        json={"question": "What are the secret terms?", "document_ids": [alice_doc_id]},
        headers=headers_b,
    )
    assert bob_qa.status_code == 404

    # Bob attempts cross-user history access -> MUST fail closed with 404
    bob_hist = await async_client.get(
        f"/api/v1/workspaces/{alice_ws_id}/history",
        headers=headers_b,
    )
    assert bob_hist.status_code == 404

    # Bob attempts unauthorized evaluation access -> MUST fail closed with 404
    bob_eval = await async_client.post(
        f"/api/v1/workspaces/{alice_ws_id}/evaluation/run",
        json={"benchmark_name": "malicious_run"},
        headers=headers_b,
    )
    assert bob_eval.status_code == 404


@pytest.mark.asyncio
async def test_forged_identifiers_fail_closed(async_client: AsyncClient):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "forgery_test@prooflens.local", "password": "SecurePassword123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['api_key']}"}

    # Random nonexistent workspace
    res = await async_client.get(
        "/api/v1/workspaces/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert res.status_code == 404

    # Random nonexistent document
    res = await async_client.get(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_invalid_and_missing_auth_in_production(async_client: AsyncClient):
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"

        # Missing token in production -> 401
        res = await async_client.get("/api/v1/workspaces")
        assert res.status_code == 401

        # Invalid token in production -> 401
        res = await async_client.get(
            "/api/v1/workspaces",
            headers={"Authorization": "Bearer invalid_forged_token_xyz"},
        )
        assert res.status_code == 401
    finally:
        settings.ENVIRONMENT = original_env
