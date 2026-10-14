'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { QueryRun, Citation } from '@/lib/types/api';
import {
  History,
  Calendar,
  MessageSquare,
  ShieldCheck,
  AlertTriangle,
  Bookmark,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  Trash2,
} from 'lucide-react';

export default function HistoryPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [historyItems, setHistoryItems] = useState<QueryRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, [workspaceId]);

  async function loadHistory() {
    try {
      setLoading(true);
      const res = await api.listHistory(workspaceId);
      setHistoryItems(res.items);
    } catch (err: any) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(queryId: string) {
    if (!window.confirm('Delete this question and answer from history?')) return;
    try {
      await api.deleteQueryRun(workspaceId, queryId);
      setHistoryItems((prev) => prev.filter((i) => i.id !== queryId));
    } catch (err: any) {
      alert(`Failed to delete history item: ${err.message}`);
    }
  }

  async function handleClearAll() {
    if (!window.confirm('Are you sure you want to clear ALL query history for this workspace?')) return;
    try {
      await api.clearHistory(workspaceId);
      setHistoryItems([]);
    } catch (err: any) {
      alert(`Failed to clear history: ${err.message}`);
    }
  }

  async function handleToggleSave(queryId: string) {
    try {
      const res = await api.toggleSaveQueryRun(workspaceId, queryId);
      setHistoryItems((prev) =>
        prev.map((i) => (i.id === queryId ? { ...i, is_saved: res.is_saved } : i))
      );
    } catch (err: any) {
      console.error('Failed to toggle save:', err);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-2 text-indigo-600">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Provenance & Query History</h2>
            <p className="text-xs text-slate-500">
              Audit log of questions asked, verified citations, and saved grounded answers.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {historyItems.length > 0 && (
            <button
              onClick={handleClearAll}
              className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-2.5 py-1 text-xs text-rose-600 hover:bg-rose-50 shadow-xs transition"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear All</span>
            </button>
          )}
          <button
            onClick={loadHistory}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 hover:text-slate-900 shadow-xs transition"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading audit log...</div>
      ) : historyItems.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center shadow-xs">
          <MessageSquare className="mx-auto h-10 w-10 text-slate-400" />
          <p className="mt-3 text-sm font-medium text-slate-700">No query history in this workspace yet</p>
          <p className="mt-1 text-xs text-slate-500">Questions submitted in the Grounded Q&A tab will be logged and accessible here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {historyItems.map((item) => {
            const isExpanded = expandedRunId === item.id;
            return (
              <div
                key={item.id}
                className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs transition hover:border-slate-300 hover:shadow-sm"
              >
                <div
                  onClick={() => setExpandedRunId(isExpanded ? null : item.id)}
                  className="flex cursor-pointer items-center justify-between p-5"
                >
                  <div className="space-y-1.5 max-w-2xl">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-slate-500">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                      {item.answer?.insufficient_evidence ? (
                        <span className="rounded bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-200">
                          Abstention
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-200">
                          Grounded
                        </span>
                      )}
                      {item.citations && item.citations.length > 0 && (
                        <span className="text-[11px] font-mono text-slate-500">
                          {item.citations.length} citation{item.citations.length === 1 ? '' : 's'}
                        </span>
                      )}
                      {item.is_saved && (
                        <span className="rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 border border-indigo-200">
                          Saved
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-900">{item.question}</h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleSave(item.id);
                      }}
                      title={item.is_saved ? "Remove bookmark" : "Save / Bookmark"}
                      className={`rounded-lg p-1.5 transition ${
                        item.is_saved
                          ? 'text-amber-500 bg-amber-50 hover:bg-amber-100'
                          : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'
                      }`}
                    >
                      <Bookmark className={`h-4 w-4 ${item.is_saved ? 'fill-amber-500' : ''}`} />
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(item.id);
                      }}
                      title="Delete question and answer from history"
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>

                    <ChevronDown
                      className={`h-4 w-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180 text-indigo-600' : ''
                      }`}
                    />
                  </div>
                </div>

                {/* Expanded Answer and Citations */}
                {isExpanded && (
                  <div className="border-t border-slate-100 bg-slate-50/70 p-5 space-y-4 text-xs">
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-slate-500 text-[10px]">
                        Recorded Answer
                      </span>
                      <p className="mt-1.5 text-slate-800 leading-relaxed whitespace-pre-line text-sm">
                        {item.answer?.answer_text || '(No answer recorded for this query)'}
                      </p>
                    </div>

                    {item.citations && item.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-200/80">
                        <span className="font-semibold uppercase tracking-wider text-slate-500 text-[10px]">
                          Cited Provenance
                        </span>
                        <div className="mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                          {item.citations.map((c, cIdx) => (
                            <div key={cIdx} className="rounded-lg border border-slate-200 bg-white p-3 shadow-xs">
                              <div className="flex items-center justify-between text-[11px] font-mono text-indigo-600 mb-1">
                                <span>[{c.citation_index}] Page {c.page_number}</span>
                                <span className="text-slate-500">{c.validation_status}</span>
                              </div>
                              <p className="text-slate-700 italic text-[11px]">&ldquo;{c.excerpt}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
