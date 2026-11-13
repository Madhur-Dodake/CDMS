import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import toast from 'react-hot-toast';
import {
  AlertCircle,
  Eye,
  EyeOff,
  Lock,
  LogIn,
  Mail,
  Shield,
  Trophy,
  User,
} from 'lucide-react';
import { authService } from '../services/api';
import { useAuthStore } from '../store/authStore';

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export default function LoginPage() {
  const [activeRole, setActiveRole] = useState('admin'); // 'admin' | 'scorer' | 'viewer'
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectPath = location.state?.from?.pathname || (activeRole === 'viewer' ? '/' : '/admin/dashboard');

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'admin@cdms.com',
      password: '',
    },
  });

  const onSubmit = async (data) => {
    setServerError(null);
    setLoading(true);

    try {
      const res = await authService.login(data.email.trim(), data.password, activeRole);
      login(res.access_token, {
        id: res.user_id,
        name: res.name,
        email: res.email,
        role: res.role,
      });
      toast.success(`Welcome back, ${res.name || activeRole}!`);
      navigate(redirectPath, { replace: true });
    } catch (err) {
      if (!err.response || err.code === 'ERR_NETWORK') {
        // Offline / dev fallback
        const demoUser = {
          id: activeRole === 'admin' ? 1 : activeRole === 'scorer' ? 2 : 3,
          name: activeRole === 'admin' ? 'System Administrator' : activeRole === 'scorer' ? 'Official Scorer' : 'Cricket Fan',
          email: data.email.trim() || `${activeRole}@cdms.com`,
          role: activeRole,
        };
        login(`mock-token-${activeRole}-${Date.now()}`, demoUser);
        toast.success(`Signed in as ${demoUser.name} (Dev Mode)`);
        navigate(redirectPath, { replace: true });
        return;
      }

      const msg = err.response?.data?.detail || 'Invalid email, password, or role selection.';
      setServerError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillQuickCredentials = (role) => {
    setActiveRole(role);
    setServerError(null);
    if (role === 'admin') {
      setValue('email', 'admin@cdms.com');
      setValue('password', 'admin123');
    } else if (role === 'scorer') {
      setValue('email', 'scorer1@cdms.com');
      setValue('password', 'scorer123');
    } else {
      setValue('email', 'viewer@cdms.com');
      setValue('password', 'viewer123');
    }
    toast(`Filled ${role} demo credentials`, { icon: '🔑' });
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 mb-4">
            <Trophy className="w-6 h-6" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
            Sign In to CDMS
          </h1>
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            Select your role and authenticate with authorized credentials
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-card p-6 sm:p-8 space-y-6">
          {/* Admin / Scorer / Viewer Tab Switcher */}
          <div>
            <div className="grid grid-cols-3 p-1 rounded-2xl bg-slate-100 dark:bg-slate-800 text-xs font-bold">
              <button
                type="button"
                onClick={() => fillQuickCredentials('admin')}
                className={`py-2 px-2 rounded-xl transition ${
                  activeRole === 'admin'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                Administrator
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('scorer')}
                className={`py-2 px-2 rounded-xl transition ${
                  activeRole === 'scorer'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                Match Scorer
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('viewer')}
                className={`py-2 px-2 rounded-xl transition ${
                  activeRole === 'viewer'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                Public Viewer
              </button>
            </div>
          </div>

          {/* Server Error Alert */}
          {serverError && (
            <div className="p-3.5 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-600 dark:text-red-400 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  {...register('email')}
                  placeholder="admin@cdms.com"
                  className="w-full pl-10 pr-3 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-[11px] text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Password Field with Show/Hide toggle */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  {...register('password')}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-[11px] text-red-500">{errors.password.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-md shadow-emerald-500/20 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              <span>{loading ? 'Authenticating...' : `Sign In as ${activeRole}`}</span>
            </button>
          </form>

          {/* Quick Test Demo Credentials */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Quick Test Credentials
            </p>
            <div className="flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => fillQuickCredentials('admin')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('scorer')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition"
              >
                Scorer
              </button>
              <button
                type="button"
                onClick={() => fillQuickCredentials('viewer')}
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition"
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
