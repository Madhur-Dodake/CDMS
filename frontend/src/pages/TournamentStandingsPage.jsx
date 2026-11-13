import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Layers,
  MapPin,
  Radio,
  RefreshCw,
  Shield,
  Table,
  Trophy,
  ArrowRight,
} from 'lucide-react';
import { tournamentsService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function TournamentStandingsPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('standings'); // 'standings' | 'fixtures' | 'teams'
  const [tournament, setTournament] = useState(null);
  const [pointsTable, setPointsTable] = useState([]);
  const [fixtures, setFixtures] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTournamentData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);

      const [tourneyRes, ptRes, fixturesRes, teamsRes] = await Promise.allSettled([
        tournamentsService.getById(id),
        tournamentsService.getPointsTable(id),
        tournamentsService.getFixtures(id),
        tournamentsService.getTeams(id),
      ]);

      if (tourneyRes.status === 'fulfilled') {
        setTournament(tourneyRes.value);
      } else {
        throw new Error('Tournament not found');
      }

      if (ptRes.status === 'fulfilled') {
        setPointsTable(ptRes.value || []);
      }
      if (fixturesRes.status === 'fulfilled') {
        setFixtures(fixturesRes.value?.items || []);
      }
      if (teamsRes.status === 'fulfilled') {
        setTeams(teamsRes.value || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to load tournament data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTournamentData();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="h-8 w-48 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse" />
        <LoadingSkeleton rows={1} type="card" />
        <LoadingSkeleton rows={4} type="table" />
      </div>
    );
  }

  if (error || !tournament) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          to="/tournaments"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-emerald-500 mb-4 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Tournaments</span>
        </Link>
        <ErrorState message={error || 'Tournament not found'} onRetry={loadTournamentData} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/tournaments"
            className="p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                {tournament.format || 'T20'} • {tournament.level}
              </span>
              <span className="text-xs text-slate-500">
                {new Date(tournament.start_date).toLocaleDateString([], { month: 'short', day: 'numeric' })} -{' '}
                {new Date(tournament.end_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white mt-1">
              {tournament.name}
            </h1>
          </div>
        </div>

        <button
          onClick={loadTournamentData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-4">
        <button
          onClick={() => setActiveTab('standings')}
          className={`pb-3 px-2 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'standings'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Table className="w-4 h-4" />
          <span>Points Table & NRR</span>
        </button>
        <button
          onClick={() => setActiveTab('fixtures')}
          className={`pb-3 px-2 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'fixtures'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>Fixtures & Results</span>
        </button>
        <button
          onClick={() => setActiveTab('teams')}
          className={`pb-3 px-2 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'teams'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Registered Teams</span>
        </button>
      </div>

      {/* Tab 1: Points Table */}
      {activeTab === 'standings' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Official Points Table & Standings
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Sorted by Points, Net Run Rate (NRR), and Wins per tournament rules
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Win: 2 pts • Tie/NR: 1 pt • Loss: 0 pt
            </span>
          </div>

          {pointsTable.length === 0 ? (
            <EmptyState
              title="Points table not generated yet"
              description="No matches have been completed for this tournament yet."
              icon={Table}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                    <th className="py-3 px-3">Pos</th>
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
                  {pointsTable.map((row, idx) => {
                    const nrrVal = typeof row.nrr === 'number' ? row.nrr : parseFloat(row.nrr || '0');
                    const nrrStr = (nrrVal >= 0 ? '+' : '') + nrrVal.toFixed(3);
                    return (
                      <tr key={row.team_id || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="py-3.5 px-3 font-bold text-slate-400">{idx + 1}</td>
                        <td className="py-3.5 px-3 font-bold text-slate-900 dark:text-white flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              idx === 0
                                ? 'bg-amber-400 ring-2 ring-amber-400/30'
                                : idx < 3
                                ? 'bg-emerald-500'
                                : 'bg-slate-400'
                            }`}
                          />
                          <span>{row.team_name}</span>
                        </td>
                        <td className="py-3.5 px-3 text-center text-slate-600 dark:text-slate-300">
                          {row.played}
                        </td>
                        <td className="py-3.5 px-3 text-center font-semibold text-emerald-600 dark:text-emerald-400">
                          {row.won}
                        </td>
                        <td className="py-3.5 px-3 text-center text-rose-500">{row.lost}</td>
                        <td className="py-3.5 px-3 text-center text-slate-500">
                          {(row.tied || 0) + (row.nr || 0)}
                        </td>
                        <td className="py-3.5 px-3 text-center font-black text-slate-900 dark:text-white text-sm">
                          {row.points}
                        </td>
                        <td
                          className={`py-3.5 px-3 text-right font-mono font-bold ${
                            nrrVal > 0
                              ? 'text-emerald-500'
                              : nrrVal < 0
                              ? 'text-rose-500'
                              : 'text-slate-400'
                          }`}
                        >
                          {nrrStr}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Fixtures & Results */}
      {activeTab === 'fixtures' && (
        <div className="space-y-4">
          {fixtures.length === 0 ? (
            <EmptyState
              title="No fixtures scheduled yet"
              description="Tournament schedule has not been generated."
              icon={Calendar}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {fixtures.map((m) => (
                <div
                  key={m.match_id}
                  className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs mb-3">
                      <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(m.match_date).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      {m.status === 'live' ? (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-500 text-[10px] font-bold border border-rose-500/20">
                          <Radio className="w-3 h-3 animate-pulse" />
                          LIVE
                        </span>
                      ) : m.status === 'completed' ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold">
                          COMPLETED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-bold">
                          SCHEDULED
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">
                      {m.team1_name} <span className="font-normal text-slate-400">vs</span>{' '}
                      {m.team2_name}
                    </h4>

                    {m.result_summary && (
                      <p className="mt-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 p-2 rounded-xl">
                        {m.result_summary}
                      </p>
                    )}

                    <div className="mt-3 flex items-center gap-1 text-xs text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{m.venue_name || 'Stadium'}</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                    <Link
                      to={`/matches/${m.match_id}`}
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                    >
                      <span>{m.status === 'live' ? 'Open Live Scorecard' : 'View Match Details'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Registered Teams */}
      {activeTab === 'teams' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {teams.length === 0 ? (
            <EmptyState title="No registered teams" icon={Shield} />
          ) : (
            teams.map((t) => (
              <div
                key={t.team_id}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card text-center space-y-2"
              >
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto font-black text-sm">
                  {t.short_code || 'TM'}
                </div>
                <h4 className="font-bold text-slate-900 dark:text-white text-sm">{t.team_name}</h4>
                <p className="text-xs text-slate-500">{t.city}</p>
                <p className="text-[11px] text-slate-400">Coach: {t.coach_name || 'N/A'}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
