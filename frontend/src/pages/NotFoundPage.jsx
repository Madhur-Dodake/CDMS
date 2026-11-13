import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileQuestion } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-3xl bg-slate-200 dark:bg-slate-800 text-slate-500 flex items-center justify-center mx-auto mb-6">
          <FileQuestion className="w-8 h-8 text-emerald-500" />
        </div>

        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
          404 - Page Not Found
        </h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
          The requested page or cricket resource does not exist or has been relocated.
        </p>

        <div className="mt-8 flex justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Home</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

