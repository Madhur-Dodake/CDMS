import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  PlayCircle,
  Plus,
  Shield,
  Table,
  Trophy,
  Users,
} from 'lucide-react';
import apiClient from '../../services/api';

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get('/api/dashboard/summary')
      .then((res) => {
        setSummary(res.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const statsCards = [
    {
      title: 'Active Tournaments',
      count: summary?.total_tournaments ?? 2,
      to: '/admin/tournaments',
      icon: Trophy,
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900',
    },
    {
      title: 'Registered Teams',
      count: summary?.total_teams ?? 4,
      to: '/admin/teams',
      icon: Shield,
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900',
    },
    {
      title: 'Player Roster',
      count: summary?.total_players ?? 60,
      to: '/admin/players',
      icon: Users,
      color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900',
    },
    {
      title: 'Scheduled Matches',
      count: summary?.scheduled_matches ?? 6,
      to: '/admin/matches',
      icon: Calendar,
      color: 'text-purple-500 bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-900',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Welcome Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white border border-slate-700/80 shadow-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] uppercase tracking-widest font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Operations Control
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold mt-2 text-white">
              CDMS Administration Dashboard
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-xl">
              Monitor tournaments, generate fixture schedules, and launch live match scoring sessions.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/admin/scoring"
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm flex items-center gap-1.5 transition"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Score Match</span>
            </Link>
            <Link
              to="/admin/matches"
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 flex items-center gap-1.5 transition"
            >
              <Calendar className="w-4 h-4" />
              <span>Fixtures</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statsCards.map((card) => (
          <Link
            key={card.title}
            to={card.to}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition duration-150 flex items-center justify-between group"
          >
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {card.title}
              </p>
              <p className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1 group-hover:text-emerald-500 transition">
                {loading ? '...' : card.count}
              </p>
            </div>
            <div className={`p-3 rounded-xl border ${card.color}`}>
              <card.icon className="w-5 h-5" />
            </div>
          </Link>
        ))}
      </div>

      {/* Recent Activity Log */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-500" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Recent System Activity
            </h3>
          </div>
          <span className="text-xs text-slate-400">Latest 5 events</span>
        </div>

        <div className="space-y-3">
          {(summary?.recent_activity || [
            { id: 1, action: 'Match Fixture Generated', detail: 'Round-robin schedule created with conflict checking', time: '10 mins ago' },
            { id: 2, action: 'Ball Event Scored', detail: 'Scorer recorded boundary four in live match session', time: '25 mins ago' },
            { id: 3, action: 'Points Table Updated', detail: 'Cumulative NRR recomputed from match outcomes', time: '1 hour ago' },
            { id: 4, action: 'Team Registered', detail: 'Eagles confirmed in T20 Scoring League', time: '2 hours ago' },
            { id: 5, action: 'Venue Inspected', detail: 'Wankhede Stadium slot verified for fixtures', time: '3 hours ago' },
          ]).map((act) => (
            <div
              key={act.id}
              className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-start justify-between gap-4"
            >
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-white">
                    {act.action}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {act.detail}
                  </p>
                </div>
              </div>
              <span className="text-[11px] text-slate-400 flex items-center gap-1 shrink-0">
                <Clock className="w-3 h-3" />
                <span>{act.time}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

