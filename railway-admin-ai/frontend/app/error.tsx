'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Caught in global error boundary:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-railway-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl border border-slate-100 text-center animate-fade-in">
        <div>
          <h2 className="mt-2 text-3xl font-extrabold text-slate-900 tracking-tight">Oops! Something went wrong.</h2>
          <p className="mt-4 text-sm text-slate-600 leading-relaxed">
            We encountered an unexpected issue while processing your request. Please try again or contact support if the problem persists.
          </p>
        </div>
        <div className="mt-8 flex flex-col space-y-4">
          <button
            onClick={() => reset()}
            className="btn-primary w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-railway-600 hover:bg-railway-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-railway-500"
          >
            Try again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="btn-secondary w-full flex justify-center py-3 px-4 rounded-lg shadow-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2"
          >
            Return Home
          </button>
        </div>
      </div>
    </div>
  );
}
