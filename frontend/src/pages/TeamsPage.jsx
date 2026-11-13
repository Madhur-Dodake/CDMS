import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Search, Shield, User, Users } from 'lucide-react';
import apiClient from '../services/api';

export default function TeamsPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    apiClient
      .get('/api/teams?page_size=50')
      .then((res) => {
        setTeams(res.data.items || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const filteredTeams = teams.filter((t) =>
    t.team_name.toLowerCase().includes(search.toLowerCase()) ||
    (t.city && t.city.toLowerCase().includes(search.toLowerCase())) ||
    (t.short_code && t.short_code.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-emerald-500" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Cricket Teams
            </h1>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Registered tournament franchises, squads, and head coaches
          </p>
        </div>

        {/* Filter Input */}
        <div className="relative max-w-xs w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search teams or cities..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-40 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : filteredTeams.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 shadow-card">
          <Shield className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Teams Found</h3>
          <p className="text-xs text-slate-500 mt-1">Try adjusting your search query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {filteredTeams.map((team) => (
            <div
              key={team.team_id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-extrabold flex items-center justify-center border border-emerald-500/20">
                    {team.short_code || team.team_name.substring(0, 2).toUpperCase()}
                  </div>
                  {team.city && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                      <MapPin className="w-3 h-3" />
                      <span>{team.city}</span>
                    </span>
                  )}
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {team.team_name}
                </h3>
                {team.coach_name && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1">
                    <User className="w-3 h-3 text-slate-400" />
                    <span>Coach: {team.coach_name}</span>
                  </p>
                )}
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  <span>15 Players</span>
                </span>
                <Link
                  to={`/players?team_id=${team.team_id}`}
                  className="font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                >
                  Roster &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

