'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Document, DocumentSummaryResponse } from '@/lib/types/api';
import {
  UploadCloud,
  FileText,
  Trash2,
  RefreshCw,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  X,
  FileCheck,
  ChevronRight,
} from 'lucide-react';

export default function DocumentsPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Summary modal state
  const [selectedDocSummary, setSelectedDocSummary] = useState<DocumentSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [activeDocForSummary, setActiveDocForSummary] = useState<Document | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const res = await api.listDocuments(workspaceId);
      setDocuments(res.documents);
    } catch (err: any) {
      console.error('Failed to list documents:', err);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // Polling for processing documents
  useEffect(() => {
    const hasProcessing = documents.some((d) =>
      ['pending', 'extracting', 'chunking', 'embedding'].includes(d.processing_status)
    );

    if (!hasProcessing) return;

    const interval = setInterval(() => {
      loadDocuments();
    }, 2500);

    return () => clearInterval(interval);
  }, [documents, loadDocuments]);

  async function handleFileUpload(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF documents are supported.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File exceeds maximum 10MB limit.');
      return;
    }

    try {
      setError(null);
      setUploading(true);
      setUploadProgress(`Uploading ${file.name}...`);
      const newDoc = await api.uploadDocument(workspaceId, file);
      setDocuments((prev) => [newDoc, ...prev]);
      setUploadProgress('Document uploaded. Processing pipeline active...');
      setTimeout(() => {
        setUploadProgress(null);
        setUploading(false);
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Upload failed.');
      setUploading(false);
      setUploadProgress(null);
    }
  }

  async function handleDelete(docId: string) {
    if (!confirm('Are you sure you want to permanently delete this document and all its indexed chunks?')) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert(`Deletion failed: ${err.message}`);
    }
  }

  async function handleRetry(docId: string) {
    try {
      const updated = await api.retryDocument(docId);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? updated : d)));
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    }
  }

  async function handleOpenSummary(doc: Document) {
    setActiveDocForSummary(doc);
    setSummaryLoading(true);
    setSelectedDocSummary(null);
    try {
      const summary = await api.getDocumentSummary(doc.id);
      setSelectedDocSummary(summary);
    } catch (err: any) {
      alert(`Could not generate summary: ${err.message}`);
      setActiveDocForSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }

  function formatBytes(bytes: number) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function getStatusBadge(status: string, errorMsg?: string | null) {
    switch (status) {
      case 'ready':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
            <CheckCircle2 className="h-3 w-3" />
            Ready
          </span>
        );
      case 'unsupported':
        return (
          <span
            title={errorMsg || 'Unsupported or text-empty PDF (e.g. scanned without OCR)'}
            className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700"
          >
            <AlertTriangle className="h-3 w-3" />
            Unsupported
          </span>
        );
      case 'failed':
        return (
          <span
            title={errorMsg || 'Extraction or embedding error'}
            className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-0.5 text-xs font-medium text-rose-700"
          >
            <AlertTriangle className="h-3 w-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
            <Clock className="h-3 w-3 animate-spin" />
            {status.charAt(0).toUpperCase() + status.slice(1)}...
          </span>
        );
    }
  }

  return (
    <div className="space-y-8">
      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
        }}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
        className="group relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed border-slate-300 bg-white p-8 text-center shadow-sm transition-all hover:border-indigo-400 hover:bg-indigo-50/20"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />
        <div className="flex flex-col items-center justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition group-hover:scale-110 group-hover:bg-indigo-100">
            <UploadCloud className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">
            Upload PDF Document
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Drag and drop your file here, or click to browse. Max 10MB per PDF.
          </p>
          <div className="mt-4 flex items-center gap-2 text-[11px] text-slate-500">
            <FileCheck className="h-3.5 w-3.5 text-indigo-600" />
            <span>Extracts text with 1-based page provenance & vector embeddings</span>
          </div>
        </div>

        {uploadProgress && (
          <div className="mt-4 rounded-lg bg-indigo-50 p-2 text-xs font-medium text-indigo-700">
            {uploadProgress}
          </div>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-900">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Documents Table */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Document Library</h2>
            <p className="text-xs text-slate-500">Indexed PDFs available for retrieval & cross-examination</p>
          </div>
          <button
            onClick={loadDocuments}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            <RefreshCw className="h-3 w-3" />
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading library...</div>
        ) : documents.length === 0 ? (
          <div className="py-16 text-center">
            <FileText className="mx-auto h-10 w-10 text-slate-300" />
            <p className="mt-3 text-sm font-medium text-slate-700">No documents in this workspace yet</p>
            <p className="mt-1 text-xs text-slate-500">Upload a PDF above to begin evidence extraction.</p>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="pb-3 font-semibold">Document</th>
                  <th className="pb-3 font-semibold">Size</th>
                  <th className="pb-3 font-semibold">Pages</th>
                  <th className="pb-3 font-semibold">Chunks</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition">
                    <td className="py-3.5 pr-4">
                      <div className="flex items-center gap-2.5">
                        <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div className="max-w-[240px] truncate sm:max-w-xs">
                          <div className="font-medium text-slate-900 truncate" title={doc.filename}>
                            {doc.filename}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {new Date(doc.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 text-slate-600 font-mono">
                      {formatBytes(doc.file_size)}
                    </td>
                    <td className="py-3.5 text-slate-600 font-mono">
                      {doc.page_count ?? '—'}
                    </td>
                    <td className="py-3.5 text-slate-600 font-mono">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3.5">
                      {getStatusBadge(doc.processing_status, doc.error_message)}
                    </td>
                    <td className="py-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {doc.processing_status === 'ready' && (
                          <button
                            onClick={() => handleOpenSummary(doc)}
                            className="flex items-center gap-1 rounded-md bg-indigo-50 px-2 py-1 text-[11px] font-medium text-indigo-700 hover:bg-indigo-100 transition"
                            title="Generate/view executive summary"
                          >
                            <Sparkles className="h-3 w-3" />
                            Summary
                          </button>
                        )}
                        {['failed', 'unsupported'].includes(doc.processing_status) && (
                          <button
                            onClick={() => handleRetry(doc.id)}
                            className="rounded-md border border-slate-200 p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                            title="Retry processing"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="rounded-md border border-slate-200 p-1 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary Slide-over / Modal */}
      {activeDocForSummary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900">Document Intelligence Summary</h3>
                  <p className="text-xs text-slate-500 truncate max-w-md">{activeDocForSummary.filename}</p>
                </div>
              </div>
              <button
                onClick={() => setActiveDocForSummary(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {summaryLoading ? (
              <div className="py-16 text-center text-sm text-slate-500 flex flex-col items-center gap-3">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
                <span>Generating evidence summary & extracting suggested questions...</span>
              </div>
            ) : selectedDocSummary ? (
              <div className="mt-6 space-y-6 text-sm">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Executive Summary</h4>
                  <p className="mt-2 text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200">
                    {selectedDocSummary.executive_summary}
                  </p>
                </div>

                {selectedDocSummary.key_findings && selectedDocSummary.key_findings.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Key Findings</h4>
                    <ul className="mt-2 space-y-2">
                      {selectedDocSummary.key_findings.map((finding, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-slate-700">
                          <span className="h-1.5 w-1.5 rounded-full bg-indigo-600 mt-2 shrink-0" />
                          <span>{finding}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedDocSummary.suggested_questions && selectedDocSummary.suggested_questions.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Suggested Inquiries</h4>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectedDocSummary.suggested_questions.map((q, idx) => (
                        <span
                          key={idx}
                          className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs text-indigo-700 font-medium"
                        >
                          {q}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
