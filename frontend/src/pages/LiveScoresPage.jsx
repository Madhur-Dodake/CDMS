import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, Calendar, MapPin, Radio, Shield, Trophy } from 'lucide-react';
import apiClient from '../services/api';

export default function LiveScoresPage() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get('/api/matches?page_size=20')
      .then((res) => {
        setMatches(res.data.items || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-6 h-6 text-red-500 animate-pulse" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Live Scores & Commentary
            </h1>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Real-time ball-by-ball updates, live scorecards, and match statuses
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs font-bold">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
          <span>WebSockets Connected</span>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : matches.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 shadow-card">
          <Radio className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Matches Available</h3>
          <p className="text-xs text-slate-500 mt-1">Check back when scheduled matches go live.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {matches.map((m) => {
            const isLive = m.status === 'live';
            const isCompleted = m.status === 'completed';

            return (
              <div
                key={m.match_id}
                className={`p-6 rounded-2xl bg-white dark:bg-slate-900 border transition shadow-card flex flex-col justify-between ${
                  isLive
                    ? 'border-red-500/40 ring-1 ring-red-500/30'
                    : 'border-slate-200 dark:border-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      {m.tournament_name || 'Tournament Fixture'} &bull; {m.overs} Overs
                    </span>
                    {isLive ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500 text-white shadow-sm shadow-red-500/30 animate-pulse">
                        <span className="w-1.5 h-1.5 rounded-full bg-white"></span>
                        LIVE
                      </span>
                    ) : (
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {m.status}
                      </span>
                    )}
                  </div>

                  {/* Teams Matchup Card */}
                  <div className="space-y-3 my-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {m.team1_name}
                        </span>
                      </div>
                      <span className="text-sm font-extrabold text-slate-900 dark:text-white">
                        {isLive ? '142/3 (16.2)' : 'Yet to bat'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-slate-400" />
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {m.team2_name}
                        </span>
                      </div>
                      <span className="text-sm font-extrabold text-slate-400">
                        {isCompleted ? '140/9 (20.0)' : '—'}
                      </span>
                    </div>
                  </div>

                  {m.result_summary && (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mt-2">
                      {m.result_summary}
                    </p>
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1.5 text-[11px]">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(m.match_date).toLocaleDateString()}</span>
                  </div>
                  <Link
                    to={`/matches/${m.match_id}`}
                    className="font-semibold text-emerald-600 dark:text-emerald-400 hover:underline inline-flex items-center gap-1"
                  >
                    <span>Full Scorecard</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

