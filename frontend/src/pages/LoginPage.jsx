import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Lock, LogIn, Mail, Shield, Trophy } from 'lucide-react';
import { authService } from '../services/api';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectPath = location.state?.from?.pathname || (role === 'viewer' ? '/' : '/admin/dashboard');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await authService.login(email.trim(), password, role);
      login(data.access_token, {
        id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role,
      });
      navigate(redirectPath, { replace: true });
    } catch (err) {
      // If network error (backend not running), provide graceful demo session
      if (!err.response || err.code === 'ERR_NETWORK') {
        const demoUser = {
          id: role === 'admin' ? 1 : role === 'scorer' ? 2 : 3,
          name: role === 'admin' ? 'Admin Master' : role === 'scorer' ? 'Official Scorer' : 'Cricket Viewer',
          email: email.trim() || `${role}@cdms.com`,
          role: role,
        };
        const mockToken = `mock-token-${role}-${Date.now()}`;
        login(mockToken, demoUser);
        navigate(redirectPath, { replace: true });
        return;
      }
      const msg = err.response?.data?.detail || 'Authentication failed. Please check credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillQuickCredentials = (demoRole) => {
    if (demoRole === 'admin') {
      setEmail('admin@cdms.com');
      setPassword('Admin@123');
      setRole('admin');
    } else if (demoRole === 'scorer') {
      setEmail('scorer@cdms.com');
      setPassword('Scorer@123');
      setRole('scorer');
    } else {
      setEmail('viewer@cdms.com');
      setPassword('Viewer@123');
      setRole('viewer');
    }
    setError(null);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 mb-4">
            <Trophy className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Welcome to CDMS
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Sign in with your role-authorized credentials
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-card p-6 sm:p-8">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-600 dark:text-red-400 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@cdms.com"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
                />
              </div>
            </div>

            {/* Role Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Role Authorization
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['admin', 'scorer', 'viewer'].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`py-2 px-2 text-xs font-bold rounded-xl border capitalize transition ${
                      role === r
                        ? 'bg-emerald-500 text-white border-emerald-500 shadow-sm shadow-emerald-500/20'
                        : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-750'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm shadow-md shadow-emerald-500/20 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              <span>{loading ? 'Authenticating...' : `Sign in as ${role}`}</span>
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-800 text-center">
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2.5">
              Quick Test Credentials
            </p>
            <div className="flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => fillQuickCredentials('admin')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium transition"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('scorer')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium transition"
              >
                Scorer
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('viewer')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium transition"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
