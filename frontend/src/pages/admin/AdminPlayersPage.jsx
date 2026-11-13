import React from 'react';
import { Plus, Users } from 'lucide-react';

export default function AdminPlayersPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-500" />
            <span>Player Management</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Register player profiles, date of birth validations, and batting/bowling classifications
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition">
          <Plus className="w-4 h-4" />
          <span>Add Player</span>
        </button>
      </div>

      <div className="p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card text-center">
        <Users className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
          Player Registry Module
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Career statistics tracking, 50s/100s milestones, and non-future date of birth validation rules.
        </p>
      </div>
    </div>
  );
}

