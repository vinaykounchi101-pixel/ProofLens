'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/workspaces');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-slate-50 text-slate-600">
      <div className="flex items-center gap-3">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
        <p className="text-sm font-medium">Entering ProofLens AI...</p>
      </div>
    </div>
  );
}
