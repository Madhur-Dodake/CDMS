import React from 'react';
import { Plus, Trophy } from 'lucide-react';

export default function AdminTournamentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-emerald-500" />
            <span>Tournaments Management</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Create, update, and manage tournaments, formats, and round-robin schedule generation
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition">
          <Plus className="w-4 h-4" />
          <span>New Tournament</span>
        </button>
      </div>

      <div className="p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card text-center">
        <Trophy className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
          Tournament Operations Module
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Supports round-robin schedule generation (n(n-1)/2), venue conflict checks, and team registrations.
        </p>
      </div>
    </div>
  );
}

