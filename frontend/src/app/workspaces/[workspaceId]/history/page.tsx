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
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-indigo-600/20 p-2 text-indigo-400">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Provenance & Query Audit Trail</h2>
            <p className="text-xs text-slate-400">
              Complete audit log of questions asked, citations generated, and evidence retrieved.
            </p>
          </div>
        </div>
        <button
          onClick={loadHistory}
          className="flex items-center gap-1.5 rounded-lg border border-slate-800 px-2.5 py-1 text-xs text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          <RefreshCw className="h-3 w-3" />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading audit log...</div>
      ) : historyItems.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/20 py-16 text-center">
          <MessageSquare className="mx-auto h-10 w-10 text-slate-700" />
          <p className="mt-3 text-sm font-medium text-slate-400">No query history in this workspace yet</p>
          <p className="mt-1 text-xs text-slate-600">Questions submitted in the Grounded Q&A tab will be logged here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {historyItems.map((item) => {
            const isExpanded = expandedRunId === item.id;
            return (
              <div
                key={item.id}
                className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/40 transition hover:border-slate-700"
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
                        <span className="rounded bg-amber-950/60 px-2 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-800/40">
                          Abstention
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-950/60 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-800/40">
                          Grounded
                        </span>
                      )}
                      {item.citations && (
                        <span className="text-[11px] font-mono text-slate-400">
                          {item.citations.length} citation{item.citations.length === 1 ? '' : 's'}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-white">{item.question}</h3>
                  </div>

                  <div className="flex items-center gap-3">
                    <ChevronDown
                      className={`h-4 w-4 text-slate-500 transition-transform ${
                        isExpanded ? 'rotate-180 text-white' : ''
                      }`}
                    />
                  </div>
                </div>

                {/* Expanded Answer and Citations */}
                {isExpanded && item.answer && (
                  <div className="border-t border-slate-800/80 bg-slate-950/70 p-5 space-y-4 text-xs">
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-slate-400 text-[10px]">
                        Recorded Answer
                      </span>
                      <p className="mt-1.5 text-slate-300 leading-relaxed whitespace-pre-line text-sm">
                        {item.answer.answer_text}
                      </p>
                    </div>

                    {item.citations && item.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-800/60">
                        <span className="font-semibold uppercase tracking-wider text-slate-400 text-[10px]">
                          Cited Provenance
                        </span>
                        <div className="mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                          {item.citations.map((c, cIdx) => (
                            <div key={cIdx} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                              <div className="flex items-center justify-between text-[11px] font-mono text-indigo-400 mb-1">
                                <span>[{c.citation_index}] Page {c.page_number}</span>
                                <span className="text-slate-500">{c.validation_status}</span>
                              </div>
                              <p className="text-slate-300 italic text-[11px]">&ldquo;{c.excerpt}&rdquo;</p>
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
