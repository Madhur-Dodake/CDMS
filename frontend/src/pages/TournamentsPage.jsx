import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Layers,
  Search,
  Trophy,
  ArrowRight,
  RefreshCw,
  Table,
} from 'lucide-react';
import { tournamentsService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function TournamentsPage() {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState('');

  const fetchTournaments = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (searchQuery.trim()) params.q = searchQuery.trim();
      if (levelFilter) params.level = levelFilter;

      const data = await tournamentsService.list(params);
      setTournaments(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournaments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTournaments();
  }, [levelFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTournaments();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <Trophy className="w-6 h-6 text-emerald-500" />
            <span>Tournaments & Leagues</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse cricket championships, points standings, round-robin fixtures, and Net Run Rates
          </p>
        </div>

        <button
          onClick={fetchTournaments}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search & Level Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tournament by name..."
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
          />
        </form>

        <div className="flex items-center gap-2">
          {['', 'domestic', 'club', 'international'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-3 py-2 text-xs font-bold rounded-xl border capitalize transition ${
                levelFilter === lvl
                  ? 'bg-emerald-500 text-white border-emerald-500 shadow-sm'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:bg-slate-50'
              }`}
            >
              {lvl === '' ? 'All Levels' : lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Tournaments Grid */}
      {loading ? (
        <LoadingSkeleton rows={3} type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchTournaments} />
      ) : tournaments.length === 0 ? (
        <EmptyState
          title="No tournaments found"
          description="Try adjusting your search criteria or filter to find tournaments."
          icon={Trophy}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tournaments.map((tourney) => (
            <div
              key={tourney.tournament_id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
                    <Trophy className="w-5 h-5" />
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {tourney.format || 'T20'} • {tourney.level}
                  </span>
                </div>

                <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                  {tourney.name}
                </h3>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-1.5 text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {new Date(tourney.start_date).toLocaleDateString([], { month: 'short', day: 'numeric' })} -{' '}
                      {new Date(tourney.end_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    <span>Teams Registered: {tourney.teams_count ?? 4}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/80 flex items-center gap-2">
                <Link
                  to={`/tournaments/${tourney.tournament_id}`}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-sm transition"
                >
                  <Table className="w-3.5 h-3.5" />
                  <span>Points Table & Fixtures</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
