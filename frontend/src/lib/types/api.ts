export interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
  total: number;
}

export interface Document {
  id: string;
  workspace_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  processing_status: 'pending' | 'extracting' | 'chunking' | 'embedding' | 'ready' | 'failed' | 'unsupported';
  page_count: number | null;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentSummaryResponse {
  document_id: string;
  executive_summary: string;
  key_findings: string[];
  suggested_questions: string[];
}

export interface Citation {
  citation_index: number;
  document_id: string;
  document_title: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
  confidence: number;
  validation_status: string;
}

export interface RetrievedEvidence {
  chunk_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  chunk_text: string;
  relevance_score: number;
}

export interface AnswerResponse {
  query_run_id: string;
  question: string;
  answer_text: string;
  citations: Citation[];
  retrieved_evidence: RetrievedEvidence[];
  insufficient_evidence: boolean;
  has_conflicts: boolean;
  confidence_score: number;
  model_name: string;
}

export interface QuestionRequest {
  question: string;
  document_ids?: string[];
}

export interface CompareRequest {
  document_ids: string[];
  comparison_topic: string;
}

export interface ComparisonFinding {
  topic: string;
  description: string;
  citations: Citation[];
}

export interface ComparisonResponse {
  id: string;
  workspace_id: string;
  comparison_topic: string;
  document_ids: string[];
  summary: string;
  agreements: ComparisonFinding[];
  disagreements: ComparisonFinding[];
  omissions: ComparisonFinding[];
  insufficient_evidence: boolean;
  created_at: string;
}

export interface QueryRun {
  id: string;
  workspace_id: string;
  question: string;
  document_ids: string[];
  answer?: AnswerResponse;
  citations?: Citation[];
  created_at: string;
}

export interface HistoryListResponse {
  items: QueryRun[];
  total: number;
}

export interface EvaluationRun {
  id: string;
  workspace_id: string;
  status: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  metrics: Record<string, number>;
  details: any;
  created_at: string;
}

export interface EvaluationRunListResponse {
  runs: EvaluationRun[];
  total: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
