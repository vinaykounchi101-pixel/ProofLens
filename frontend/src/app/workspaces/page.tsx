'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Workspace } from '@/lib/types/api';
import { FolderGit2, Plus, Sparkles, Shield, FileText, ArrowRight, X, Trash2 } from 'lucide-react';

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  async function loadWorkspaces() {
    try {
      setLoading(true);
      setError(null);
      const res = await api.listWorkspaces();
      setWorkspaces(res.workspaces);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to ProofLens API backend. Ensure FastAPI server is running on http://localhost:8000.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      setCreating(true);
      const ws = await api.createWorkspace(newTitle.trim(), newDesc.trim() || undefined);
      setWorkspaces((prev) => [ws, ...prev]);
      setIsModalOpen(false);
      setNewTitle('');
      setNewDesc('');
    } catch (err: any) {
      alert(`Error creating workspace: ${err.message}`);
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteWorkspace(workspaceId: string, name: string) {
    if (!window.confirm(`Are you sure you want to permanently delete workspace "${name}"?\nAll indexed documents, vectors, and query history will be removed.`)) {
      return;
    }
    try {
      await api.deleteWorkspace(workspaceId);
      setWorkspaces((prev) => prev.filter((w) => w.id !== workspaceId));
    } catch (err: any) {
      alert(`Failed to delete workspace: ${err.message}`);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-12 md:px-12 lg:px-24">
      {/* Header */}
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-md shadow-indigo-500/20">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">ProofLens AI</h1>
              <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                Evidence-First RAG
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">
              Isolate legal, financial, and technical documents into verified, provenance-tracked workspaces.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            New Workspace
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mt-8 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
            <p className="font-semibold text-rose-900">Backend Connection Notice</p>
            <p className="mt-1 text-xs text-rose-700">{error}</p>
          </div>
        )}

        {/* Content */}
        <div className="mt-10">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">Your Document Workspaces</h2>
            <span className="text-xs font-medium text-slate-500">{workspaces.length} workspace{workspaces.length === 1 ? '' : 's'}</span>
          </div>

          {loading ? (
            <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-44 animate-pulse rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" />
              ))}
            </div>
          ) : workspaces.length === 0 ? (
            <div className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
              <FolderGit2 className="h-12 w-12 text-slate-400" />
              <h3 className="mt-4 text-base font-medium text-slate-800">No workspaces yet</h3>
              <p className="mt-1 max-w-sm text-sm text-slate-500">
                Create a workspace to upload your PDF documents and start extracting verified evidence.
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="mt-6 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
              >
                <Plus className="h-4 w-4" />
                Create First Workspace
              </button>
            </div>
          ) : (
            <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {workspaces.map((ws) => (
                <Link
                  key={ws.id}
                  href={`/workspaces/${ws.id}/documents`}
                  className="group relative flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition-all hover:border-indigo-400 hover:shadow-md hover:shadow-indigo-500/5"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600 group-hover:bg-indigo-100 group-hover:text-indigo-700">
                        <FolderGit2 className="h-5 w-5" />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">
                          {new Date(ws.created_at).toLocaleDateString()}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleDeleteWorkspace(ws.id, ws.name);
                          }}
                          title="Delete workspace"
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-slate-900 group-hover:text-indigo-600">
                      {ws.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500">
                      {ws.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 text-xs font-medium text-indigo-600">
                    <span>Enter Workspace</span>
                    <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-lg font-semibold text-slate-900">Create New Workspace</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Workspace Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Financial Audit, Project Legal Docs"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-slate-300 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 transition focus:border-indigo-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/10"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Description (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Scope, regulatory framework, or notes..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-slate-300 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 transition focus:border-indigo-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/10"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newTitle.trim()}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
