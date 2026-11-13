import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, LogIn, ShieldAlert } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function ForbiddenPage() {
  const { role, user } = useAuthStore();
  const location = useLocation();
  const requiredRoles = location.state?.requiredRoles || ['admin'];

  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-3xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-500 flex items-center justify-center mx-auto mb-6 border border-amber-500/30">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
          403 - Access Forbidden
        </h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
          Your current account role (<span className="font-bold text-amber-500 uppercase">{role || 'viewer'}</span>) does not possess privileges to access this management module.
        </p>

        <div className="my-6 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300 shadow-card">
          <p>
            Required Authorization: <span className="font-semibold text-emerald-500">{requiredRoles.join(', ')}</span>
          </p>
          <p className="mt-1 text-slate-400">
            Signed in as: <span className="text-slate-200">{user?.email || 'Anonymous'}</span>
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-800 text-white text-xs font-semibold hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Public Home</span>
          </Link>
          <Link
            to="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign in as Admin</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

