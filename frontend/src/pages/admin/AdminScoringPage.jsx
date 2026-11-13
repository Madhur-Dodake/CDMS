import React, { useState } from 'react';
import { PlayCircle, RotateCcw, AlertTriangle, CheckCircle, Radio } from 'lucide-react';

export default function AdminScoringPage() {
  const [matchState, setMatchState] = useState({
    teamA: 'Mumbai Titans',
    teamB: 'Delhi Strikers',
    score: 142,
    wickets: 3,
    overs: '16.4',
    striker: 'Rohit Sharma (58* off 41)',
    nonStriker: 'Suryakumar Yadav (32* off 19)',
    bowler: 'Anrich Nortje (3.4-0-28-2)',
    recentBalls: ['1', '4', '0', 'W', '1', '2'],
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-emerald-500" />
            <span>Match Scorer Console</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time ball-by-ball recording with pure domain engine & deterministic undo
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-500 border border-rose-500/30">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>LIVE MATCH 101</span>
          </span>
        </div>
      </div>

      {/* Main Scorecard Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white shadow-card border border-slate-700/60">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
          <div>
            <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400">1st Innings</span>
            <h3 className="text-2xl font-black">{matchState.teamA}</h3>
          </div>
          <div className="text-right">
            <div className="text-3xl font-black tracking-tight text-white">
              {matchState.score}/{matchState.wickets}
              <span className="text-sm font-semibold text-slate-400 ml-2">({matchState.overs} Ov)</span>
            </div>
            <p className="text-xs text-emerald-400 font-medium">CRR: 8.52 • Projected: 171</p>
          </div>
        </div>

        {/* Striker / Non-Striker / Bowler info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">On Strike *</span>
            <p className="font-bold text-white mt-0.5">{matchState.striker}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Non-Striker</span>
            <p className="font-bold text-white mt-0.5">{matchState.nonStriker}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Bowler</span>
            <p className="font-bold text-white mt-0.5">{matchState.bowler}</p>
          </div>
        </div>

        {/* Recent Balls Strip */}
        <div className="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
          <span className="text-xs text-slate-400 font-medium">Recent Deliveries:</span>
          <div className="flex items-center gap-1.5">
            {matchState.recentBalls.map((b, idx) => (
              <span
                key={idx}
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                  b === 'W'
                    ? 'bg-rose-500 text-white'
                    : b === '4' || b === '6'
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-700 text-slate-200'
                }`}
              >
                {b}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Scorer Controls */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4">
        <h4 className="text-sm font-bold text-slate-900 dark:text-white">Record Delivery</h4>
        
        {/* Run Buttons */}
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
          {['0', '1', '2', '3', '4', '5', '6'].map((run) => (
            <button
              key={run}
              className="py-3 px-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 bg-slate-50 dark:bg-slate-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-sm font-extrabold text-slate-800 dark:text-slate-100 transition text-center"
            >
              {run} Runs
            </button>
          ))}
        </div>

        {/* Extras & Wicket */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
          <button className="py-2.5 px-3 rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 text-xs font-bold hover:bg-amber-100 transition">
            Wide (Wd)
          </button>
          <button className="py-2.5 px-3 rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 text-xs font-bold hover:bg-amber-100 transition">
            No Ball (Nb)
          </button>
          <button className="py-2.5 px-3 rounded-xl border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-sky-950/30 text-sky-700 dark:text-sky-400 text-xs font-bold hover:bg-sky-100 transition">
            Bye / Leg Bye
          </button>
          <button className="py-2.5 px-3 rounded-xl border border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 text-xs font-bold hover:bg-rose-100 transition">
            Wicket (Out)
          </button>
        </div>

        {/* Undo & State Management */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
          <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 text-xs font-bold hover:bg-rose-100 transition">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Undo Last Delivery</span>
          </button>
          <div className="flex items-center gap-2">
            <button className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-200 transition">
              End Innings
            </button>
            <button className="px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold transition">
              Complete Match
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

