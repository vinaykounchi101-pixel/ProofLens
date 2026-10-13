'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { EvaluationRun } from '@/lib/types/api';
import {
  Activity,
  Play,
  CheckCircle2,
  AlertTriangle,
  Shield,
  Zap,
  BarChart3,
  RefreshCw,
  Clock,
} from 'lucide-react';

export default function EvaluationPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [activeRun, setActiveRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    loadRuns();
  }, [workspaceId]);

  async function loadRuns() {
    try {
      setLoading(true);
      const res = await api.listEvaluationRuns(workspaceId);
      setRuns(res.runs);
      if (res.runs.length > 0) {
        setActiveRun(res.runs[0]);
      }
    } catch (err: any) {
      console.error('Failed to load evaluation runs:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerEval() {
    try {
      setRunningEval(true);
      const newRun = await api.runEvaluation(workspaceId);
      setRuns((prev) => [newRun, ...prev]);
      setActiveRun(newRun);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setRunningEval(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-2 text-indigo-600">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">RAG Verification & Evaluation Suite</h2>
            <p className="text-xs text-slate-500">
              Benchmark retrieval recall, citation fidelity, honest abstention, and zero hallucination metrics.
            </p>
          </div>
        </div>

        <button
          onClick={handleTriggerEval}
          disabled={runningEval}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-500 active:scale-95 disabled:opacity-50"
        >
          {runningEval ? (
            <>
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Running Benchmark Suite...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5" />
              <span>Run Automated Benchmark</span>
            </>
          )}
        </button>
      </div>

      {/* Primary Metrics Overview (from latest or active run) */}
      {activeRun ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Metric 1: Retrieval Recall */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Retrieval Recall</span>
                <BarChart3 className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
                {((activeRun.metrics.retrieval_recall ?? 0.0) * 100).toFixed(1)}%
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Gold chunk match in top-k</p>
            </div>

            {/* Metric 2: Citation Accuracy */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Citation Precision</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-emerald-600">
                {((activeRun.metrics.citation_accuracy ?? 0.0) * 100).toFixed(1)}%
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Verified page-level quotes</p>
            </div>

            {/* Metric 3: Abstention Fidelity */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Abstention Accuracy</span>
                <Shield className="h-4 w-4 text-amber-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-amber-600">
                {((activeRun.metrics.abstention_accuracy ?? 0.0) * 100).toFixed(1)}%
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Refusal on no-evidence queries</p>
            </div>

            {/* Metric 4: Hallucination Rate */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Hallucination Rate</span>
                <Zap className="h-4 w-4 text-rose-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-rose-600">
                {((activeRun.metrics.hallucination_rate ?? 0.0) * 100).toFixed(1)}%
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Ungrounded claim occurrences</p>
            </div>
          </div>

          {/* Test Cases Results Detail */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <h3 className="text-sm font-semibold text-slate-900">Benchmark Execution Summary</h3>
            <div className="mt-4 flex flex-wrap gap-4 text-xs font-mono text-slate-600">
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                <span className="text-slate-500 block">Run Identifier</span>
                <span className="text-slate-800">{activeRun.id}</span>
              </div>
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                <span className="text-slate-500 block">Total Synthetic Scenarios</span>
                <span className="text-slate-800">{activeRun.total_cases} test cases</span>
              </div>
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                <span className="text-slate-500 block">Passed Validations</span>
                <span className="text-emerald-700 font-bold">{activeRun.passed_cases} passed</span>
              </div>
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                <span className="text-slate-500 block">Failed Validations</span>
                <span className="text-rose-700 font-bold">{activeRun.failed_cases} failed</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center shadow-xs">
          <Activity className="mx-auto h-10 w-10 text-slate-400" />
          <p className="mt-3 text-sm font-medium text-slate-700">No evaluation benchmarks recorded</p>
          <p className="mt-1 text-xs text-slate-500">
            Click &quot;Run Automated Benchmark&quot; to test this workspace against the evaluation test suite.
          </p>
        </div>
      )}

      {/* Historical Runs Table */}
      {runs.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-semibold text-slate-900">Benchmark History</h3>
            <span className="text-xs text-slate-500">{runs.length} runs</span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="pb-3 font-semibold">Date & Time</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Test Cases</th>
                  <th className="pb-3 font-semibold">Passed / Failed</th>
                  <th className="pb-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80">
                    <td className="py-3 text-slate-700">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="py-3">
                      <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-200">
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-600">{r.total_cases} cases</td>
                    <td className="py-3">
                      <span className="text-emerald-700 font-semibold">{r.passed_cases}</span> /{' '}
                      <span className="text-rose-700 font-semibold">{r.failed_cases}</span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => setActiveRun(r)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        Inspect Metrics
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
