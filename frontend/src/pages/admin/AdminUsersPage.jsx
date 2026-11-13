import React from 'react';
import { UserCheck, Plus, Shield, User } from 'lucide-react';

export default function AdminUsersPage() {
  const users = [
    { id: 1, email: 'admin@cdms.com', name: 'Admin Master', role: 'admin', status: 'Active' },
    { id: 2, email: 'scorer@cdms.com', name: 'Official Scorer', role: 'scorer', status: 'Active' },
    { id: 3, email: 'viewer@cdms.com', name: 'Cricket Fan', role: 'viewer', status: 'Active' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-emerald-500" />
            <span>User & Access Control Management</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage user roles (Admin, Scorer, Viewer), privilege elevation, and credentials
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition">
          <Plus className="w-4 h-4" />
          <span>Invite User</span>
        </button>
      </div>

      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-3">User</th>
                <th className="py-3 px-3">Email</th>
                <th className="py-3 px-3">Assigned Role</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300">
                      <User className="w-3.5 h-3.5" />
                    </span>
                    <span>{u.name}</span>
                  </td>
                  <td className="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono">{u.email}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        u.role === 'admin'
                          ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                          : u.role === 'scorer'
                          ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                          : 'bg-slate-500/10 text-slate-500 border border-slate-500/20'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="inline-flex items-center gap-1.5 text-xs text-emerald-500">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      {u.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button className="text-xs font-semibold text-emerald-500 hover:text-emerald-600">
                      Edit Role
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

