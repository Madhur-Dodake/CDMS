import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Plus,
  PlayCircle,
  Clock,
  MapPin,
  UserCheck,
  Search,
  Sparkles,
  X,
  AlertCircle,
  Shield,
  Layers,
  ChevronRight,
} from 'lucide-react';
import {
  matchesService,
  tournamentsService,
  teamsService,
  venuesService,
  usersService,
} from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

const matchSchema = z
  .object({
    tournament_id: z.string().min(1, 'Please select a tournament'),
    team1_id: z.string().min(1, 'Please select Team 1'),
    team2_id: z.string().min(1, 'Please select Team 2'),
    venue_id: z.string().min(1, 'Please select a venue'),
    match_date: z.string().min(1, 'Match date & time is required'),
    overs: z
      .preprocess(
        (val) => (val === '' || val === null || val === undefined ? 20 : Number(val)),
        z.number({ invalid_type_error: 'Overs must be a number' }).min(1, 'Minimum 1 over').max(100, 'Maximum 100 overs')
      ),
    scorer_id: z.string().optional().or(z.literal('')),
  })
  .refine((data) => data.team1_id !== data.team2_id, {
    message: 'Team 1 and Team 2 must be different teams',
    path: ['team2_id'],
  });

export default function AdminMatchesPage() {
  const [matches, setMatches] = useState([]);
  const [tournaments, setTournaments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [venues, setVenues] = useState([]);
  const [scorers, setScorers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  // Modals state
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [selectedGenerateTournament, setSelectedGenerateTournament] = useState('');
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(matchSchema),
    defaultValues: {
      tournament_id: '',
      team1_id: '',
      team2_id: '',
      venue_id: '',
      match_date: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
      overs: 20,
      scorer_id: '',
    },
  });

  const fetchDependencies = async () => {
    try {
      setLoading(true);
      const [matchesRes, tournamentsRes, teamsRes, venuesRes, usersRes] = await Promise.all([
        matchesService.list({ page_size: 100 }),
        tournamentsService.list({ page_size: 50 }),
        teamsService.list({ page_size: 50 }),
        venuesService.list({ page_size: 50 }),
        usersService.list({ page_size: 100 }),
      ]);
      setMatches(matchesRes.items || []);
      setTournaments(tournamentsRes.items || []);
      setTeams(teamsRes.items || []);
      setVenues(venuesRes.items || []);

      // Filter users who are scorers or admins
      const scorerList = (usersRes.items || []).filter(
        (u) => u.role === 'scorer' || u.role === 'admin'
      );
      setScorers(scorerList);
    } catch (err) {
      toast.error('Failed to load scheduler data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDependencies();
  }, []);

  const openScheduleModal = () => {
    setServerError('');
    reset({
      tournament_id: tournaments[0]?.tournament_id || '',
      team1_id: teams[0]?.team_id || '',
      team2_id: teams[1]?.team_id || '',
      venue_id: venues[0]?.venue_id || '',
      match_date: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
      overs: 20,
      scorer_id: scorers[0]?.user_id || '',
    });
    setIsScheduleModalOpen(true);
  };

  const closeScheduleModal = () => {
    setIsScheduleModalOpen(false);
    setServerError('');
  };

  const onScheduleSubmit = async (data) => {
    setServerError('');
    setIsSubmitting(true);
    try {
      const payload = {
        tournament_id: data.tournament_id,
        team1_id: data.team1_id,
        team2_id: data.team2_id,
        venue_id: data.venue_id,
        match_date: new Date(data.match_date).toISOString(),
        overs: Number(data.overs),
        scorer_id: data.scorer_id ? data.scorer_id : null,
      };

      await matchesService.schedule(payload);
      toast.success('Match scheduled successfully!');
      closeScheduleModal();
      fetchDependencies();
    } catch (err) {
      // Catch server validation error (e.g. venue double booking, date conflict)
      const msg = err.response?.data?.detail || 'Failed to schedule match';
      setServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGenerateRoundRobin = async () => {
    if (!selectedGenerateTournament) {
      toast.error('Please select a tournament');
      return;
    }
    setIsGenerating(true);
    try {
      const res = await tournamentsService.generateSchedule(selectedGenerateTournament);
      toast.success(`Schedule generated! ${res.matches_generated} round-robin fixtures created.`);
      setIsGenerateModalOpen(false);
      fetchDependencies();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate tournament schedule';
      toast.error(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const filteredMatches = matches.filter((m) => {
    const matchesStatus =
      statusFilter === 'ALL'
        ? true
        : statusFilter === 'LIVE'
        ? m.status === 'IN_PROGRESS' || m.status === 'LIVE'
        : m.status === statusFilter;

    const t1 = m.team1_name || '';
    const t2 = m.team2_name || '';
    const v = m.venue_name || '';
    const matchesSearch =
      t1.toLowerCase().includes(search.toLowerCase()) ||
      t2.toLowerCase().includes(search.toLowerCase()) ||
      v.toLowerCase().includes(search.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-500" />
            <span>Venues & Match Scheduler</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Schedule fixtures, assign match scorers, verify venue conflicts, and launch live scoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/admin/scoring"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs font-semibold shadow-sm hover:opacity-90 transition"
          >
            <PlayCircle className="w-4 h-4 text-emerald-500" />
            <span>Scoring Console</span>
          </Link>
          <button
            onClick={() => {
              setSelectedGenerateTournament(tournaments[0]?.tournament_id || '');
              setIsGenerateModalOpen(true);
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold shadow-sm transition"
          >
            <Sparkles className="w-4 h-4 text-emerald-500" />
            <span>Generate Schedule</span>
          </button>
          <button
            onClick={openScheduleModal}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Schedule Match</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl overflow-x-auto text-xs font-semibold">
          {[
            { id: 'ALL', label: 'All Fixtures' },
            { id: 'SCHEDULED', label: 'Scheduled' },
            { id: 'LIVE', label: 'Live' },
            { id: 'COMPLETED', label: 'Completed' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition ${
                statusFilter === tab.id
                  ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search teams or venues..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
      </div>

      {/* Matches Fixtures List */}
      {loading ? (
        <LoadingSkeleton rows={4} type="list" />
      ) : filteredMatches.length === 0 ? (
        <EmptyState
          title="No match fixtures found"
          description={
            search || statusFilter !== 'ALL'
              ? 'Try modifying your search or status filter.'
              : 'Schedule your first fixture or generate a round-robin schedule for a tournament.'
          }
          icon={Calendar}
          actionLabel="Schedule Match"
          onAction={openScheduleModal}
        />
      ) : (
        <div className="space-y-3">
          {filteredMatches.map((m) => {
            const isLive = m.status === 'IN_PROGRESS' || m.status === 'LIVE';
            const isCompleted = m.status === 'COMPLETED';
            const scorer = scorers.find((s) => s.user_id === m.scorer_id);

            return (
              <div
                key={m.match_id}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-300 dark:hover:border-slate-700 transition"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        isLive
                          ? 'bg-rose-500/10 text-rose-500 border border-rose-500/30 animate-pulse'
                          : isCompleted
                          ? 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                          : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                      }`}
                    >
                      {m.status}
                    </span>
                    <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {new Date(m.match_date).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {m.venue_name || 'Venue TBA'}
                    </span>
                    <span className="text-xs text-slate-400">({m.overs} overs quota)</span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>{m.team1_name}</span>
                    <span className="text-slate-400 font-normal text-xs">vs</span>
                    <span>{m.team2_name}</span>
                    {m.tournament_name && (
                      <span className="text-xs font-normal text-slate-400 dark:text-slate-500 ml-1">
                        • {m.tournament_name}
                      </span>
                    )}
                  </h3>

                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <UserCheck className="w-3.5 h-3.5 text-emerald-500" />
                      Assigned Scorer:{' '}
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {scorer ? scorer.name : m.scorer_id ? 'Assigned' : 'Unassigned'}
                      </span>
                    </span>
                    {m.result_summary && (
                      <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                        Result: {m.result_summary}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    to={`/admin/scoring`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
                  >
                    <PlayCircle className="w-4 h-4" />
                    <span>Scoring Console</span>
                  </Link>
                  <Link
                    to={`/match/${m.match_id}`}
                    target="_blank"
                    className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition"
                    title="View Public Scorecard"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Schedule Match Modal */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-500" />
                <span>Schedule New Fixture</span>
              </h3>
              <button
                onClick={closeScheduleModal}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Server Error Alert (e.g. Venue double-booking conflict) */}
            {serverError && (
              <div className="mt-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="font-bold">Scheduling Conflict Detected</p>
                  <p>{serverError}</p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit(onScheduleSubmit)} className="mt-4 space-y-4">
              {/* Tournament */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Tournament
                </label>
                <select
                  {...register('tournament_id')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {tournaments.map((t) => (
                    <option key={t.tournament_id} value={t.tournament_id}>
                      {t.name} ({t.format})
                    </option>
                  ))}
                </select>
                {errors.tournament_id && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.tournament_id.message}</p>
                )}
              </div>

              {/* Team 1 & Team 2 */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Team 1 (Home)
                  </label>
                  <select
                    {...register('team1_id')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    {teams.map((t) => (
                      <option key={t.team_id} value={t.team_id}>
                        {t.team_name}
                      </option>
                    ))}
                  </select>
                  {errors.team1_id && (
                    <p className="text-[11px] text-rose-500 mt-1">{errors.team1_id.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Team 2 (Away)
                  </label>
                  <select
                    {...register('team2_id')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    {teams.map((t) => (
                      <option key={t.team_id} value={t.team_id}>
                        {t.team_name}
                      </option>
                    ))}
                  </select>
                  {errors.team2_id && (
                    <p className="text-[11px] text-rose-500 mt-1">{errors.team2_id.message}</p>
                  )}
                </div>
              </div>

              {/* Venue & Overs */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Stadium Venue
                  </label>
                  <select
                    {...register('venue_id')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    {venues.map((v) => (
                      <option key={v.venue_id} value={v.venue_id}>
                        {v.venue_name} ({v.city})
                      </option>
                    ))}
                  </select>
                  {errors.venue_id && (
                    <p className="text-[11px] text-rose-500 mt-1">{errors.venue_id.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Overs Quota
                  </label>
                  <input
                    type="number"
                    {...register('overs')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {errors.overs && <p className="text-[11px] text-rose-500 mt-1">{errors.overs.message}</p>}
                </div>
              </div>

              {/* Match Date & Time */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Match Date & Time
                </label>
                <input
                  type="datetime-local"
                  {...register('match_date')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.match_date && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.match_date.message}</p>
                )}
              </div>

              {/* Assigned Scorer */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Assigned Match Scorer
                </label>
                <select
                  {...register('scorer_id')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Unassigned (Open for any authorized scorer)</option>
                  {scorers.map((s) => (
                    <option key={s.user_id} value={s.user_id}>
                      {s.name} ({s.email}) - {s.role.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={closeScheduleModal}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl shadow-sm transition"
                >
                  {isSubmitting ? 'Verifying & Scheduling...' : 'Schedule Match'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Generate Schedule Modal */}
      {isGenerateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-500" />
                <span>Generate Round-Robin Schedule</span>
              </h3>
              <button
                onClick={() => setIsGenerateModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <p className="text-xs text-slate-500">
                Select a tournament with registered teams to automatically generate all $n(n-1)/2$ round-robin fixtures without venue time conflicts.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Select Tournament
                </label>
                <select
                  value={selectedGenerateTournament}
                  onChange={(e) => setSelectedGenerateTournament(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {tournaments.map((t) => (
                    <option key={t.tournament_id} value={t.tournament_id}>
                      {t.name} ({t.team_count || 0} teams registered)
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleGenerateRoundRobin}
                  disabled={isGenerating}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl shadow-sm transition"
                >
                  {isGenerating ? 'Generating Fixtures...' : 'Generate Schedule'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
