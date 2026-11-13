import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Activity, Search, Shield, User, Users } from 'lucide-react';
import apiClient from '../services/api';

export default function PlayersPage() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const teamId = searchParams.get('team_id');
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    const query = teamId ? `?team_id=${teamId}&page_size=50` : '?page_size=50';
    apiClient
      .get(`/api/players${query}`)
      .then((res) => {
        setPlayers(res.data.items || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [teamId]);

  const filteredPlayers = players.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.role && p.role.toLowerCase().includes(search.toLowerCase())) ||
    (p.team_name && p.team_name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-6 h-6 text-emerald-500" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Players Directory
            </h1>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Player profiles, batting/bowling classifications, and career statistical figures
          </p>
        </div>

        {/* Search */}
        <div className="relative max-w-xs w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search player or role..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : filteredPlayers.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 shadow-card">
          <User className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Players Found</h3>
          <p className="text-xs text-slate-500 mt-1">Try clearing filters or search terms.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlayers.map((player) => (
            <div
              key={player.player_id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      {player.name}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-1">
                      <Shield className="w-3 h-3 text-emerald-500" />
                      <span>{player.team_name || 'Independent Player'}</span>
                    </p>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    {player.role || 'Player'}
                  </span>
                </div>

                <div className="mt-3 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                  {player.batting_style && <div>Batting: <span className="text-slate-700 dark:text-slate-200 font-medium">{player.batting_style}</span></div>}
                  {player.bowling_style && <div>Bowling: <span className="text-slate-700 dark:text-slate-200 font-medium">{player.bowling_style}</span></div>}
                </div>
              </div>

              {/* Career Stats Preview */}
              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-4 gap-2 text-center text-xs">
                <div>
                  <p className="text-slate-400 text-[10px] uppercase font-bold">Runs</p>
                  <p className="font-extrabold text-slate-800 dark:text-slate-100 mt-0.5">
                    {player.stats?.runs ?? 0}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400 text-[10px] uppercase font-bold">SR</p>
                  <p className="font-extrabold text-slate-800 dark:text-slate-100 mt-0.5">
                    {player.stats?.strike_rate ?? '0.0'}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400 text-[10px] uppercase font-bold">Wkts</p>
                  <p className="font-extrabold text-slate-800 dark:text-slate-100 mt-0.5">
                    {player.stats?.wickets ?? 0}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400 text-[10px] uppercase font-bold">Econ</p>
                  <p className="font-extrabold text-slate-800 dark:text-slate-100 mt-0.5">
                    {player.stats?.economy ?? '0.0'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

