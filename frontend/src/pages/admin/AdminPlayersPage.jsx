import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import {
  Users,
  Plus,
  Search,
  Edit2,
  Trash2,
  Filter,
  X,
  AlertCircle,
  Calendar,
  Shield,
  User,
} from 'lucide-react';
import { playersService, teamsService } from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

const playerSchema = z.object({
  name: z.string().min(1, 'Player name is required').max(100),
  team_id: z.string().optional().or(z.literal('')),
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

export default function AdminPlayersPage() {
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [teamFilter, setTeamFilter] = useState('all');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm({
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

  const fetchData = async () => {
    try {
      setLoading(true);
      const [playersRes, teamsRes] = await Promise.all([
        playersService.list({ page_size: 100 }),
        teamsService.list({ page_size: 50 }),
      ]);
      setPlayers(playersRes.items || []);
      setTeams(teamsRes.items || []);
    } catch (err) {
      toast.error('Failed to load player directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCreateModal = () => {
    setEditingPlayer(null);
    setServerError('');
    reset({
      name: '',
      team_id: teams[0]?.team_id || '',
      role: 'Batter',
      batting_style: 'Right-hand bat',
      bowling_style: 'Right-arm medium',
      dob: '2000-01-01',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (p) => {
    setEditingPlayer(p);
    setServerError('');
    setValue('name', p.name);
    setValue('team_id', p.team_id || '');
    setValue('role', p.role || 'Batter');
    setValue('batting_style', p.batting_style || 'Right-hand bat');
    setValue('bowling_style', p.bowling_style || '');
    setValue('dob', p.dob || '');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingPlayer(null);
    setServerError('');
  };

  const onSubmit = async (data) => {
    setServerError('');
    setIsSubmitting(true);
    try {
      const payload = {
        name: data.name,
        team_id: data.team_id ? data.team_id : null,
        role: data.role,
        batting_style: data.batting_style,
        bowling_style: data.bowling_style || null,
        dob: data.dob || null,
      };

      if (editingPlayer) {
        await playersService.update(editingPlayer.player_id, payload);
        toast.success(`Player "${data.name}" updated successfully!`);
      } else {
        await playersService.create(payload);
        toast.success(`Player "${data.name}" created successfully!`);
      }
      closeModal();
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'An unexpected error occurred while saving player';
      setServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await playersService.delete(deleteId);
      toast.success('Player deleted successfully');
      setDeleteId(null);
      fetchData();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete player';
      toast.error(msg);
    }
  };

  const filteredPlayers = players.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === 'All' || p.role === roleFilter;
    const matchesTeam = teamFilter === 'all' || p.team_id === teamFilter;
    return matchesSearch && matchesRole && matchesTeam;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-500" />
            <span>Player Registry</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Register player profiles, date of birth validations, and batting/bowling classifications
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add Player</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Role Filters */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl overflow-x-auto text-xs font-semibold">
          {['All', 'Batter', 'Bowler', 'All-Rounder', 'Wicketkeeper'].map((role) => (
            <button
              key={role}
              onClick={() => setRoleFilter(role)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition ${
                roleFilter === role
                  ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {role}
            </button>
          ))}
        </div>

        {/* Team filter & Search */}
        <div className="flex items-center gap-3">
          <select
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Teams</option>
            {teams.map((t) => (
              <option key={t.team_id} value={t.team_id}>
                {t.team_name}
              </option>
            ))}
          </select>

          <div className="relative w-full md:w-56">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search players..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition"
            />
          </div>
        </div>
      </div>

      {/* Players Table */}
      {loading ? (
        <LoadingSkeleton rows={5} type="table" />
      ) : filteredPlayers.length === 0 ? (
        <EmptyState
          title="No players found"
          description={
            search || roleFilter !== 'All' || teamFilter !== 'all'
              ? 'Try adjusting your search query or filters.'
              : 'Add player profiles to assign them to team rosters.'
          }
          icon={Users}
          actionLabel="Add Player"
          onAction={openCreateModal}
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-3.5 px-4">Player</th>
                  <th className="py-3.5 px-4">Team</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Batting</th>
                  <th className="py-3.5 px-4">Bowling</th>
                  <th className="py-3.5 px-4">DOB</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredPlayers.map((p) => {
                  const team = teams.find((t) => t.team_id === p.team_id);
                  return (
                    <tr key={p.player_id} className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
                        <span className="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300">
                          <User className="w-3.5 h-3.5" />
                        </span>
                        <span>{p.name}</span>
                      </td>
                      <td className="py-3 px-4">
                        {team ? (
                          <span className="inline-flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-300">
                            <Shield className="w-3.5 h-3.5 text-emerald-500" />
                            {team.team_name}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">Unassigned</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {p.role || 'Player'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400">{p.batting_style || '—'}</td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400">{p.bowling_style || '—'}</td>
                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">{p.dob || '—'}</td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => openEditModal(p)}
                            title="Edit Player"
                            className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => setDeleteId(p.player_id)}
                            title="Delete Player"
                            className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-500/10 transition"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-500" />
                <span>{editingPlayer ? 'Edit Player' : 'Register New Player'}</span>
              </h3>
              <button
                onClick={closeModal}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {serverError && (
              <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{serverError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Virat Kohli"
                  {...register('name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.name && <p className="text-[11px] text-rose-500 mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Team Assignment
                </label>
                <select
                  {...register('team_id')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Unassigned (Free Agent)</option>
                  {teams.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.team_name} ({t.city})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Playing Role
                  </label>
                  <select
                    {...register('role')}
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
                    {...register('batting_style')}
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
                    placeholder="e.g. Right-arm medium"
                    {...register('bowling_style')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    {...register('dob')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {errors.dob && <p className="text-[11px] text-rose-500 mt-1">{errors.dob.message}</p>}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl shadow-sm transition"
                >
                  {isSubmitting ? 'Saving...' : editingPlayer ? 'Update Player' : 'Register Player'}
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
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Delete Player?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to delete this player? Career match statistics and scoring records may be affected.
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
                onClick={handleDelete}
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
