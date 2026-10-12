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
} from 'lucide-react';

export default function QAPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
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

      const res = await api.askQuestion(workspaceId, {
        question: question.trim(),
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      });

      setAnswer(res);
    } catch (err: any) {
      setError(err.message || 'Failed to process inquiry.');
    } finally {
      setLoading(false);
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
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Evidence Scope
            </span>
            <span className="text-xs text-slate-500">
              ({selectedDocIds.length} of {documents.length} documents selected)
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedDocIds(documents.map((d) => d.id))}
              className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300"
            >
              Select All
            </button>
            <span className="text-slate-700">|</span>
            <button
              onClick={() => setSelectedDocIds([])}
              className="text-[11px] font-medium text-slate-400 hover:text-slate-300"
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
                      ? 'border-indigo-500/50 bg-indigo-600/20 text-indigo-200'
                      : 'border-slate-800 bg-slate-900/50 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span className="max-w-[200px] truncate">{doc.filename}</span>
                  <span className="text-[10px] text-slate-500">({doc.page_count}p)</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Question Form */}
      <form onSubmit={handleAsk} className="relative">
        <div className="relative rounded-2xl border border-slate-800 bg-slate-900/40 p-2 focus-within:border-indigo-500/80 focus-within:ring-1 focus-within:ring-indigo-500/50">
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
            className="w-full resize-none bg-transparent p-3 text-sm text-white placeholder-slate-500 focus:outline-none"
          />
          <div className="flex items-center justify-between border-t border-slate-800/80 px-3 pt-2">
            <span className="text-[11px] text-slate-500">
              Press <kbd className="rounded bg-slate-800 px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to submit
            </span>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 transition hover:bg-indigo-500 active:scale-95 disabled:opacity-40"
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
        <div className="rounded-xl border border-rose-900/50 bg-rose-950/30 p-4 text-xs text-rose-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-rose-400" />
            <span className="font-semibold">Query Execution Error</span>
          </div>
          <p className="mt-1 text-rose-400/90">{error}</p>
        </div>
      )}

      {/* Answer Output View */}
      {answer && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl">
            {/* Answer Header Badges */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                {answer.insufficient_evidence ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-300">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Abstention: Insufficient Evidence
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Grounded with Verifiable Citations
                  </span>
                )}

                {answer.has_conflicts && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-300">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Conflicting Claims Detected
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span>Confidence:</span>
                <div className="flex items-center gap-1 font-mono font-bold text-white">
                  <span>{Math.round(answer.confidence_score * 100)}%</span>
                  <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-800">
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
            <div className="mt-6 text-sm leading-relaxed text-slate-200">
              <div className="whitespace-pre-line font-sans">{answer.answer_text}</div>
            </div>

            {/* Honest Abstention Note */}
            {answer.insufficient_evidence && (
              <div className="mt-6 rounded-xl border border-amber-500/20 bg-amber-950/20 p-4 text-xs text-amber-300">
                <p className="font-semibold text-amber-200">Evidence Guardrail Engaged</p>
                <p className="mt-1 leading-relaxed text-amber-400/90">
                  ProofLens prioritized evidence over speculation. The indexed documents do not contain explicit facts to reliably answer this question without ungrounded extrapolation.
                </p>
              </div>
            )}
          </div>

          {/* Citations Grid */}
          {answer.citations && answer.citations.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-2">
                  <Bookmark className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">
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
                    className="flex flex-col justify-between rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 transition hover:border-slate-700"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600/20 text-xs font-bold text-indigo-400">
                          [{c.citation_index}]
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-300">
                            Page {c.page_number}
                          </span>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                              c.validation_status === 'verified'
                                ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/50'
                                : 'bg-amber-950/80 text-amber-300 border border-amber-800/50'
                            }`}
                          >
                            {c.validation_status}
                          </span>
                        </div>
                      </div>

                      <div className="mt-2.5 font-medium text-xs text-slate-300 truncate" title={c.document_title}>
                        {c.document_title}
                      </div>

                      <blockquote className="mt-2 text-xs italic text-slate-400 border-l-2 border-indigo-500/40 pl-2.5 leading-relaxed">
                        &ldquo;{c.excerpt}&rdquo;
                      </blockquote>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-800/40 pt-2 text-[10px] text-slate-500 font-mono">
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
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/20 p-4">
              <button
                onClick={() => setShowRetrievedEvidence(!showRetrievedEvidence)}
                className="flex w-full items-center justify-between text-xs font-medium text-slate-400 hover:text-white"
              >
                <span>Inspect All Retrieved Source Passages ({answer.retrieved_evidence.length})</span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${showRetrievedEvidence ? 'rotate-180' : ''}`}
                />
              </button>

              {showRetrievedEvidence && (
                <div className="mt-4 space-y-3 pt-3 border-t border-slate-800/60">
                  {answer.retrieved_evidence.map((ev, i) => (
                    <div key={i} className="rounded-lg bg-slate-950/80 p-3 text-xs border border-slate-800">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                        <span className="font-semibold text-slate-300">{ev.document_title} (p. {ev.page_number})</span>
                        <span className="font-mono text-slate-500">Relevance: {(ev.relevance_score * 100).toFixed(1)}%</span>
                      </div>
                      <p className="text-slate-400 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
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
