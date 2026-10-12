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
  HistoryListResponse,
  EvaluationRun,
  EvaluationRunListResponse,
} from '../types/api';

export const api = {
  // Workspaces
  async listWorkspaces(): Promise<WorkspaceListResponse> {
    return apiFetch<WorkspaceListResponse>('/workspaces');
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

  // Documents
  async listDocuments(workspaceId: string): Promise<DocumentListResponse> {
    return apiFetch<DocumentListResponse>(`/workspaces/${workspaceId}/documents`);
  },

  async uploadDocument(workspaceId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    return apiFetch<Document>(`/workspaces/${workspaceId}/documents`, {
      method: 'POST',
      body: formData,
    });
  },

  async getDocument(documentId: string): Promise<Document> {
    return apiFetch<Document>(`/documents/${documentId}`);
  },

  async deleteDocument(documentId: string): Promise<void> {
    await apiFetch<void>(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  async retryDocument(documentId: string): Promise<Document> {
    return apiFetch<Document>(`/documents/${documentId}/retry`, {
      method: 'POST',
    });
  },

  // Summaries
  async getDocumentSummary(documentId: string): Promise<DocumentSummaryResponse> {
    return apiFetch<DocumentSummaryResponse>(`/documents/${documentId}/summary`);
  },

  // Q&A
  async askQuestion(workspaceId: string, req: QuestionRequest): Promise<AnswerResponse> {
    return apiFetch<AnswerResponse>(`/workspaces/${workspaceId}/qa`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  // Comparison
  async compareDocuments(workspaceId: string, req: CompareRequest): Promise<ComparisonResponse> {
    return apiFetch<ComparisonResponse>(`/workspaces/${workspaceId}/compare`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  // History
  async listHistory(workspaceId: string, limit: number = 50, offset: number = 0): Promise<HistoryListResponse> {
    return apiFetch<HistoryListResponse>(`/workspaces/${workspaceId}/history?limit=${limit}&offset=${offset}`);
  },

  // Evaluation
  async listEvaluationRuns(workspaceId: string): Promise<EvaluationRunListResponse> {
    return apiFetch<EvaluationRunListResponse>(`/workspaces/${workspaceId}/evaluation/runs`);
  },

  async runEvaluation(workspaceId: string): Promise<EvaluationRun> {
    return apiFetch<EvaluationRun>(`/workspaces/${workspaceId}/evaluation/run`, {
      method: 'POST',
    });
  },
};
