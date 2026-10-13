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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-2 text-indigo-600">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Provenance & Query Audit Trail</h2>
            <p className="text-xs text-slate-500">
              Complete audit log of questions asked, citations generated, and evidence retrieved.
            </p>
          </div>
        </div>
        <button
          onClick={loadHistory}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 hover:text-slate-900 shadow-xs"
        >
          <RefreshCw className="h-3 w-3" />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading audit log...</div>
      ) : historyItems.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center shadow-xs">
          <MessageSquare className="mx-auto h-10 w-10 text-slate-400" />
          <p className="mt-3 text-sm font-medium text-slate-700">No query history in this workspace yet</p>
          <p className="mt-1 text-xs text-slate-500">Questions submitted in the Grounded Q&A tab will be logged here.</p>
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
                      {item.citations && (
                        <span className="text-[11px] font-mono text-slate-500">
                          {item.citations.length} citation{item.citations.length === 1 ? '' : 's'}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-900">{item.question}</h3>
                  </div>

                  <div className="flex items-center gap-3">
                    <ChevronDown
                      className={`h-4 w-4 text-slate-400 transition-transform ${
                        isExpanded ? 'rotate-180 text-indigo-600' : ''
                      }`}
                    />
                  </div>
                </div>

                {/* Expanded Answer and Citations */}
                {isExpanded && item.answer && (
                  <div className="border-t border-slate-100 bg-slate-50/70 p-5 space-y-4 text-xs">
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-slate-500 text-[10px]">
                        Recorded Answer
                      </span>
                      <p className="mt-1.5 text-slate-800 leading-relaxed whitespace-pre-line text-sm">
                        {item.answer.answer_text}
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
