import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import {
  MapPin,
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  AlertCircle,
  Users,
  Compass,
} from 'lucide-react';
import { venuesService } from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

const venueSchema = z.object({
  venue_name: z.string().min(1, 'Venue name is required').max(100),
  city: z.string().min(1, 'City is required').max(100),
  capacity: z
    .preprocess(
      (val) => (val === '' || val === null || val === undefined ? undefined : Number(val)),
      z.number({ invalid_type_error: 'Capacity must be a valid number' }).min(0, 'Capacity must be positive').optional()
    ),
});

export default function AdminVenuesPage() {
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVenue, setEditingVenue] = useState(null);
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
    resolver: zodResolver(venueSchema),
    defaultValues: {
      venue_name: '',
      city: '',
      capacity: 35000,
    },
  });

  const fetchVenues = async () => {
    try {
      setLoading(true);
      const data = await venuesService.list({ page_size: 50 });
      setVenues(data.items || []);
    } catch (err) {
      toast.error('Failed to load venues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVenues();
  }, []);

  const openCreateModal = () => {
    setEditingVenue(null);
    setServerError('');
    reset({
      venue_name: '',
      city: '',
      capacity: 35000,
    });
    setIsModalOpen(true);
  };

  const openEditModal = (v) => {
    setEditingVenue(v);
    setServerError('');
    setValue('venue_name', v.venue_name);
    setValue('city', v.city);
    setValue('capacity', v.capacity || '');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingVenue(null);
    setServerError('');
  };

  const onSubmit = async (data) => {
    setServerError('');
    setIsSubmitting(true);
    try {
      const payload = {
        venue_name: data.venue_name,
        city: data.city,
        capacity: data.capacity !== undefined ? data.capacity : null,
      };

      if (editingVenue) {
        await venuesService.update(editingVenue.venue_id, payload);
        toast.success(`Venue "${data.venue_name}" updated successfully!`);
      } else {
        await venuesService.create(payload);
        toast.success(`Venue "${data.venue_name}" added successfully!`);
      }
      closeModal();
      fetchVenues();
    } catch (err) {
      const msg = err.response?.data?.detail || 'An unexpected error occurred while saving venue';
      setServerError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await venuesService.delete(deleteId);
      toast.success('Venue deleted successfully');
      setDeleteId(null);
      fetchVenues();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to delete venue';
      toast.error(msg);
    }
  };

  const filteredVenues = venues.filter((v) => {
    const q = search.toLowerCase();
    return v.venue_name.toLowerCase().includes(q) || v.city.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-emerald-500" />
            <span>Venues & Stadiums</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage stadium locations, spectator capacity, and venue availability schedules
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add Venue</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search venues by name or city..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition"
        />
      </div>

      {/* Venues Grid */}
      {loading ? (
        <LoadingSkeleton rows={6} type="card" />
      ) : filteredVenues.length === 0 ? (
        <EmptyState
          title="No venues registered"
          description={search ? 'No venues match your search query.' : 'Add your first cricket stadium to host matches and tournaments.'}
          icon={MapPin}
          actionLabel="Add Venue"
          onAction={openCreateModal}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredVenues.map((venue) => (
            <div
              key={venue.venue_id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col justify-between hover:border-emerald-500/50 transition group"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                      <Compass className="w-5 h-5" />
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition">
                        {venue.venue_name}
                      </h3>
                      <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {venue.city}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openEditModal(venue)}
                      title="Edit Venue"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setDeleteId(venue.venue_id)}
                      title="Delete Venue"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-500 flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    Spectator Capacity:
                  </span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {venue.capacity ? Number(venue.capacity).toLocaleString() : 'Not Specified'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-500" />
                <span>{editingVenue ? 'Edit Venue' : 'Register New Venue'}</span>
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
                  Stadium / Venue Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Wankhede Stadium"
                  {...register('venue_name')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.venue_name && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.venue_name.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  City
                </label>
                <input
                  type="text"
                  placeholder="e.g. Mumbai"
                  {...register('city')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.city && <p className="text-[11px] text-rose-500 mt-1">{errors.city.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Seating Capacity
                </label>
                <input
                  type="number"
                  placeholder="e.g. 33000"
                  {...register('capacity')}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                />
                {errors.capacity && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.capacity.message}</p>
                )}
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
                  {isSubmitting ? 'Saving...' : editingVenue ? 'Update Venue' : 'Add Venue'}
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
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Delete Venue?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to delete this venue? Stadiums with assigned matches cannot be deleted.
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
