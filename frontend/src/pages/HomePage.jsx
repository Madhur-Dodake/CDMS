import React, { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';
import { Activity, Shield, Users, Radio } from 'lucide-react';

export default function HomePage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to connect to backend API');
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          Cricket Data Management System
        </h1>
        <p className="mt-4 text-lg text-slate-400">
          Lightweight, ad-free cricket tournament management, live scoring, and statistics engine.
        </p>
      </header>

      {/* Backend Status Card */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-12 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Activity className="w-6 h-6 text-emerald-400" />
            <h2 className="text-xl font-semibold text-white">Backend Health Status</h2>
          </div>
          {loading ? (
            <span className="px-3 py-1 text-xs rounded-full bg-slate-700 text-slate-300 animate-pulse">
              Checking...
            </span>
          ) : error ? (
            <span className="px-3 py-1 text-xs rounded-full bg-red-900/60 text-red-300 border border-red-700">
              Offline / Standalone
            </span>
          ) : (
            <span className="px-3 py-1 text-xs rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700">
              Operational
            </span>
          )}
        </div>

        {loading ? (
          <p className="text-slate-400 text-sm">Querying GET /health...</p>
        ) : error ? (
          <p className="text-slate-400 text-sm">
            Backend not reachable on <code className="text-emerald-400">http://localhost:8000</code>. Start FastAPI backend with <code className="text-slate-200">uvicorn app.main:app --reload</code>.
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block text-xs">Status</span>
              <span className="font-semibold text-emerald-400">{health.status}</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block text-xs">Environment</span>
              <span className="font-semibold text-slate-200">{health.environment}</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block text-xs">API Version</span>
              <span className="font-semibold text-slate-200">{health.version}</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block text-xs">Architecture</span>
              <span className="font-semibold text-indigo-400">FastAPI + Vite</span>
            </div>
          </div>
        )}
      </div>

      {/* Role Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-6">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-4">
            <Shield className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Administrator</h3>
          <p className="text-slate-400 text-sm">
            Configure tournaments, teams, venues, and fixtures. Assign authorized scorers to matches.
          </p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-6">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-4">
            <Radio className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Match Scorer</h3>
          <p className="text-slate-400 text-sm">
            Live ball-by-ball entry, extras, dismissals, strike rotation, and replay-based delivery undo.
          </p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-6">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Public Viewer</h3>
          <p className="text-slate-400 text-sm">
            Real-time scorecards, ball-by-ball commentary, points table with NRR, and player career stats.
          </p>
        </div>
      </div>
    </div>
  );
}

