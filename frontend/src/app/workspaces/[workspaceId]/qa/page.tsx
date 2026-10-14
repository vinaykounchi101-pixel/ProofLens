'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Document, AnswerResponse, Citation } from '@/lib/types/api';
import {
  MessageSquareQuote,
  Send,
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  FileText,
  CheckCircle2,
  Bookmark,
  ExternalLink,
  ChevronDown,
  Layers,
  Sparkles,
  Trash2,
} from 'lucide-react';

export default function QAPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [isSaved, setIsSaved] = useState(true);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRetrievedEvidence, setShowRetrievedEvidence] = useState(false);

  useEffect(() => {
    api.listDocuments(workspaceId).then((res) => {
      const readyDocs = res.documents.filter((d) => d.processing_status === 'ready');
      setDocuments(readyDocs);
      // Default to all ready documents
      setSelectedDocIds(readyDocs.map((d) => d.id));
    });
  }, [workspaceId]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setAnswer(null);
      setSaveNotice(null);

      const res = await api.askQuestion(workspaceId, {
        question: question.trim(),
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      });

      setAnswer(res);
      setIsSaved(true);
    } catch (err: any) {
      setError(err.message || 'Failed to process inquiry.');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleSave() {
    if (!answer?.query_run_id) return;
    try {
      const res = await api.toggleSaveQueryRun(workspaceId, answer.query_run_id);
      setIsSaved(res.is_saved);
      setSaveNotice(res.is_saved ? 'Answer saved to query history!' : 'Removed from saved history.');
      setTimeout(() => setSaveNotice(null), 3000);
    } catch (err: any) {
      console.error('Failed to toggle save:', err);
    }
  }

  async function handleDeleteConversation() {
    if (!window.confirm('Delete this conversation? This will clear the screen and remove this record from history.')) {
      return;
    }
    try {
      if (answer?.query_run_id) {
        await api.deleteQueryRun(workspaceId, answer.query_run_id);
      }
    } catch (err: any) {
      console.error('Failed to delete query run from server:', err);
    } finally {
      setAnswer(null);
      setQuestion('');
    }
  }

  function toggleDocSelection(docId: string) {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  }

  return (
    <div className="space-y-8">
      {/* Scope Selector Bar */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-600" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Evidence Scope
            </span>
            <span className="text-xs text-slate-500">
              ({selectedDocIds.length} of {documents.length} documents selected)
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedDocIds(documents.map((d) => d.id))}
              className="text-[11px] font-medium text-indigo-600 hover:text-indigo-700"
            >
              Select All
            </button>
            <span className="text-slate-300">|</span>
            <button
              onClick={() => setSelectedDocIds([])}
              className="text-[11px] font-medium text-slate-500 hover:text-slate-700"
            >
              Clear
            </button>
          </div>
        </div>

        {documents.length === 0 ? (
          <p className="mt-3 text-xs text-slate-500">
            No ready documents found. Please upload and process PDFs in the Documents tab first.
          </p>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
            {documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <button
                  key={doc.id}
                  onClick={() => toggleDocSelection(doc.id)}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                    isSelected
                      ? 'border-indigo-300 bg-indigo-50 text-indigo-700 shadow-xs'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300 hover:text-slate-800'
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span className="max-w-[200px] truncate">{doc.filename}</span>
                  <span className="text-[10px] text-slate-400">({doc.page_count}p)</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Question Form */}
      <form onSubmit={handleAsk} className="relative">
        <div className="relative rounded-2xl border border-slate-300 bg-white p-2 shadow-sm transition focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-600/10">
          <textarea
            rows={3}
            placeholder="Ask a question grounded in the selected documents (e.g. 'What are the termination liabilities in Section 4?')"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk(e);
              }
            }}
            className="w-full resize-none bg-transparent p-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
          />
          <div className="flex items-center justify-between border-t border-slate-100 px-3 pt-2">
            <span className="text-[11px] text-slate-400">
              Press <kbd className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[10px] text-slate-600 border border-slate-200">Enter</kbd> to submit
            </span>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-95 disabled:opacity-40"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Retrieving & Grounding...</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Ask Question</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Error Display */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-rose-600" />
            <span className="font-semibold">Query Execution Error</span>
          </div>
          <p className="mt-1 text-rose-700">{error}</p>
        </div>
      )}

      {/* Answer Output View */}
      {answer && (
        <div className="space-y-4">
          {/* Conversation Actions Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-1">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleToggleSave}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition shadow-xs ${
                  isSaved
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                    : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Bookmark className={`h-3.5 w-3.5 ${isSaved ? 'fill-emerald-600 text-emerald-600' : ''}`} />
                <span>{isSaved ? 'Saved to History' : 'Save Query & Answer'}</span>
              </button>

              <button
                type="button"
                onClick={handleDeleteConversation}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 shadow-xs transition"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Conversation</span>
              </button>
            </div>

            {saveNotice && (
              <span className="text-xs font-medium text-emerald-600">
                ✓ {saveNotice}
              </span>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            {/* Answer Header Badges */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2">
                {answer.insufficient_evidence ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Abstention: Insufficient Evidence
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Grounded with Verifiable Citations
                  </span>
                )}

                {answer.has_conflicts && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Conflicting Claims Detected
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-500">
                <span>Confidence:</span>
                <div className="flex items-center gap-1 font-mono font-bold text-slate-800">
                  <span>{Math.round(answer.confidence_score * 100)}%</span>
                  <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-100 border border-slate-200">
                    <div
                      className={`h-full ${
                        answer.confidence_score > 0.75
                          ? 'bg-emerald-500'
                          : answer.confidence_score > 0.4
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${answer.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Answer Body */}
            <div className="mt-6 text-sm leading-relaxed text-slate-800">
              <div className="whitespace-pre-line font-sans">{answer.answer_text}</div>
            </div>

            {/* Honest Abstention Note */}
            {answer.insufficient_evidence && (
              <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
                <p className="font-semibold text-amber-900">Evidence Guardrail Engaged</p>
                <p className="mt-1 leading-relaxed text-amber-700">
                  ProofLens prioritized evidence over speculation. The indexed documents do not contain explicit facts to reliably answer this question without ungrounded extrapolation.
                </p>
              </div>
            )}
          </div>

          {/* Citations Grid */}
          {answer.citations && answer.citations.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <Bookmark className="h-4 w-4 text-indigo-600" />
                  <h3 className="text-sm font-semibold text-slate-900">
                    Page-Level Citations ({answer.citations.length})
                  </h3>
                </div>
                <span className="text-[11px] text-slate-500">
                  Every claim is tied to an indexed document and 1-based page number
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                {answer.citations.map((c, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/70 p-4 transition hover:border-indigo-300 hover:bg-white"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-indigo-100 text-xs font-bold text-indigo-700">
                          [{c.citation_index}]
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="rounded bg-slate-200/80 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-700">
                            Page {c.page_number}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                              c.validation_status === 'verified'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                          >
                            {c.validation_status}
                          </span>
                        </div>
                      </div>

                      <div className="mt-2.5 font-medium text-xs text-slate-800 truncate" title={c.document_title}>
                        {c.document_title}
                      </div>

                      <blockquote className="mt-2 text-xs italic text-slate-600 border-l-2 border-indigo-400 pl-2.5 leading-relaxed bg-white/60 p-2 rounded-r-md">
                        &ldquo;{c.excerpt}&rdquo;
                      </blockquote>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-200/60 pt-2 text-[10px] text-slate-500 font-mono">
                      <span>Chunk #{c.chunk_id.slice(0, 8)}</span>
                      <span>Match Score: {Math.round(c.confidence * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Toggle Retrieved Evidence / Chunks */}
          {answer.retrieved_evidence && answer.retrieved_evidence.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <button
                onClick={() => setShowRetrievedEvidence(!showRetrievedEvidence)}
                className="flex w-full items-center justify-between text-xs font-medium text-slate-600 hover:text-slate-900"
              >
                <span>Inspect All Retrieved Source Passages ({answer.retrieved_evidence.length})</span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${showRetrievedEvidence ? 'rotate-180' : ''}`}
                />
              </button>

              {showRetrievedEvidence && (
                <div className="mt-4 space-y-3 pt-3 border-t border-slate-100">
                  {answer.retrieved_evidence.map((ev, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 p-3 text-xs border border-slate-200">
                      <div className="flex items-center justify-between text-[11px] text-slate-600 mb-1">
                        <span className="font-semibold text-slate-800">{ev.document_title} (p. {ev.page_number})</span>
                        <span className="font-mono text-slate-500">Relevance: {(ev.relevance_score * 100).toFixed(1)}%</span>
                      </div>
                      <p className="text-slate-600 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                        {ev.chunk_text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
