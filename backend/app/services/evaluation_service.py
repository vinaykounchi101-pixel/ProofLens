"""Evaluation harness service for measuring genuine RAG quality, citations, and abstention (FR-15)."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.document import Document
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.schemas.evaluation import EvaluationRunResponse, EvaluationMetrics, EvaluationCaseResult
from app.services.rag_service import rag_service


def _load_evaluation_dataset() -> List[Dict[str, Any]]:
    """Loads version-controlled evaluation dataset from disk."""
    dataset_path = Path(__file__).resolve().parent.parent.parent / "tests" / "evaluation" / "dataset.json"
    if dataset_path.exists():
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load evaluation dataset from {dataset_path}: {e}")
    # Return minimal safe baseline if file load fails
    return [
        {
            "case_id": "case_01_factual",
            "question": "What was the total net sales revenue reported?",
            "expected_status": "supported",
            "should_abstain": False,
            "expected_keywords": ["81,797", "net sales"],
        },
        {
            "case_id": "case_02_abstention",
            "question": "What was the CEO's personal holiday travel itinerary for July?",
            "expected_status": "insufficient_evidence",
            "should_abstain": True,
            "expected_keywords": [],
        },
    ]


class EvaluationService:
    @staticmethod
    async def run_evaluation(
        session: AsyncSession,
        workspace_id: str,
        benchmark_name: str = "mvp_baseline",
        sample_doc_ids: Optional[List[str]] = None,
    ) -> EvaluationRunResponse:
        dataset = _load_evaluation_dataset()

        # If sample_doc_ids not explicitly provided, find indexed documents for this workspace
        doc_ids = sample_doc_ids
        if not doc_ids:
            doc_stmt = select(Document.id).where(
                Document.workspace_id == workspace_id,
                Document.status == "indexed",
            )
            doc_res = await session.execute(doc_stmt)
            doc_ids = list(doc_res.scalars().all())

        # If still no documents, fail honest without fabricating passing metrics
        if not doc_ids:
            eval_run = EvaluationRun(
                workspace_id=workspace_id,
                benchmark_name=f"{benchmark_name} (unexecuted - no documents)",
                precision_at_k=0.0,
                recall_at_k=0.0,
                citation_validity_rate=0.0,
                abstention_accuracy=0.0,
            )
            session.add(eval_run)
            await session.commit()
            await session.refresh(eval_run)

            return EvaluationRunResponse(
                id=eval_run.id,
                benchmark_name=eval_run.benchmark_name,
                metrics=EvaluationMetrics(
                    precision_at_k=0.0,
                    recall_at_k=0.0,
                    citation_validity_rate=0.0,
                    abstention_accuracy=0.0,
                ),
                total_cases=len(dataset),
                passed_cases=0,
                failed_cases=len(dataset),
                failed_results=[
                    EvaluationCaseResult(
                        case_id="no_indexed_documents",
                        passed=False,
                        metrics={"score": 0.0},
                        failure_reason="No indexed documents available in workspace to execute evaluation against.",
                    )
                ],
            )

        case_results: List[EvaluationCaseResult] = []
        total_cases = len(dataset)
        passed_cases = 0

        total_citations = 0
        valid_citations = 0

        total_abstention_cases = 0
        correct_abstentions = 0

        precisions_at_k = []
        recalls_at_k = []

        for case in dataset:
            case_id = case["case_id"]
            question = case["question"]
            expected_status = case["expected_status"]
            should_abstain = case.get("should_abstain", False)
            expected_keywords = case.get("expected_keywords", [])

            # Run actual RAG pipeline against authorized documents
            qa_res = await rag_service.answer_question(
                session=session,
                workspace_id=workspace_id,
                question=question,
                document_ids=doc_ids,
                top_k=3,
                track_usage=False,
            )

            actual_status = qa_res.evidence_status
            citations = qa_res.citations

            # Track abstention
            if should_abstain:
                total_abstention_cases += 1
                if actual_status == "insufficient_evidence":
                    correct_abstentions += 1

            # Track citations
            for c in citations:
                total_citations += 1
                if c.is_verified and c.is_reference_valid and c.is_excerpt_valid:
                    valid_citations += 1

            # Precision & Recall estimation based on keyword relevance
            if expected_keywords:
                matched_chunks = 0
                for c in citations:
                    if any(kw.lower() in c.cited_excerpt.lower() for kw in expected_keywords):
                        matched_chunks += 1
                k = max(1, len(citations))
                precisions_at_k.append(matched_chunks / k)
                recalls_at_k.append(1.0 if matched_chunks > 0 else 0.0)
            else:
                precisions_at_k.append(1.0 if actual_status == expected_status else 0.0)
                recalls_at_k.append(1.0 if actual_status == expected_status else 0.0)

            status_matched = (actual_status == expected_status)
            case_passed = status_matched

            if case_passed:
                passed_cases += 1

            failure_reason = None
            if not case_passed:
                failure_reason = f"Expected status '{expected_status}', got '{actual_status}'."

            case_results.append(
                EvaluationCaseResult(
                    case_id=case_id,
                    passed=case_passed,
                    metrics={"score": 1.0 if case_passed else 0.0},
                    failure_reason=failure_reason,
                )
            )

        # Real aggregate calculations
        citation_validity_rate = round(valid_citations / max(1, total_citations), 2) if total_citations > 0 else 1.0
        abstention_accuracy = round(correct_abstentions / max(1, total_abstention_cases), 2) if total_abstention_cases > 0 else 1.0
        precision_at_k = round(sum(precisions_at_k) / max(1, len(precisions_at_k)), 2)
        recall_at_k = round(sum(recalls_at_k) / max(1, len(recalls_at_k)), 2)

        eval_run = EvaluationRun(
            workspace_id=workspace_id,
            benchmark_name=benchmark_name,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            citation_validity_rate=citation_validity_rate,
            abstention_accuracy=abstention_accuracy,
        )
        session.add(eval_run)
        await session.flush()

        for cr in case_results:
            er = EvaluationResult(
                evaluation_run_id=eval_run.id,
                case_id=cr.case_id,
                passed=cr.passed,
                metrics=cr.metrics,
                failure_reason=cr.failure_reason,
            )
            session.add(er)

        await session.commit()
        await session.refresh(eval_run)

        failed_results = [r for r in case_results if not r.passed]

        return EvaluationRunResponse(
            id=eval_run.id,
            benchmark_name=benchmark_name,
            metrics=EvaluationMetrics(
                precision_at_k=precision_at_k,
                recall_at_k=recall_at_k,
                citation_validity_rate=citation_validity_rate,
                abstention_accuracy=abstention_accuracy,
            ),
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=total_cases - passed_cases,
            failed_results=failed_results,
        )


evaluation_service = EvaluationService()
