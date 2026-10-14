"""End-to-end integration tests for ProofLens API workflow."""

import pytest


@pytest.mark.asyncio
async def test_health_and_ready_endpoints(async_client):
    res_health = await async_client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_ready = await async_client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_complete_evidence_first_rag_lifecycle(
    async_client, sample_pdf_bytes, second_sample_pdf_bytes
):
    # 1. Create Workspace
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Q3 Financials", "description": "Earnings and policies"},
    )
    assert ws_res.status_code == 201
    ws_data = ws_res.json()
    ws_id = ws_data["id"]

    # 2. Upload Document 1
    upload_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        files={"file": ("Apple_Q3.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_1 = upload_res.json()
    assert doc_1["status"] == "indexed"
    assert doc_1["total_pages"] == 2
    assert doc_1["total_chunks"] >= 2
    doc_1_id = doc_1["id"]

    # 3. List Documents
    list_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) == 1

    # 4. Ask Supported Question
    qa_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/qa",
        json={
            "question": "What was the total net sales revenue reported?",
            "document_ids": [doc_1_id],
            "top_k": 3,
        },
    )
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["evidence_status"] == "supported"
    assert len(qa_data["citations"]) > 0
    assert qa_data["citations"][0]["document_id"] == doc_1_id
    assert qa_data["citations"][0]["page_number"] in [1, 2]
    assert "81797" in qa_data["answer"]

    # 5. Ask Unsupported Question (Abstention check)
    unsupported_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/qa",
        json={
            "question": "What was the CEO's personal travel itinerary for vacation?",
            "document_ids": [doc_1_id],
            "top_k": 3,
        },
    )
    assert unsupported_res.status_code == 200
    unsupported_data = unsupported_res.json()
    assert unsupported_data["evidence_status"] == "insufficient_evidence"
    assert len(unsupported_data["citations"]) == 0

    # 6. Check Query History (FR-12)
    hist_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/history")
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    assert len(history_items) >= 2

    # 7. Document Summary (FR-09)
    sum_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/documents/{doc_1_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["summary"] is not None
    assert len(sum_data["suggested_questions"]) >= 1

    # 8. Upload Document 2 for Comparison (FR-10)
    upload_2_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        files={"file": ("Policy_2024.pdf", second_sample_pdf_bytes, "application/pdf")},
    )
    assert upload_2_res.status_code == 201
    doc_2_id = upload_2_res.json()["id"]

    # 9. Cross-Document Comparison
    comp_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/compare",
        json={
            "topic": "Notice period requirement",
            "document_ids": [doc_1_id, doc_2_id],
        },
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["comparison_status"] == "completed"
    assert len(comp_data["findings"]) >= 1

    # 10. Automated Evaluation (FR-15)
    eval_res = await async_client.post(
        f"/api/v1/evaluation/run?workspace_id={ws_id}",
        json={"benchmark_name": "integration_test_run"},
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["metrics"]["citation_validity_rate"] >= 0.8
    assert eval_data["metrics"]["abstention_accuracy"] >= 0.8

    # 11. Delete Document 1 and check cascade
    del_res = await async_client.delete(f"/api/v1/workspaces/{ws_id}/documents/{doc_1_id}")
    assert del_res.status_code == 204

    # Verify Document 1 is no longer listed
    list_after_del = await async_client.get(f"/api/v1/workspaces/{ws_id}/documents")
    assert list_after_del.status_code == 200
    remaining_docs = list_after_del.json()
    assert len(remaining_docs) == 1
    assert remaining_docs[0]["id"] == doc_2_id

    # 12. Toggle Save / Bookmark Query Run
    first_query_id = history_items[0]["id"]
    save_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/history/{first_query_id}/save"
    )
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["query_id"] == first_query_id
    assert "is_saved" in save_data

    # 12b. Verify Live Query Evaluation computed from user asked questions
    live_eval_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/evaluation/live"
    )
    assert live_eval_res.status_code == 200
    live_eval_data = live_eval_res.json()
    assert live_eval_data["total_queries"] >= 2
    assert live_eval_data["supported_queries"] >= 1
    assert live_eval_data["abstention_queries"] >= 1
    assert live_eval_data["citation_validity_rate"] >= 0.8
    assert len(live_eval_data["evaluated_queries"]) >= 2

    # 13. Delete Single Query Run
    del_query_res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}/history/{first_query_id}"
    )
    assert del_query_res.status_code == 204

    # 14. Clear All History for Workspace
    clear_res = await async_client.delete(f"/api/v1/workspaces/{ws_id}/history")
    assert clear_res.status_code == 204

    # Verify history is now empty
    hist_after_clear = await async_client.get(f"/api/v1/workspaces/{ws_id}/history")
    assert hist_after_clear.status_code == 200
    assert len(hist_after_clear.json()) == 0

    # 15. Delete Workspace
    del_ws_res = await async_client.delete(f"/api/v1/workspaces/{ws_id}")
    assert del_ws_res.status_code == 204

    # Verify workspace is gone
    get_ws_res = await async_client.get(f"/api/v1/workspaces/{ws_id}")
    assert get_ws_res.status_code == 404

