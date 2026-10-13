'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Document, ComparisonResponse } from '@/lib/types/api';
import {
  GitCompare,
  ArrowRight,
  FileText,
  CheckCircle2,
  AlertTriangle,
  MinusCircle,
  HelpCircle,
  Bookmark,
  Layers,
  Send,
} from 'lucide-react';

export default function ComparePage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparisonTopic, setComparisonTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDocuments(workspaceId).then((res) => {
      const readyDocs = res.documents.filter((d) => d.processing_status === 'ready');
      setDocuments(readyDocs);
      if (readyDocs.length >= 2) {
        setSelectedDocIds([readyDocs[0].id, readyDocs[1].id]);
      }
    });
  }, [workspaceId]);

  function toggleDocSelection(docId: string) {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  }

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    if (selectedDocIds.length < 2) {
      setError('Please select at least 2 documents for cross-document comparison.');
      return;
    }
    if (!comparisonTopic.trim()) {
      setError('Please provide a comparison topic or question.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const res = await api.compareDocuments(workspaceId, {
        document_ids: selectedDocIds,
        comparison_topic: comparisonTopic.trim(),
      });

      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Comparison execution failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-2 text-indigo-600">
            <GitCompare className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Cross-Document Comparison Matrix</h2>
            <p className="text-xs text-slate-500">
              Identify agreements, material contradictions, and omissions across multiple PDF sources.
            </p>
          </div>
        </div>
      </div>

      {/* Document Selector Bar */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
            Select Documents to Compare (Min 2)
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {selectedDocIds.length} selected
          </span>
        </div>

        {documents.length < 2 ? (
          <p className="mt-3 text-xs text-slate-500">
            You need at least two ready PDF documents in this workspace to perform cross-document comparisons.
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
                      ? 'border-indigo-300 bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span className="max-w-[200px] truncate">{doc.filename}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Comparison Form */}
      <form onSubmit={handleCompare} className="relative">
        <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-xs focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/10">
          <input
            type="text"
            placeholder="Comparison Topic (e.g. 'Payment terms, breach penalty clauses, termination rights')"
            value={comparisonTopic}
            onChange={(e) => setComparisonTopic(e.target.value)}
            className="w-full bg-transparent p-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
          />
          <div className="flex items-center justify-end border-t border-slate-100 px-3 pt-2">
            <button
              type="submit"
              disabled={loading || selectedDocIds.length < 2 || !comparisonTopic.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-500 active:scale-95 disabled:opacity-40"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Comparing Sources...</span>
                </>
              ) : (
                <>
                  <GitCompare className="h-3.5 w-3.5" />
                  <span>Execute Comparison</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Error alert */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          {error}
        </div>
      )}

      {/* Comparison Results */}
      {result && (
        <div className="space-y-6">
          {/* Executive Synthesis */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-semibold text-slate-900">Comparative Synthesis</h3>
              <span className="text-[11px] font-mono text-slate-500">
                {result.document_ids.length} Sources Analyzed
              </span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200">
              {result.summary}
            </p>
          </div>

          {/* Three Column Matrix: Agreements, Disagreements, Omissions */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Agreements */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5">
              <div className="flex items-center gap-2 border-b border-emerald-200/60 pb-3 text-emerald-800">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Agreements ({result.agreements.length})</h4>
              </div>
              <div className="mt-4 space-y-3">
                {result.agreements.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No explicit common provisions detected.</p>
                ) : (
                  result.agreements.map((item, idx) => (
                    <div key={idx} className="rounded-xl border border-emerald-200 bg-white p-3.5 text-xs shadow-xs">
                      <p className="font-semibold text-emerald-800 mb-1">{item.topic}</p>
                      <p className="text-slate-600 leading-relaxed">{item.description}</p>
                      {item.citations && item.citations.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1 border-t border-slate-100 pt-2">
                          {item.citations.map((c, cIdx) => (
                            <span key={cIdx} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                              p.{c.page_number} ({c.document_title.slice(0, 15)}...)
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Discrepancies / Disagreements */}
            <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-5">
              <div className="flex items-center gap-2 border-b border-rose-200/60 pb-3 text-rose-800">
                <AlertTriangle className="h-4 w-4 text-rose-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Discrepancies ({result.disagreements.length})</h4>
              </div>
              <div className="mt-4 space-y-3">
                {result.disagreements.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No conflicting clauses detected.</p>
                ) : (
                  result.disagreements.map((item, idx) => (
                    <div key={idx} className="rounded-xl border border-rose-200 bg-white p-3.5 text-xs shadow-xs">
                      <p className="font-semibold text-rose-800 mb-1">{item.topic}</p>
                      <p className="text-slate-600 leading-relaxed">{item.description}</p>
                      {item.citations && item.citations.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1 border-t border-slate-100 pt-2">
                          {item.citations.map((c, cIdx) => (
                            <span key={cIdx} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                              p.{c.page_number} ({c.document_title.slice(0, 15)}...)
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Omissions */}
            <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-5">
              <div className="flex items-center gap-2 border-b border-amber-200/60 pb-3 text-amber-800">
                <MinusCircle className="h-4 w-4 text-amber-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Omissions ({result.omissions.length})</h4>
              </div>
              <div className="mt-4 space-y-3">
                {result.omissions.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No one-sided omissions identified.</p>
                ) : (
                  result.omissions.map((item, idx) => (
                    <div key={idx} className="rounded-xl border border-amber-200 bg-white p-3.5 text-xs shadow-xs">
                      <p className="font-semibold text-amber-800 mb-1">{item.topic}</p>
                      <p className="text-slate-600 leading-relaxed">{item.description}</p>
                      {item.citations && item.citations.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1 border-t border-slate-100 pt-2">
                          {item.citations.map((c, cIdx) => (
                            <span key={cIdx} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                              p.{c.page_number} ({c.document_title.slice(0, 15)}...)
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
