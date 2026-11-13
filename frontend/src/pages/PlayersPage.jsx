import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Award,
  BarChart3,
  Flame,
  RefreshCw,
  Search,
  User,
  Users,
} from 'lucide-react';
import { playersService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function PlayersPage() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page_size: 60 };
      if (searchQuery.trim()) params.q = searchQuery.trim();
      if (roleFilter) params.role = roleFilter;

      const data = await playersService.list(params);
      setPlayers(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load players');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlayers();
  }, [roleFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchPlayers();
  };

  const roles = [
    { id: '', label: 'All Squad' },
    { id: 'Batter', label: 'Batters' },
    { id: 'Bowler', label: 'Bowlers' },
    { id: 'All-rounder', label: 'All-Rounders' },
    { id: 'Wicketkeeper', label: 'Wicketkeepers' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <Users className="w-6 h-6 text-emerald-500" />
            <span>Athletes & Player Registry</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Search players, filter by specialty role, view career batting averages, bowling economies, and match logs
          </p>
        </div>

        <button
          onClick={fetchPlayers}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search and Role Filter Tabs */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search athlete by name (e.g. Virat, Rohit)..."
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
          />
        </form>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {roles.map((r) => (
            <button
              key={r.id}
              onClick={() => setRoleFilter(r.id)}
              className={`px-3 py-2 text-xs font-bold rounded-xl border whitespace-nowrap transition ${
                roleFilter === r.id
                  ? 'bg-emerald-500 text-white border-emerald-500 shadow-sm'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:bg-slate-50'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Players Grid */}
      {loading ? (
        <LoadingSkeleton rows={6} type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchPlayers} />
      ) : players.length === 0 ? (
        <EmptyState
          title="No athletes found"
          description="Try broadening your search term or selecting another role filter."
          icon={Users}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {players.map((p) => {
            const stats = p.stats || {};
            return (
              <div
                key={p.player_id}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {p.role || 'Athlete'}
                    </span>
                    <span className="text-[11px] font-bold text-slate-400">
                      {p.team_name || 'Free Agent'}
                    </span>
                  </div>

                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                    {p.name}
                  </h3>

                  <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-1 text-[11px] text-slate-500">
                    <p>
                      Batting: <strong className="text-slate-700 dark:text-slate-300">{p.batting_style || 'Right-hand'}</strong>
                    </p>
                    {p.bowling_style && p.bowling_style !== 'None' && (
                      <p>
                        Bowling: <strong className="text-slate-700 dark:text-slate-300">{p.bowling_style}</strong>
                      </p>
                    )}
                  </div>

                  {/* Career figures preview */}
                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                      <span className="text-[9px] uppercase font-bold text-slate-400 block">Matches</span>
                      <strong className="text-slate-800 dark:text-slate-200">{stats.matches_played ?? 0}</strong>
                    </div>
                    <div className="p-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                      <span className="text-[9px] uppercase font-bold text-slate-400 block">Runs</span>
                      <strong className="text-emerald-600 dark:text-emerald-400">{stats.runs ?? 0}</strong>
                    </div>
                    <div className="p-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                      <span className="text-[9px] uppercase font-bold text-slate-400 block">Wkts</span>
                      <strong className="text-slate-800 dark:text-slate-200">{stats.wickets ?? 0}</strong>
                    </div>
                  </div>
                </div>

                <div className="mt-5">
                  <Link
                    to={`/players/${p.player_id}`}
                    className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-emerald-500 dark:hover:bg-emerald-500 hover:text-white dark:hover:text-white text-slate-700 dark:text-slate-300 font-semibold text-xs transition"
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span>View Profile & Chart</span>
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
