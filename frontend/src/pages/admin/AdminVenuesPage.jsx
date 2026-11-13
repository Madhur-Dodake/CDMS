import React from 'react';
import { MapPin, Plus } from 'lucide-react';

export default function AdminVenuesPage() {
  const venues = [
    { id: 1, name: 'Eden Gardens', city: 'Kolkata', country: 'India', capacity: '66,000' },
    { id: 2, name: 'Wankhede Stadium', city: 'Mumbai', country: 'India', capacity: '33,000' },
    { id: 3, name: 'Lord\'s Cricket Ground', city: 'London', country: 'UK', capacity: '30,000' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-emerald-500" />
            <span>Venues Management</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage stadiums, pitch conditions, and venue availability schedules
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition">
          <Plus className="w-4 h-4" />
          <span>Add Venue</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {venues.map((venue) => (
          <div
            key={venue.id}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">{venue.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{venue.city}, {venue.country}</p>
              </div>
              <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                <MapPin className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-between text-xs">
              <span className="text-slate-500">Capacity</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">{venue.capacity}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

