import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Calendar,
  CheckCircle2,
  Radio,
  Shield,
  Trophy,
  Users,
  Zap,
} from 'lucide-react';
import apiClient from '../services/api';

export default function HomePage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get('/api/dashboard/summary')
      .then((res) => {
        setStats(res.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const features = [
    {
      title: 'Live Ball-by-Ball Scoring',
      desc: 'Sub-second real-time broadcasts powered by native WebSockets with replay-based undo.',
      icon: Radio,
      badge: 'LIVE ENGINE',
      to: '/live-scores',
      color: 'text-red-500 bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900',
    },
    {
      title: 'Tournament Operations',
      desc: 'Round-robin fixture generation with automated venue conflict prevention and schedule tracking.',
      icon: Trophy,
      badge: 'ADMIN',
      to: '/tournaments',
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900',
    },
    {
      title: 'Cumulative Points & NRR',
      desc: 'Deterministic ICC Net Run Rate computational engine with all-out quota cap and instant tie-breaks.',
      icon: BarChart3,
      badge: 'STANDINGS',
      to: '/tournaments',
      color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900',
    },
    {
      title: 'Team & Player Profiles',
      desc: 'Comprehensive player career stats, batting averages, strike rates, bowling economies, and 50s/100s milestones.',
      icon: Users,
      badge: 'ROSTERS',
      to: '/players',
      color: 'text-purple-500 bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-900',
    },
  ];

  return (
    <div>
      {/* Dark Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-white py-16 sm:py-24 border-b border-slate-800">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(16,185,129,0.15),rgba(255,255,255,0))]"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
            <Zap className="w-3.5 h-3.5" />
            <span>Cricket Data Management System</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
            Comprehensive Cricket Operations,{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              Zero Clutter.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Tournament administration, deterministic ball-by-ball scoring, real-time viewer scorecards, and automated Net Run Rate computations.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/live-scores"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold shadow-lg shadow-emerald-500/25 transition transform hover:-translate-y-0.5"
            >
              <Radio className="w-4 h-4 text-white" />
              <span>Watch Live Matches</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/tournaments"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold transition"
            >
              <Trophy className="w-4 h-4 text-emerald-400" />
              <span>Explore Tournaments</span>
            </Link>
          </div>

          {/* Quick Metrics Strip */}
          <div className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur">
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                {loading ? '...' : stats?.total_tournaments ?? 2}
              </p>
              <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                Tournaments
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur">
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                {loading ? '...' : stats?.total_teams ?? 4}
              </p>
              <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                Teams
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur">
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                {loading ? '...' : stats?.total_players ?? 60}
              </p>
              <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                Players
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur">
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                {loading ? '...' : stats?.scheduled_matches ?? 6}
              </p>
              <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                Fixtures
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Cards Grid (Rounded White Cards in Light, Slate Cards in Dark) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Engineered for Academic Precision & Speed
          </h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
            Strict three-tier Role-Based Access Control (Admin, Scorer, Viewer), pure domain scoring arithmetic, and native WebSocket broadcasts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((f) => (
            <Link
              key={f.title}
              to={f.to}
              className="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl border ${f.color}`}>
                    <f.icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {f.badge}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition">
                  {f.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {f.desc}
                </p>
              </div>

              <div className="mt-6 flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400 group-hover:translate-x-1 transition duration-150">
                <span>View Details</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
