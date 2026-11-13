import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Calendar, Filter, Plus, Search, Table, Trophy } from 'lucide-react';
import apiClient from '../services/api';

export default function TournamentsPage() {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') || '';
  const [searchTerm, setSearchTerm] = useState(q);

  useEffect(() => {
    setLoading(true);
    const query = q ? `?q=${encodeURIComponent(q)}` : '';
    apiClient
      .get(`/api/tournaments${query}`)
      .then((res) => {
        setTournaments(res.data.items || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [q]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchParams(searchTerm ? { q: searchTerm } : {});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <Trophy className="w-6 h-6 text-emerald-500" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Tournaments
            </h1>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Official cricket leagues, fixtures, formats, and cumulative standings
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex items-center gap-2 max-w-sm w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search tournaments..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-500 text-white hover:bg-emerald-600 transition"
          >
            Filter
          </button>
        </form>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-44 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse"
            />
          ))}
        </div>
      ) : tournaments.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 shadow-card">
          <Trophy className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            No Tournaments Found
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {q ? `No results matched "${q}". Try clearing filters.` : 'No tournaments registered yet.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tournaments.map((t) => (
            <div
              key={t.tournament_id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    {t.format || 'T20'}
                  </span>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">
                    {t.level || 'Local'}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {t.name}
                </h3>
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    {t.start_date} &rarr; {t.end_date}
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  {t.team_count ?? 4} Teams registered
                </span>
                <Link
                  to={`/tournaments/${t.tournament_id}/standings`}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                >
                  <Table className="w-3.5 h-3.5" />
                  <span>Points Table</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

