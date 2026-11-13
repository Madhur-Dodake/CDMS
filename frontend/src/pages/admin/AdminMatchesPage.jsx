import React from 'react';
import { Calendar, Plus, Clock, MapPin, PlayCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AdminMatchesPage() {
  const matches = [
    {
      id: 1,
      team1: 'Mumbai Titans',
      team2: 'Delhi Strikers',
      venue: 'Wankhede Stadium',
      date: 'Today, 19:30 IST',
      status: 'SCHEDULED',
      scorer: 'Rajesh Sharma',
    },
    {
      id: 2,
      team1: 'Kolkata Knights',
      team2: 'Bangalore Blasters',
      venue: 'Eden Gardens',
      date: 'Live Now',
      status: 'LIVE',
      scorer: 'Anand Scorer',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-500" />
            <span>Match Operations & Fixtures</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Schedule fixtures, assign match scorers, and manage match state transitions
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition">
          <Plus className="w-4 h-4" />
          <span>Schedule Match</span>
        </button>
      </div>

      <div className="space-y-3">
        {matches.map((match) => (
          <div
            key={match.id}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4"
          >
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    match.status === 'LIVE'
                      ? 'bg-rose-500/10 text-rose-500 border border-rose-500/30 animate-pulse'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                  }`}
                >
                  {match.status}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {match.date}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {match.venue}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {match.team1} <span className="text-slate-400 font-normal">vs</span> {match.team2}
              </h3>
              <p className="text-xs text-slate-500">
                Assigned Scorer: <span className="font-semibold text-slate-700 dark:text-slate-300">{match.scorer}</span>
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <Link
                to={`/admin/scoring`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Launch Console</span>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

