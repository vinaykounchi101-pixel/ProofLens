'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { EvaluationRun, LiveEvaluationSummary } from '@/lib/types/api';
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
  HelpCircle,
  FileText,
  Sparkles,
  Database,
  Check,
  X,
  MessageSquare,
} from 'lucide-react';

export default function EvaluationPage() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [activeTab, setActiveTab] = useState<'live' | 'benchmark'>('live');
  const [liveSummary, setLiveSummary] = useState<LiveEvaluationSummary | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [activeRun, setActiveRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    loadAllData();
  }, [workspaceId]);

  async function loadAllData() {
    try {
      setLoading(true);
      const [liveData, runsData] = await Promise.all([
        api.getLiveEvaluation(workspaceId).catch(() => null),
        api.listEvaluationRuns(workspaceId).catch(() => ({ runs: [], total: 0 })),
      ]);

      if (liveData) {
        setLiveSummary(liveData);
      }
      setRuns(runsData.runs);
      if (runsData.runs.length > 0) {
        setActiveRun(runsData.runs[0]);
      }
    } catch (err: any) {
      console.error('Failed to load evaluation data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerBenchmark() {
    try {
      setRunningEval(true);
      const newRun = await api.runEvaluation(workspaceId);
      setRuns((prev) => [newRun, ...prev]);
      setActiveRun(newRun);
      setActiveTab('benchmark');
    } catch (err: any) {
      alert(`Benchmark execution failed: ${err.message}`);
    } finally {
      setRunningEval(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-50 border border-indigo-100 p-2.5 text-indigo-600 shadow-xs">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">RAG Verification & Evaluation Suite</h2>
            <p className="text-xs text-slate-500">
              Measure citation accuracy, truthful abstention, and zero hallucination on real user queries and synthetic benchmarks.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-xs hover:bg-slate-50 transition"
            title="Refresh Evaluation Metrics"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-indigo-600' : 'text-slate-500'}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleTriggerBenchmark}
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
                <span>Run Automated Benchmark (Dummy Scenarios)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Primary Tab Navigation */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('live')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeTab === 'live'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          <span>Live Workspace Inquiries</span>
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
            activeTab === 'live' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'
          }`}>
            {liveSummary?.total_queries ?? 0}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('benchmark')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeTab === 'benchmark'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          <span>Automated Benchmark Suite</span>
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
            activeTab === 'benchmark' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'
          }`}>
            {runs.length} runs
          </span>
        </button>
      </div>

      {/* TAB 1: LIVE USER QUERIES EVALUATION */}
      {activeTab === 'live' && (
        <div className="space-y-6">
          {/* Context Banner */}
          <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-indigo-900 flex items-start gap-3">
            <Shield className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Calculated from Real Questions Asked in this Workspace</span>
              <p className="mt-0.5 text-indigo-700">
                These quality metrics are dynamically calculated across all questions you have submitted in the Grounded Q&A tab, verifying genuine 1-based page citations, honest abstention on missing facts, and strict excerpt provenance.
              </p>
            </div>
          </div>

          {/* Metric Cards Row */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {/* Metric 1: Total Queries Evaluated */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Inquiries Evaluated</span>
                <MessageSquare className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
                {liveSummary?.total_queries ?? 0}
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                {liveSummary?.supported_queries ?? 0} supported &bull; {liveSummary?.abstention_queries ?? 0} refused
              </p>
            </div>

            {/* Metric 2: Citation Precision */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Citation Precision</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-emerald-600">
                {liveSummary && liveSummary.total_queries > 0
                  ? `${((liveSummary.citation_validity_rate ?? 0) * 100).toFixed(1)}%`
                  : '100.0%'}
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Verified page quotes</p>
            </div>

            {/* Metric 3: Abstention Fidelity */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Abstention Accuracy</span>
                <Shield className="h-4 w-4 text-amber-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-amber-600">
                {liveSummary && liveSummary.total_queries > 0
                  ? `${((liveSummary.abstention_rate ?? 0) * 100).toFixed(1)}%`
                  : '0.0%'}
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Faithfully refused no-evidence</p>
            </div>

            {/* Metric 4: Hallucination Rate */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Hallucination Rate</span>
                <Zap className="h-4 w-4 text-rose-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-rose-600">
                {((liveSummary?.hallucination_rate ?? 0) * 100).toFixed(1)}%
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Unverified claim occurrences</p>
            </div>

            {/* Metric 5: Average Latency */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Average Latency</span>
                <Clock className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-indigo-600">
                {liveSummary?.avg_latency_ms ? `${Math.round(liveSummary.avg_latency_ms)} ms` : '—'}
              </div>
              <p className="mt-1 text-[11px] text-slate-500">Mean RAG audit cycle</p>
            </div>
          </div>

          {/* Evaluated Questions List */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-semibold text-slate-900">Evaluated User Queries</h3>
              <span className="text-xs text-slate-500">{liveSummary?.evaluated_queries?.length ?? 0} questions recorded</span>
            </div>

            {liveSummary && liveSummary.evaluated_queries.length > 0 ? (
              <div className="mt-4 divide-y divide-slate-100">
                {liveSummary.evaluated_queries.map((q) => (
                  <div key={q.query_id} className="py-4 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                          q.evidence_status === 'supported'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : q.evidence_status === 'insufficient_evidence'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-blue-50 text-blue-700 border-blue-200'
                        }`}>
                          {q.evidence_status === 'supported' ? 'Fully Supported' : q.evidence_status === 'insufficient_evidence' ? 'Honest Abstention' : 'Partial Support'}
                        </span>
                        <h4 className="text-xs font-semibold text-slate-900">{q.question}</h4>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                        {q.latency_ms && <span>{q.latency_ms}ms</span>}
                        <span>{new Date(q.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    {q.answer_text && (
                      <p className="text-xs text-slate-600 line-clamp-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {q.answer_text}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500">
                      <span className="inline-flex items-center gap-1">
                        <Check className="h-3 w-3 text-emerald-600" />
                        <span>{q.valid_citations} of {q.total_citations} citations verified</span>
                      </span>

                      {q.has_hallucinations ? (
                        <span className="inline-flex items-center gap-1 text-rose-600 font-medium">
                          <X className="h-3 w-3" />
                          <span>Hallucination / unverified excerpt detected</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Zero hallucination</span>
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center">
                <HelpCircle className="mx-auto h-8 w-8 text-slate-300" />
                <p className="mt-2 text-xs font-medium text-slate-700">No questions asked yet in this workspace</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  Submit inquiries in the Grounded Q&A tab to see your questions automatically evaluated here.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: AUTOMATED BENCHMARK SUITE (DUMMY SCENARIOS) */}
      {activeTab === 'benchmark' && (
        <div className="space-y-6">
          {/* Explanation Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <span className="text-xs font-semibold text-slate-900 block">Synthetic 25-Case Benchmark Corpus</span>
              <p className="mt-0.5 text-xs text-slate-500">
                Runs pre-configured synthetic dummy questions (known gold-standard factual queries and out-of-scope abstention traps) to stress-test retrieval recall and boundary compliance.
              </p>
            </div>

            <button
              onClick={handleTriggerBenchmark}
              disabled={runningEval}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-500 active:scale-95 disabled:opacity-50 shrink-0"
            >
              {runningEval ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Executing Benchmark...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5" />
                  <span>Execute Benchmark Now</span>
                </>
              )}
            </button>
          </div>

          {/* Primary Metrics from Active Benchmark Run */}
          {activeRun ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {/* Metric 1: Retrieval Recall */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Retrieval Recall (k=3)</span>
                    <BarChart3 className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
                    {((activeRun.metrics.recall_at_k ?? activeRun.metrics.retrieval_recall ?? 0.0) * 100).toFixed(1)}%
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
                    {((activeRun.metrics.citation_validity_rate ?? activeRun.metrics.citation_accuracy ?? 0.0) * 100).toFixed(1)}%
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

                {/* Metric 4: Passed Test Scenarios */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Passed Scenarios</span>
                    <Check className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-slate-900">
                    {activeRun.passed_cases} / {activeRun.total_cases}
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {activeRun.failed_cases} scenario deviations
                  </p>
                </div>
              </div>

              {/* Benchmark Summary Box */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                <h3 className="text-sm font-semibold text-slate-900">Active Benchmark Run</h3>
                <div className="mt-4 flex flex-wrap gap-4 text-xs font-mono text-slate-600">
                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                    <span className="text-slate-500 block">Benchmark ID</span>
                    <span className="text-slate-800">{activeRun.id}</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                    <span className="text-slate-500 block">Corpus Scenarios</span>
                    <span className="text-slate-800">{activeRun.total_cases} dummy questions</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                    <span className="text-slate-500 block">Passed Validations</span>
                    <span className="text-emerald-700 font-bold">{activeRun.passed_cases} passed</span>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
                    <span className="text-slate-500 block">Executed At</span>
                    <span className="text-slate-800">{new Date(activeRun.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center shadow-xs">
              <Activity className="mx-auto h-10 w-10 text-slate-400" />
              <p className="mt-3 text-sm font-medium text-slate-700">No automated benchmark runs recorded yet</p>
              <p className="mt-1 text-xs text-slate-500">
                Click &quot;Execute Benchmark Now&quot; to run the 25-case synthetic evaluation suite.
              </p>
            </div>
          )}

          {/* Historical Runs Table */}
          {runs.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-semibold text-slate-900">Historical Benchmark Runs</h3>
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
                            Inspect
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
      )}
    </div>
  );
}
