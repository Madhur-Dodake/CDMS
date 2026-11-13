import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import {
  Trophy,
  Plus,
  Search,
  Calendar,
  Users,
  Edit2,
  Trash2,
  Play,
  X,
  AlertCircle,
  Clock,
  Layers,
} from 'lucide-react';
import { tournamentsService } from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

const tournamentSchema = z.object({
  name: z.string().min(1, 'Tournament name is required').max(100, 'Name must be at most 100 characters'),
  level: z.enum(['local', 'club', 'domestic', 'international'], {
    errorMap: () => ({ message: 'Please select a valid tournament level' }),
  }),
  format: z.enum(['T20', 'ODI', 'Test', 'Other'], {
    errorMap: () => ({ message: 'Please select a valid format' }),
  }),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
}).refine((data) => !data.start_date || !data.end_date || data.end_date >= data.start_date, {
  message: 'End date cannot be earlier than start date',
  path: ['end_date'],
});

export default function AdminTournamentsPage() {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTournament, setEditingTournament] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(tournamentSchema),
    defaultValues: {
      name: '',
      level: 'domestic',
      format: 'T20',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
    },
  });

  const fetchTournaments = async () => {
    try {
      setLoading(true);
      const data = await tournamentsService.list({ page_size: 50 });
      setTournaments(data.items || []);
    } catch (err) {
      toast.error('Failed to load tournaments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTournaments();
  }, []);

  const openCreateModal = () => {
    setEditingTournament(null);
    setServerError('');
    reset({
      name: '',
      level: 'domestic',
      format: 'T20',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
    });
    setIsModalOpen(true);
  };

  const openEditModal = (t) => {
    setEditingTournament(t);
    setServerError('');
    setValue('name', t.name);
    setValue('level', t.level);
    setValue('format', t.format);
    setValue('start_date', t.start_date);
    setValue('end_date', t.end_date);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingTournament(null);
    setServerError('');
  };

  const onSubmit = async (data) => {
    setServerError('');
    setIsSubmitting(true);
    try {
      if (editingTournament) {
        await tournamentsService.update(editingTournament.tournament_id, data);
        toast.success(`Tournament "${data.name}" updated successfully!`);
      } else {
        await tournamentsService.create(data);
        toast.success(`Tournament "${data.name}" created successfully!`);
      }
      closeModal();
      fetchTournaments();
    } catch (err) {
      const msg = err.response?.data?.detail || 'An unexpected error occurred while saving tournament';
      setServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await tournamentsService.delete(deleteId);
      toast.success('Tournament deleted successfully');
      setDeleteId(null);
      fetchTournaments();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete tournament';
      toast.error(msg);
    }
  };

  const handleGenerateSchedule = async (tournamentId, name) => {
    setGeneratingId(tournamentId);
    try {
      const res = await tournamentsService.generateSchedule(tournamentId);
      toast.success(`Generated ${res.matches_generated} round-robin matches for ${name}!`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate schedule';
      toast.error(msg);
    } finally {
      setGeneratingId(null);
    }
  };

  const filteredTournaments = tournaments.filter((t) => {
    const matchesSearch = t.name.toLowerCase().includes(search.toLowerCase());
    const matchesLevel = levelFilter === 'all' || t.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-emerald-500" />
            <span>Tournaments Management</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Create, update, and manage tournaments, formats, and round-robin schedule generation
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Tournament</span>
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Level Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl overflow-x-auto text-xs font-semibold">
          {['all', 'domestic', 'international', 'club', 'local'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-3 py-1.5 rounded-lg capitalize whitespace-nowrap transition ${
                levelFilter === lvl
                  ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search tournaments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
      </div>

      {/* Tournaments Content */}
      {loading ? (
        <LoadingSkeleton rows={4} type="table" />
      ) : filteredTournaments.length === 0 ? (
        <EmptyState
          title="No tournaments found"
          description={
            search || levelFilter !== 'all'
              ? 'Try modifying your filter or search query.'
              : 'Create your first cricket tournament to begin scheduling matches.'
          }
          icon={Trophy}
          actionLabel="Create Tournament"
          onAction={openCreateModal}
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-3.5 px-4">Tournament</th>
                  <th className="py-3.5 px-4">Level</th>
                  <th className="py-3.5 px-4">Format</th>
                  <th className="py-3.5 px-4">Dates</th>
                  <th className="py-3.5 px-4">Teams</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredTournaments.map((t) => (
                  <tr key={t.tournament_id} className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition">
                    <td className="py-3.5 px-4 font-bold text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2.5">
                        <span className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold">
                          <Trophy className="w-4 h-4" />
                        </span>
                        <span>{t.name}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {t.level}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 font-semibold text-slate-800 dark:text-slate-200">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        {t.format}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {t.start_date} → {t.end_date}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400">
                        <Users className="w-3.5 h-3.5" />
                        {t.team_count || 0} registered
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => handleGenerateSchedule(t.tournament_id, t.name)}
                          disabled={generatingId === t.tournament_id}
                          title="Generate Round-Robin Schedule"
                          className="p-1.5 rounded-lg text-emerald-500 hover:bg-emerald-500/10 transition"
                        >
                          <Play className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => openEditModal(t)}
                          title="Edit Tournament"
                          className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteId(t.tournament_id)}
                          title="Delete Tournament"
                          className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-500/10 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
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
                <Trophy className="w-4 h-4 text-emerald-500" />
                <span>{editingTournament ? 'Edit Tournament' : 'New Tournament'}</span>
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
              {/* Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Tournament Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Indian Premier League 2026"
                  {...register('name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.name && <p className="text-[11px] text-rose-500 mt-1">{errors.name.message}</p>}
              </div>

              {/* Level & Format */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Level
                  </label>
                  <select
                    {...register('level')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 capitalize"
                  >
                    <option value="domestic">Domestic</option>
                    <option value="international">International</option>
                    <option value="club">Club</option>
                    <option value="local">Local</option>
                  </select>
                  {errors.level && <p className="text-[11px] text-rose-500 mt-1">{errors.level.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Match Format
                  </label>
                  <select
                    {...register('format')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="T20">T20 (20 Overs)</option>
                    <option value="ODI">ODI (50 Overs)</option>
                    <option value="Test">Test (Multi-Day)</option>
                    <option value="Other">Other</option>
                  </select>
                  {errors.format && <p className="text-[11px] text-rose-500 mt-1">{errors.format.message}</p>}
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    {...register('start_date')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {errors.start_date && <p className="text-[11px] text-rose-500 mt-1">{errors.start_date.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    {...register('end_date')}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                  {errors.end_date && <p className="text-[11px] text-rose-500 mt-1">{errors.end_date.message}</p>}
                </div>
              </div>

              {/* Buttons */}
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
                  {isSubmitting ? 'Saving...' : editingTournament ? 'Update Tournament' : 'Create Tournament'}
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
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Delete Tournament?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to delete this tournament? All associated fixtures and records will be affected.
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
