import React from 'react';
import { BarChart3, TrendingUp, Award, Flame } from 'lucide-react';

export default function AdminStatsPage() {
  const topRunScorers = [
    { name: 'Virat Kohli', team: 'BLR', runs: 428, avg: '71.33', sr: '148.5' },
    { name: 'Rohit Sharma', team: 'MUM', runs: 382, avg: '54.57', sr: '152.1' },
    { name: 'KL Rahul', team: 'DEL', runs: 310, avg: '44.28', sr: '136.8' },
  ];

  const topWicketTakers = [
    { name: 'Jasprit Bumrah', team: 'MUM', wickets: 16, econ: '5.85', avg: '14.2' },
    { name: 'Mohammed Shami', team: 'KOL', wickets: 14, econ: '7.12', avg: '16.8' },
    { name: 'Kuldeep Yadav', team: 'DEL', wickets: 12, econ: '6.40', avg: '18.1' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-500" />
            <span>Tournament Statistics & Analytics</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Aggregated batting averages, strike rates, bowling economy, milestones and leaderboard
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Batters */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-500" />
              <span>Leading Run Scorers (Orange Cap)</span>
            </h3>
            <span className="text-xs font-semibold text-emerald-500">View All</span>
          </div>
          <div className="space-y-3">
            {topRunScorers.map((player, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60"
              >
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-white">{player.name}</p>
                  <p className="text-[10px] text-slate-500">Team: {player.team} • Avg: {player.avg} • SR: {player.sr}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-black text-slate-900 dark:text-white">{player.runs}</span>
                  <span className="text-[10px] text-slate-400 block">runs</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Bowlers */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Flame className="w-4 h-4 text-purple-500" />
              <span>Leading Wicket Takers (Purple Cap)</span>
            </h3>
            <span className="text-xs font-semibold text-emerald-500">View All</span>
          </div>
          <div className="space-y-3">
            {topWicketTakers.map((player, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60"
              >
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-white">{player.name}</p>
                  <p className="text-[10px] text-slate-500">Team: {player.team} • Econ: {player.econ} • Avg: {player.avg}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-black text-slate-900 dark:text-white">{player.wickets}</span>
                  <span className="text-[10px] text-slate-400 block">wkts</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

