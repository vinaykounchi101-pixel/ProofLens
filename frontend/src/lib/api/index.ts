import { apiFetch } from './client';
import {
  Workspace,
  WorkspaceListResponse,
  Document,
  DocumentListResponse,
  DocumentSummaryResponse,
  QuestionRequest,
  AnswerResponse,
  CompareRequest,
  ComparisonResponse,
  ComparisonFinding,
  Citation,
  HistoryListResponse,
  QueryRun,
  EvaluationRun,
  EvaluationRunListResponse,
  LiveEvaluationSummary,
} from '../types/api';

export const api = {
  // Workspaces
  async listWorkspaces(): Promise<WorkspaceListResponse> {
    const data = await apiFetch<any>('/workspaces');
    const items: Workspace[] = Array.isArray(data) ? data : data.workspaces || [];
    return { workspaces: items, total: items.length };
  },

  async createWorkspace(name: string, description?: string): Promise<Workspace> {
    return apiFetch<Workspace>('/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  },

  async getWorkspace(workspaceId: string): Promise<Workspace> {
    return apiFetch<Workspace>(`/workspaces/${workspaceId}`);
  },

  async deleteWorkspace(workspaceId: string): Promise<void> {
    await apiFetch<void>(`/workspaces/${workspaceId}`, {
      method: 'DELETE',
    });
  },

  // Documents
  async listDocuments(workspaceId: string): Promise<DocumentListResponse> {
    const data = await apiFetch<any>(`/workspaces/${workspaceId}/documents`);
    const rawList: any[] = Array.isArray(data) ? data : data.documents || [];
    const documents: Document[] = rawList.map((d: any) => ({
      id: d.id,
      workspace_id: d.workspace_id,
      filename: d.original_filename || d.filename || 'document.pdf',
      file_size: d.file_size_bytes ?? d.file_size ?? 0,
      mime_type: d.mime_type || 'application/pdf',
      processing_status: d.status === 'indexed' ? 'ready' : (d.status || d.processing_status || 'ready'),
      page_count: d.total_pages ?? d.page_count ?? null,
      chunk_count: d.total_chunks ?? d.chunk_count ?? 0,
      error_message: d.error_message || null,
      summary: d.summary || null,
      suggested_questions: d.suggested_questions || [],
      created_at: d.created_at,
      updated_at: d.updated_at,
    }));
    return { documents, total: documents.length };
  },

  async uploadDocument(workspaceId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const d = await apiFetch<any>(`/workspaces/${workspaceId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    return {
      id: d.id,
      workspace_id: d.workspace_id,
      filename: d.original_filename || d.filename || file.name,
      file_size: d.file_size_bytes ?? d.file_size ?? file.size,
      mime_type: d.mime_type || 'application/pdf',
      processing_status: d.status === 'indexed' ? 'ready' : (d.status || 'ready'),
      page_count: d.total_pages ?? null,
      chunk_count: d.total_chunks ?? 0,
      error_message: d.error_message || null,
      created_at: d.created_at || new Date().toISOString(),
      updated_at: d.updated_at || new Date().toISOString(),
    };
  },

  async getDocument(documentId: string, workspaceId?: string): Promise<Document> {
    const url = workspaceId ? `/workspaces/${workspaceId}/documents/${documentId}` : `/documents/${documentId}`;
    const d = await apiFetch<any>(url);
    return {
      id: d.id,
      workspace_id: d.workspace_id,
      filename: d.original_filename || d.filename || 'document.pdf',
      file_size: d.file_size_bytes ?? d.file_size ?? 0,
      mime_type: d.mime_type || 'application/pdf',
      processing_status: d.status === 'indexed' ? 'ready' : (d.status || 'ready'),
      page_count: d.total_pages ?? null,
      chunk_count: d.total_chunks ?? 0,
      error_message: d.error_message || null,
      created_at: d.created_at,
      updated_at: d.updated_at,
    };
  },

  async deleteDocument(documentId: string, workspaceId?: string): Promise<void> {
    const url = workspaceId ? `/workspaces/${workspaceId}/documents/${documentId}` : `/documents/${documentId}`;
    await apiFetch<void>(url, {
      method: 'DELETE',
    });
  },

  async retryDocument(documentId: string, workspaceId?: string): Promise<Document> {
    const url = workspaceId ? `/workspaces/${workspaceId}/documents/${documentId}/retry` : `/documents/${documentId}/retry`;
    const d = await apiFetch<any>(url, {
      method: 'POST',
    });
    return {
      id: d.id,
      workspace_id: d.workspace_id,
      filename: d.original_filename || 'document.pdf',
      file_size: d.file_size_bytes ?? 0,
      mime_type: d.mime_type || 'application/pdf',
      processing_status: d.status === 'indexed' ? 'ready' : (d.status || 'ready'),
      page_count: d.total_pages ?? null,
      chunk_count: d.total_chunks ?? 0,
      error_message: d.error_message || null,
      created_at: d.created_at,
      updated_at: d.updated_at,
    };
  },

  // Summaries
  async getDocumentSummary(documentId: string, workspaceId?: string): Promise<DocumentSummaryResponse> {
    const url = workspaceId ? `/workspaces/${workspaceId}/documents/${documentId}/summary` : `/documents/${documentId}/summary`;
    const res = await apiFetch<any>(url);
    return {
      document_id: res.document_id,
      original_filename: res.original_filename,
      executive_summary: res.summary || 'Summary unavailable.',
      key_findings: [],
      suggested_questions: res.suggested_questions || [],
    };
  },

  // Q&A
  async askQuestion(workspaceId: string, req: QuestionRequest): Promise<AnswerResponse> {
    const res = await apiFetch<any>(`/workspaces/${workspaceId}/qa`, {
      method: 'POST',
      body: JSON.stringify({
        question: req.question,
        document_ids: req.document_ids || [],
        top_k: 5,
      }),
    });

    const mappedCitations: Citation[] = (res.citations || []).map((c: any, idx: number) => ({
      citation_index: idx + 1,
      document_id: c.document_id,
      document_title: c.document_filename || 'Document',
      page_number: c.page_number,
      chunk_id: c.citation_id || c.chunk_id || '',
      excerpt: c.cited_excerpt || c.excerpt || '',
      confidence: c.is_verified ? 0.98 : 0.65,
      validation_status: c.is_verified ? 'verified' : (c.is_repaired ? 'repaired' : 'unverified'),
      is_reference_valid: c.is_reference_valid ?? true,
      is_excerpt_valid: c.is_excerpt_valid ?? true,
      is_verified: c.is_verified ?? true,
      is_repaired: c.is_repaired ?? false,
      repair_reason: c.repair_reason,
    }));

    const isInsufficient = res.evidence_status === 'insufficient_evidence';
    const hasConflicts = res.evidence_status === 'conflicting_evidence';
    const confScore = isInsufficient ? 0.15 : (hasConflicts ? 0.45 : (res.evidence_status === 'supported' ? 0.95 : 0.70));

    return {
      query_run_id: res.query_id,
      question: res.question,
      answer_text: res.answer,
      evidence_status: res.evidence_status,
      claims: res.claims || [],
      citations: mappedCitations,
      retrieved_evidence: [],
      insufficient_evidence: isInsufficient,
      has_conflicts: hasConflicts,
      confidence_score: confScore,
      latency_ms: res.latency_ms,
    };
  },

  // Comparison
  async compareDocuments(workspaceId: string, req: CompareRequest): Promise<ComparisonResponse> {
    const res = await apiFetch<any>(`/workspaces/${workspaceId}/compare`, {
      method: 'POST',
      body: JSON.stringify({
        topic: req.comparison_topic,
        document_ids: req.document_ids,
      }),
    });

    const rawFindings: any[] = res.findings || [];
    const agreements: ComparisonFinding[] = [];
    const disagreements: ComparisonFinding[] = [];
    const omissions: ComparisonFinding[] = [];

    for (const f of rawFindings) {
      const citations: Citation[] = (f.sources || []).map((s: any) => ({
        document_id: s.document_id,
        document_title: s.document_filename || 'Source',
        page_number: s.page_number,
        chunk_id: s.document_id,
        excerpt: s.excerpt,
        confidence: 0.9,
        validation_status: 'verified',
      }));

      const item: ComparisonFinding = {
        topic: f.topic_aspect || f.topic || 'Analysis',
        description: f.description,
        finding_type: f.finding_type,
        citations,
      };

      if (f.finding_type === 'agreement') {
        agreements.push(item);
      } else if (f.finding_type === 'contradiction' || f.finding_type === 'discrepancy') {
        disagreements.push(item);
      } else {
        omissions.push(item);
      }
    }

    const summary = rawFindings.length > 0
      ? `Comparison completed for topic "${res.topic}". Identified ${agreements.length} agreements, ${disagreements.length} discrepancies, and ${omissions.length} scoped differences across ${req.document_ids.length} documents.`
      : `Insufficient comparative evidence found for topic "${res.topic}".`;

    return {
      id: res.comparison_id,
      workspace_id: workspaceId,
      comparison_topic: res.topic,
      document_ids: req.document_ids,
      summary,
      agreements,
      disagreements,
      omissions,
      insufficient_evidence: res.comparison_status === 'insufficient_evidence',
      created_at: new Date().toISOString(),
    };
  },

  // History
  async listHistory(workspaceId: string, limit: number = 50, offset: number = 0): Promise<HistoryListResponse> {
    const data = await apiFetch<any>(`/workspaces/${workspaceId}/history?limit=${limit}&offset=${offset}`);
    const rawItems: any[] = Array.isArray(data) ? data : data.items || [];
    const items: QueryRun[] = rawItems.map((r: any) => {
      const runId = r.id || r.query_id || '';
      const runQuestion = r.question || r.query_text || 'Untitled Question';
      const answerText = r.answer_text || (typeof r.answer === 'string' ? r.answer : r.answer?.answer_text);

      const mappedCitations: Citation[] = (r.citations || []).map((c: any, idx: number) => ({
        citation_index: idx + 1,
        document_id: c.document_id,
        document_title: c.document_filename || 'Source Document',
        page_number: c.page_number,
        chunk_id: c.citation_id || c.chunk_id || '',
        excerpt: c.cited_excerpt || c.excerpt || '',
        confidence: c.is_verified ? 0.98 : 0.65,
        validation_status: c.is_verified ? 'verified' : (c.is_repaired ? 'repaired' : 'unverified'),
      }));

      const ans = answerText ? {
        query_run_id: runId,
        question: runQuestion,
        answer_text: answerText,
        evidence_status: r.evidence_status || 'supported',
        citations: mappedCitations,
        retrieved_evidence: [],
        insufficient_evidence: r.evidence_status === 'insufficient_evidence',
        has_conflicts: r.evidence_status === 'conflicting_evidence',
        confidence_score: 0.9,
      } : undefined;

      return {
        id: runId,
        workspace_id: r.workspace_id,
        question: runQuestion,
        document_ids: r.selected_doc_ids || [],
        evidence_status: r.evidence_status,
        answer: ans,
        citations: mappedCitations,
        created_at: r.created_at,
        is_saved: r.is_saved ?? true,
      };
    });

    return { items, total: items.length };
  },

  async deleteQueryRun(workspaceId: string, queryId: string): Promise<void> {
    await apiFetch<void>(`/workspaces/${workspaceId}/history/${queryId}`, {
      method: 'DELETE',
    });
  },

  async clearHistory(workspaceId: string): Promise<void> {
    await apiFetch<void>(`/workspaces/${workspaceId}/history`, {
      method: 'DELETE',
    });
  },

  async toggleSaveQueryRun(workspaceId: string, queryId: string): Promise<{ query_id: string; is_saved: boolean }> {
    return apiFetch<{ query_id: string; is_saved: boolean }>(`/workspaces/${workspaceId}/history/${queryId}/save`, {
      method: 'POST',
    });
  },

  // Evaluation
  async listEvaluationRuns(workspaceId: string): Promise<EvaluationRunListResponse> {
    const data = await apiFetch<any>(`/workspaces/${workspaceId}/evaluation/runs`);
    const rawRuns: any[] = Array.isArray(data) ? data : data.runs || [];
    const runs: EvaluationRun[] = rawRuns.map((r: any) => ({
      id: r.id,
      workspace_id: r.workspace_id,
      status: r.total_cases > 0 && r.passed_cases === r.total_cases ? 'Passed' : (r.total_cases > 0 ? 'Completed' : 'Not Evaluated'),
      total_cases: r.total_cases ?? 0,
      passed_cases: r.passed_cases ?? 0,
      failed_cases: r.failed_cases ?? 0,
      metrics: {
        retrieval_recall: r.metrics?.recall_at_k ?? r.recall_at_k ?? 0.0,
        citation_accuracy: r.metrics?.citation_validity_rate ?? r.citation_validity_rate ?? 0.0,
        abstention_accuracy: r.metrics?.abstention_accuracy ?? r.abstention_accuracy ?? 0.0,
        hallucination_rate: r.metrics?.hallucination_rate ?? 0.0,
        precision_at_k: r.metrics?.precision_at_k ?? r.precision_at_k ?? 0.0,
      },
      details: r.case_results || [],
      created_at: r.created_at,
    }));
    return { runs, total: runs.length };
  },

  async runEvaluation(workspaceId: string): Promise<EvaluationRun> {
    const r = await apiFetch<any>(`/workspaces/${workspaceId}/evaluation/run`, {
      method: 'POST',
    });
    return {
      id: r.id,
      workspace_id: r.workspace_id,
      status: r.total_cases > 0 && r.passed_cases === r.total_cases ? 'Passed' : 'Completed',
      total_cases: r.total_cases ?? 0,
      passed_cases: r.passed_cases ?? 0,
      failed_cases: r.failed_cases ?? 0,
      metrics: {
        retrieval_recall: r.metrics?.recall_at_k ?? r.recall_at_k ?? 0.0,
        citation_accuracy: r.metrics?.citation_validity_rate ?? r.citation_validity_rate ?? 0.0,
        abstention_accuracy: r.metrics?.abstention_accuracy ?? r.abstention_accuracy ?? 0.0,
        hallucination_rate: r.metrics?.hallucination_rate ?? 0.0,
        precision_at_k: r.metrics?.precision_at_k ?? r.precision_at_k ?? 0.0,
      },
      details: r.case_results || [],
      created_at: r.created_at,
    };
  },
  async getLiveEvaluation(workspaceId: string): Promise<LiveEvaluationSummary> {
    const data = await apiFetch<any>(`/workspaces/${workspaceId}/evaluation/live`);
    return {
      workspace_id: data.workspace_id || workspaceId,
      total_queries: data.total_queries ?? 0,
      supported_queries: data.supported_queries ?? 0,
      abstention_queries: data.abstention_queries ?? 0,
      citation_validity_rate: data.citation_validity_rate ?? 0.0,
      abstention_rate: data.abstention_rate ?? 0.0,
      hallucination_rate: data.hallucination_rate ?? 0.0,
      avg_latency_ms: data.avg_latency_ms ?? 0.0,
      evaluated_queries: Array.isArray(data.evaluated_queries) ? data.evaluated_queries : [],
    };
  },
};
