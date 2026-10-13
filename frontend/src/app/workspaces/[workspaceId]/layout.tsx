'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Workspace } from '@/lib/types/api';
import {
  FileText,
  MessageSquareQuote,
  GitCompare,
  History,
  Activity,
  ArrowLeft,
  Shield,
  Layers,
} from 'lucide-react';

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const pathname = usePathname();
  const workspaceId = params.workspaceId as string;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (workspaceId) {
      api.getWorkspace(workspaceId)
        .then(setWorkspace)
        .catch((err) => console.error('Failed to load workspace:', err))
        .finally(() => setLoading(false));
    }
  }, [workspaceId]);

  const navItems = [
    {
      name: 'Documents',
      href: `/workspaces/${workspaceId}/documents`,
      icon: FileText,
      description: 'Upload, manage & inspect PDFs',
    },
    {
      name: 'Grounded Q&A',
      href: `/workspaces/${workspaceId}/qa`,
      icon: MessageSquareQuote,
      description: 'Ask questions with page citations',
    },
    {
      name: 'Compare',
      href: `/workspaces/${workspaceId}/compare`,
      icon: GitCompare,
      description: 'Cross-document discrepancy matrix',
    },
    {
      name: 'History',
      href: `/workspaces/${workspaceId}/history`,
      icon: History,
      description: 'Provenance audit log',
    },
    {
      name: 'Evaluation',
      href: `/workspaces/${workspaceId}/evaluation`,
      icon: Activity,
      description: 'RAG verification benchmarks',
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-4">
            <Link
              href="/workspaces"
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>All Workspaces</span>
            </Link>

            <div className="h-4 w-px bg-slate-200" />

            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Shield className="h-4 w-4" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-slate-900">
                  {loading ? 'Loading workspace...' : workspace?.name || 'Workspace'}
                </h1>
                <p className="text-[10px] font-mono text-slate-400">ID: {workspaceId.slice(0, 8)}...</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Evidence Engine Active
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <nav className="flex space-x-1 border-t border-slate-100 pt-1" aria-label="Tabs">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2 border-b-2 px-3.5 py-2.5 text-xs font-medium transition ${
                    isActive
                      ? 'border-indigo-600 text-indigo-600 font-semibold'
                      : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Body */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>
    </div>
  );
}
