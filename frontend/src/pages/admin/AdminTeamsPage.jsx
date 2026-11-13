import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import {
  Shield,
  Plus,
  Search,
  Users,
  UserPlus,
  Edit2,
  Trash2,
  MapPin,
  X,
  AlertCircle,
  Award,
} from 'lucide-react';
import { teamsService, playersService } from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

const teamSchema = z.object({
  team_name: z.string().min(1, 'Team name is required').max(100, 'Name must be at most 100 characters'),
  short_code: z
    .string()
    .min(2, 'Short code must be at least 2 characters')
    .max(10, 'Short code must be at most 10 characters')
    .toUpperCase(),
  city: z.string().min(1, 'City is required').max(100),
  coach_name: z.string().max(100).optional().or(z.literal('')),
  logo_url: z.string().max(255).optional().or(z.literal('')),
});

const playerSchema = z.object({
  name: z.string().min(1, 'Player name is required').max(100),
  team_id: z.string().min(1, 'Team selection is required'),
  role: z.enum(['Batter', 'Bowler', 'All-Rounder', 'Wicketkeeper']),
  batting_style: z.enum(['Right-hand bat', 'Left-hand bat']),
  bowling_style: z.string().optional().or(z.literal('')),
  dob: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine((val) => !val || new Date(val) <= new Date(), {
      message: 'Date of birth cannot be in the future',
    }),
});

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Team Modal state
  const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [teamServerError, setTeamServerError] = useState('');

  // Player Modal state
  const [isPlayerModalOpen, setIsPlayerModalOpen] = useState(false);
  const [selectedTeamForPlayer, setSelectedTeamForPlayer] = useState(null);
  const [playerServerError, setPlayerServerError] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form for Team
  const teamForm = useForm({
    resolver: zodResolver(teamSchema),
    defaultValues: {
      team_name: '',
      short_code: '',
      city: '',
      coach_name: '',
      logo_url: '',
    },
  });

  // Form for Add Player
  const playerForm = useForm({
    resolver: zodResolver(playerSchema),
    defaultValues: {
      name: '',
      team_id: '',
      role: 'Batter',
      batting_style: 'Right-hand bat',
      bowling_style: 'Right-arm medium',
      dob: '2000-01-01',
    },
  });

  const fetchTeams = async () => {
    try {
      setLoading(true);
      const data = await teamsService.list({ page_size: 50 });
      setTeams(data.items || []);
    } catch (err) {
      toast.error('Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  // Team Modal Handlers
  const openCreateTeamModal = () => {
    setEditingTeam(null);
    setTeamServerError('');
    teamForm.reset({
      team_name: '',
      short_code: '',
      city: '',
      coach_name: '',
      logo_url: '',
    });
    setIsTeamModalOpen(true);
  };

  const openEditTeamModal = (team) => {
    setEditingTeam(team);
    setTeamServerError('');
    teamForm.setValue('team_name', team.team_name);
    teamForm.setValue('short_code', team.short_code || '');
    teamForm.setValue('city', team.city);
    teamForm.setValue('coach_name', team.coach_name || '');
    teamForm.setValue('logo_url', team.logo_url || '');
    setIsTeamModalOpen(true);
  };

  const closeTeamModal = () => {
    setIsTeamModalOpen(false);
    setEditingTeam(null);
    setTeamServerError('');
  };

  const onTeamSubmit = async (data) => {
    setTeamServerError('');
    setIsSubmitting(true);
    try {
      if (editingTeam) {
        await teamsService.update(editingTeam.team_id, data);
        toast.success(`Team "${data.team_name}" updated successfully!`);
      } else {
        await teamsService.create(data);
        toast.success(`Team "${data.team_name}" created successfully!`);
      }
      closeTeamModal();
      fetchTeams();
    } catch (err) {
      const msg = err.response?.data?.detail || 'An unexpected error occurred while saving team';
      setTeamServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTeam = async () => {
    if (!deleteId) return;
    try {
      await teamsService.delete(deleteId);
      toast.success('Team deleted successfully');
      setDeleteId(null);
      fetchTeams();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete team';
      toast.error(msg);
    }
  };

  // Player Modal Handlers
  const openAddPlayerModal = (team) => {
    setSelectedTeamForPlayer(team);
    setPlayerServerError('');
    playerForm.reset({
      name: '',
      team_id: team ? team.team_id : teams[0]?.team_id || '',
      role: 'Batter',
      batting_style: 'Right-hand bat',
      bowling_style: 'Right-arm medium',
      dob: '2000-01-01',
    });
    setIsPlayerModalOpen(true);
  };

  const closePlayerModal = () => {
    setIsPlayerModalOpen(false);
    setSelectedTeamForPlayer(null);
    setPlayerServerError('');
  };

  const onPlayerSubmit = async (data) => {
    setPlayerServerError('');
    setIsSubmitting(true);
    try {
      const payload = {
        name: data.name,
        team_id: data.team_id,
        role: data.role,
        batting_style: data.batting_style,
        bowling_style: data.bowling_style || null,
        dob: data.dob || null,
      };
      await playersService.create(payload);
      toast.success(`Player "${data.name}" registered successfully!`);
      closePlayerModal();
      fetchTeams(); // refresh player counts
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to register player';
      setPlayerServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredTeams = teams.filter((t) => {
    const q = search.toLowerCase();
    return t.team_name.toLowerCase().includes(q) || t.city.toLowerCase().includes(q) || (t.short_code || '').toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-500" />
            <span>Teams & Squads</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Register tournament teams, assign coaching staff, and manage franchise rosters
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => openAddPlayerModal(null)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold shadow-sm transition"
          >
            <UserPlus className="w-4 h-4 text-emerald-500" />
            <span>Add Player</span>
          </button>
          <button
            onClick={openCreateTeamModal}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Register Team</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-sm">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search by team name, code, or city..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition"
        />
      </div>

      {/* Teams Grid */}
      {loading ? (
        <LoadingSkeleton rows={6} type="card" />
      ) : filteredTeams.length === 0 ? (
        <EmptyState
          title="No teams registered"
          description={search ? 'No teams match your search criteria.' : 'Register your first cricket team to build squads and schedule matches.'}
          icon={Shield}
          actionLabel="Register Team"
          onAction={openCreateTeamModal}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTeams.map((team) => (
            <div
              key={team.team_id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col justify-between hover:border-emerald-500/50 transition group"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 flex items-center justify-center font-black text-emerald-500 text-base">
                      {team.short_code || team.team_name.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition">
                        {team.team_name}
                      </h3>
                      <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {team.city}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openEditTeamModal(team)}
                      title="Edit Team"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setDeleteId(team.team_id)}
                      title="Delete Team"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Head Coach:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {team.coach_name || 'Not Assigned'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Squad Size:</span>
                    <span className="font-semibold text-emerald-500 flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      {team.player_count || 0} players
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end">
                <button
                  onClick={() => openAddPlayerModal(team)}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-500 hover:text-emerald-600 transition"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Add Player</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Team Modal */}
      {isTeamModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                <span>{editingTeam ? 'Edit Team Details' : 'Register New Team'}</span>
              </h3>
              <button
                onClick={closeTeamModal}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {teamServerError && (
              <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{teamServerError}</span>
              </div>
            )}

            <form onSubmit={teamForm.handleSubmit(onTeamSubmit)} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Team Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Mumbai Titans"
                  {...teamForm.register('team_name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {teamForm.formState.errors.team_name && (
                  <p className="text-[11px] text-rose-500 mt-1">{teamForm.formState.errors.team_name.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Short Code
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. MT"
                    maxLength={10}
                    {...teamForm.register('short_code')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white uppercase focus:outline-none focus:border-emerald-500"
                  />
                  {teamForm.formState.errors.short_code && (
                    <p className="text-[11px] text-rose-500 mt-1">{teamForm.formState.errors.short_code.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    City / Home
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Mumbai"
                    {...teamForm.register('city')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {teamForm.formState.errors.city && (
                    <p className="text-[11px] text-rose-500 mt-1">{teamForm.formState.errors.city.message}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Head Coach
                </label>
                <input
                  type="text"
                  placeholder="e.g. Mahela Jayawardene"
                  {...teamForm.register('coach_name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={closeTeamModal}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl shadow-sm transition"
                >
                  {isSubmitting ? 'Saving...' : editingTeam ? 'Update Team' : 'Register Team'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Player Modal */}
      {isPlayerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-emerald-500" />
                <span>Add Player to Squad</span>
              </h3>
              <button
                onClick={closePlayerModal}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {playerServerError && (
              <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{playerServerError}</span>
              </div>
            )}

            <form onSubmit={playerForm.handleSubmit(onPlayerSubmit)} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Team
                </label>
                <select
                  {...playerForm.register('team_id')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {teams.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.team_name} ({t.city})
                    </option>
                  ))}
                </select>
                {playerForm.formState.errors.team_id && (
                  <p className="text-[11px] text-rose-500 mt-1">{playerForm.formState.errors.team_id.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Player Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Rohit Sharma"
                  {...playerForm.register('name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {playerForm.formState.errors.name && (
                  <p className="text-[11px] text-rose-500 mt-1">{playerForm.formState.errors.name.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Playing Role
                  </label>
                  <select
                    {...playerForm.register('role')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Batter">Batter</option>
                    <option value="Bowler">Bowler</option>
                    <option value="All-Rounder">All-Rounder</option>
                    <option value="Wicketkeeper">Wicketkeeper</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Batting Style
                  </label>
                  <select
                    {...playerForm.register('batting_style')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Right-hand bat">Right-hand bat</option>
                    <option value="Left-hand bat">Left-hand bat</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Bowling Style
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Right-arm fast"
                    {...playerForm.register('bowling_style')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    {...playerForm.register('dob')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {playerForm.formState.errors.dob && (
                    <p className="text-[11px] text-rose-500 mt-1">{playerForm.formState.errors.dob.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={closePlayerModal}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl shadow-sm transition"
                >
                  {isSubmitting ? 'Registering...' : 'Add Player'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Delete Team?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to delete this team? Teams with existing match fixtures cannot be deleted.
              </p>
            </div>
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setDeleteId(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteTeam}
                className="px-4 py-2 text-xs font-semibold text-white bg-rose-500 hover:bg-rose-600 rounded-xl shadow-sm transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
