import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  MapPin,
  RefreshCw,
  Search,
  Shield,
  User,
  Users,
  X,
  ChevronRight,
} from 'lucide-react';
import { teamsService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function TeamsPage() {
  const [teams, setTeams] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Roster modal state
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [roster, setRoster] = useState([]);
  const [loadingRoster, setLoadingRoster] = useState(false);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page_size: 50 };
      if (searchQuery.trim()) params.q = searchQuery.trim();
      const data = await teamsService.list(params);
      setTeams(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTeams();
  };

  const handleOpenRoster = async (team) => {
    setSelectedTeam(team);
    setLoadingRoster(true);
    try {
      const data = await teamsService.getRoster(team.team_id);
      setRoster(data.items || []);
    } catch (err) {
      setRoster([]);
    } finally {
      setLoadingRoster(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <Shield className="w-6 h-6 text-emerald-500" />
            <span>Cricket Teams & Franchises</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Registered franchises, team squads, coaching staff, and city representations
          </p>
        </div>

        <button
          onClick={fetchTeams}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearchSubmit} className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search team by name or city..."
          className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
        />
      </form>

      {/* Teams Grid */}
      {loading ? (
        <LoadingSkeleton rows={4} type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchTeams} />
      ) : teams.length === 0 ? (
        <EmptyState
          title="No teams found"
          description="Try adjusting your search criteria."
          icon={Shield}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {teams.map((team) => (
            <div
              key={team.team_id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-black text-base flex items-center justify-center">
                    {team.short_code || 'TM'}
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    {team.city}
                  </span>
                </div>

                <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                  {team.team_name}
                </h3>

                <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-1 text-xs text-slate-500">
                  <p className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    <span>Coach: <strong className="text-slate-700 dark:text-slate-300">{team.coach_name || 'N/A'}</strong></span>
                  </p>
                  <p className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>Home City: {team.city}</span>
                  </p>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/80">
                <button
                  onClick={() => handleOpenRoster(team)}
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-emerald-500 dark:hover:bg-emerald-500 hover:text-white dark:hover:text-white text-slate-700 dark:text-slate-300 font-semibold text-xs transition"
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>View 15-Player Roster</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Roster Modal */}
      {selectedTeam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-black flex items-center justify-center text-sm">
                  {selectedTeam.short_code}
                </div>
                <div>
                  <h3 className="font-extrabold text-base text-slate-900 dark:text-white">
                    {selectedTeam.team_name} Squad
                  </h3>
                  <p className="text-xs text-slate-500">Coach: {selectedTeam.coach_name}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedTeam(null)}
                className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex-1">
              {loadingRoster ? (
                <div className="space-y-2 py-4">
                  <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
                  <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
                  <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
                </div>
              ) : roster.length === 0 ? (
                <p className="text-center text-xs text-slate-500 py-8">No players registered in roster yet.</p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {roster.map((player) => (
                    <div
                      key={player.player_id}
                      className="py-3 flex items-center justify-between text-xs hover:bg-slate-50 dark:hover:bg-slate-800/40 px-2 rounded-xl"
                    >
                      <div>
                        <Link
                          to={`/players/${player.player_id}`}
                          onClick={() => setSelectedTeam(null)}
                          className="font-bold text-slate-900 dark:text-white hover:text-emerald-500 transition"
                        >
                          {player.name}
                        </Link>
                        <p className="text-[11px] text-slate-400">
                          {player.role || 'Player'} • {player.batting_style}
                        </p>
                      </div>
                      <Link
                        to={`/players/${player.player_id}`}
                        onClick={() => setSelectedTeam(null)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                      >
                        <span>Profile & Stats</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
