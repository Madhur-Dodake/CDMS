import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, MapPin, Radio, Share2 } from 'lucide-react';

export default function MatchScorecardPage() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/live"
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-rose-500/10 text-rose-500 border border-rose-500/30">
                <Radio className="w-3 h-3 animate-pulse" />
                <span>LIVE</span>
              </span>
              <span className="text-xs text-slate-500">Match #{id || '101'} • T20 Format</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
              Mumbai Titans vs Delhi Strikers
            </h1>
          </div>
        </div>
      </div>

      {/* Main Score Board */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white shadow-card border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
          <div>
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Currently Batting</span>
            <h2 className="text-2xl font-black mt-1">Mumbai Titans</h2>
            <p className="text-xs text-slate-400 mt-1">Toss won by Delhi Strikers, chose to bowl first</p>
          </div>
          <div className="text-right">
            <div className="text-3xl sm:text-4xl font-black text-white">
              164/4 <span className="text-sm font-semibold text-slate-400">(18.2 Ov)</span>
            </div>
            <p className="text-xs text-emerald-400 mt-1 font-medium">CRR: 8.95 • RPO Target: --</p>
          </div>
        </div>

        {/* Live Batsmen & Bowlers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-5 text-xs">
          <div className="space-y-2">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Batters</span>
            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 flex justify-between items-center">
              <div>
                <p className="font-bold text-white">Rohit Sharma *</p>
                <p className="text-[10px] text-slate-400">48 balls, 7 fours, 3 sixes</p>
              </div>
              <span className="font-extrabold text-emerald-400 text-sm">68*</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 flex justify-between items-center">
              <div>
                <p className="font-bold text-white">Hardik Pandya</p>
                <p className="text-[10px] text-slate-400">12 balls, 2 fours, 1 six</p>
              </div>
              <span className="font-extrabold text-slate-200 text-sm">22*</span>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Current Bowler</span>
            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 flex justify-between items-center">
              <div>
                <p className="font-bold text-white">Anrich Nortje</p>
                <p className="text-[10px] text-slate-400">3.2 overs, 1 maiden, 31 runs</p>
              </div>
              <div className="text-right">
                <span className="font-extrabold text-white text-sm">2 wkts</span>
                <p className="text-[10px] text-slate-400 font-mono">Econ: 9.3</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

