import React from 'react';
import { Table, Trophy, ArrowUpRight } from 'lucide-react';

export default function AdminPointsTablePage() {
  const standings = [
    { rank: 1, team: 'Mumbai Titans', played: 6, won: 5, lost: 1, tied: 0, nr: 0, pts: 10, nrr: '+1.520' },
    { rank: 2, team: 'Bangalore Blasters', played: 6, won: 4, lost: 2, tied: 0, nr: 0, pts: 8, nrr: '+0.850' },
    { rank: 3, team: 'Kolkata Knights', played: 6, won: 3, lost: 3, tied: 0, nr: 0, pts: 6, nrr: '-0.120' },
    { rank: 4, team: 'Delhi Strikers', played: 6, won: 2, lost: 4, tied: 0, nr: 0, pts: 4, nrr: '-0.450' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Table className="w-5 h-5 text-emerald-500" />
            <span>Tournament Points Table & Standings</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time NRR calculation and automated standings sorted by points, wins, and NRR
          </p>
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-3">#</th>
                <th className="py-3 px-3">Team</th>
                <th className="py-3 px-3 text-center">P</th>
                <th className="py-3 px-3 text-center">W</th>
                <th className="py-3 px-3 text-center">L</th>
                <th className="py-3 px-3 text-center">T/NR</th>
                <th className="py-3 px-3 text-center font-bold text-emerald-500">Pts</th>
                <th className="py-3 px-3 text-right">NRR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {standings.map((row) => (
                <tr key={row.rank} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                  <td className="py-3 px-3 font-bold text-slate-500">{row.rank}</td>
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span>{row.team}</span>
                  </td>
                  <td className="py-3 px-3 text-center text-slate-600 dark:text-slate-300">{row.played}</td>
                  <td className="py-3 px-3 text-center text-slate-600 dark:text-slate-300">{row.won}</td>
                  <td className="py-3 px-3 text-center text-slate-600 dark:text-slate-300">{row.lost}</td>
                  <td className="py-3 px-3 text-center text-slate-600 dark:text-slate-300">{row.tied + row.nr}</td>
                  <td className="py-3 px-3 text-center font-black text-emerald-600 dark:text-emerald-400 text-sm">
                    {row.pts}
                  </td>
                  <td className={`py-3 px-3 text-right font-mono font-semibold ${
                    row.nrr.startsWith('+') ? 'text-emerald-500' : 'text-slate-400'
                  }`}>
                    {row.nrr}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

