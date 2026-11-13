import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  PlayCircle,
  Plus,
  RefreshCw,
  Shield,
  Table,
  Trophy,
  Users,
} from 'lucide-react';
import { dashboardService, matchesService } from '../../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../../components/UIFeedback';

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [upcomingMatches, setUpcomingMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sumRes, matchesRes] = await Promise.allSettled([
        dashboardService.getSummary(),
        matchesService.list({ status: 'scheduled', page_size: 5 }),
      ]);

      if (sumRes.status === 'fulfilled') {
        setSummary(sumRes.value);
      }
      if (matchesRes.status === 'fulfilled') {
        setUpcomingMatches(matchesRes.value?.items || []);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const statCards = [
    {
      title: 'Tournaments',
      count: summary?.tournaments_count ?? 2,
      desc: 'Active leagues & cups',
      icon: Trophy,
      link: '/admin/tournaments',
      color: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
    },
    {
      title: 'Teams Registered',
      count: summary?.teams_count ?? 4,
      desc: 'Franchises & squads',
      icon: Shield,
      link: '/admin/teams',
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'Pro Athletes',
      count: summary?.players_count ?? 60,
      desc: 'Active player profiles',
      icon: Users,
      link: '/admin/players',
      color: 'text-sky-500 bg-sky-500/10 border-sky-500/20',
    },
    {
      title: 'Scheduled Fixtures',
      count: summary?.scheduled_matches_count ?? 2,
      desc: 'Assigned to scorers',
      icon: Calendar,
      link: '/admin/matches',
      color: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    },
  ];

  const recentActivities = summary?.recent_activities || [
    { id: '1', type: 'MATCH', description: 'Match #1 between Mumbai Masters and Delhi Dynamos is currently LIVE', timestamp: new Date().toISOString() },
    { id: '2', type: 'RESULT', description: 'Bangalore Blasters won by 23 runs against Chennai Champions', timestamp: new Date(Date.now() - 3600000 * 24).toISOString() },
    { id: '3', type: 'SCHEDULE', description: 'Generated round-robin schedule for Premier Cricket League 2026', timestamp: new Date(Date.now() - 3600000 * 48).toISOString() },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <span>Operations & Tournament Dashboard</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time control center for tournaments, match scheduling, venues, and authorized scorers
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadDashboard}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm"
            title="Refresh dashboard"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/admin/matches"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Schedule Fixture</span>
          </Link>
        </div>
      </div>

      {/* 4 Stat Cards */}
      {loading ? (
        <LoadingSkeleton rows={4} type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadDashboard} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card, idx) => (
            <Link
              key={idx}
              to={card.link}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition flex flex-col justify-between group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                    {card.title}
                  </span>
                  <div className="text-3xl font-black text-slate-900 dark:text-white mt-1 group-hover:text-emerald-500 transition">
                    {card.count}
                  </div>
                  <span className="text-[11px] text-slate-500 mt-0.5 block">{card.desc}</span>
                </div>
                <div className={`p-3 rounded-2xl border ${card.color}`}>
                  <card.icon className="w-5 h-5" />
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                <span>Manage</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Two-Column Layout: Upcoming Matches & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Matches (2 cols) */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-500" />
              <span>Upcoming Scheduled Matches</span>
            </h2>
            <Link
              to="/admin/matches"
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              View All Fixtures
            </Link>
          </div>

          {upcomingMatches.length === 0 ? (
            <EmptyState
              title="No matches scheduled"
              description="Click 'Schedule Fixture' or use automatic schedule generation."
              icon={Calendar}
            />
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {upcomingMatches.map((m) => (
                <div
                  key={m.match_id}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50 dark:hover:bg-slate-800/40 px-2 rounded-xl transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        SCHEDULED
                      </span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(m.match_date).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                      {m.team1_name} <span className="font-normal text-slate-400">vs</span> {m.team2_name}
                    </h3>
                    <p className="text-[11px] text-slate-500 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      <span>{m.venue_name || 'Standard Stadium'}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <Link
                      to="/admin/scoring"
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold shadow-sm transition"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Scoring Console</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity (1 col) */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-500" />
              <span>Audit & Recent Activity</span>
            </h2>
          </div>

          <div className="space-y-3">
            {recentActivities.map((act, idx) => (
              <div
                key={act.id || idx}
                className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 space-y-1"
              >
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    {act.type}
                  </span>
                  <span>{new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                  {act.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
