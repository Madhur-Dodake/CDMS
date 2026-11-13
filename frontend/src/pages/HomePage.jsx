import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Calendar,
  Clock,
  MapPin,
  Radio,
  Shield,
  Trophy,
  Users,
  Zap,
} from 'lucide-react';
import apiClient, { matchesService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function HomePage() {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [liveMatches, setLiveMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadHomeData() {
      try {
        setLoading(true);
        const [dashRes, matchesRes] = await Promise.allSettled([
          apiClient.get('/api/dashboard/summary'),
          matchesService.list({ status: 'live', page_size: 5 }),
        ]);

        if (dashRes.status === 'fulfilled') {
          setDashboardStats(dashRes.value.data);
        }
        if (matchesRes.status === 'fulfilled') {
          setLiveMatches(matchesRes.value.data?.items || []);
        }
      } catch (err) {
        setError('Failed to load live match data');
      } finally {
        setLoading(false);
      }
    }
    loadHomeData();
  }, []);

  const featureCards = [
    {
      title: 'Real-Time Ball-by-Ball Engine',
      desc: 'Sub-second WebSocket broadcasts, live strike rotation, dot-to-boundary tracking, and deterministic replay undo.',
      icon: Radio,
      badge: 'LIVE ENGINE',
      link: '/live-scores',
      color: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
    },
    {
      title: 'Tournament Standings & NRR',
      desc: 'Pure ICC Net Run Rate calculator with all-out overs quota cap, automatic tie-breaks, and points tables.',
      icon: Trophy,
      badge: 'STANDINGS',
      link: '/tournaments',
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'Player Analytics & Career Profiles',
      desc: 'Batting strike rates, averages, milestones (50s/100s), bowling economies, and Recharts match performance curves.',
      icon: BarChart3,
      badge: 'ANALYTICS',
      link: '/players',
      color: 'text-sky-500 bg-sky-500/10 border-sky-500/20',
    },
    {
      title: 'Official Match Scorer Console',
      desc: 'Restricted scorer workflow enforcing playing XI validation, no consecutive bowler overs, and atomic state machine transitions.',
      icon: Shield,
      badge: 'OPERATIONS',
      link: '/admin/scoring',
      color: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    },
  ];

  return (
    <div className="space-y-12 pb-16">
      {/* 1. Dark Hero Section with Emerald Glow */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white border-b border-slate-800 py-16 sm:py-24">
        {/* Emerald Glow Background Gradients */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 right-10 w-72 h-72 bg-teal-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
            <Zap className="w-3.5 h-3.5" />
            <span>Cricket Data Management System</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-tight max-w-4xl mx-auto">
            Comprehensive Tournament, Live Scoring &{' '}
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-500 bg-clip-text text-transparent">
              Analytics Suite
            </span>
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            High-performance cricket operations platform featuring pure scoring mechanics, live WebSocket streams,
            deterministic NRR calculations, and career statistical modeling.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/live-scores"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-lg shadow-emerald-500/25 transition transform hover:-translate-y-0.5"
            >
              <Radio className="w-4 h-4 animate-pulse" />
              <span>Watch Live Scores</span>
            </Link>
            <Link
              to="/tournaments"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 font-semibold text-sm border border-slate-700 transition"
            >
              <span>Explore Tournaments</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Quick Counter Strip */}
          <div className="mt-12 pt-8 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto text-center">
            <div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                {dashboardStats?.tournaments_count ?? 2}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 font-medium">Tournaments</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-emerald-400">
                {dashboardStats?.teams_count ?? 4}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 font-medium">Teams Registered</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                {dashboardStats?.players_count ?? 60}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 font-medium">Pro Athletes</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-teal-400">
                {dashboardStats?.matches_count ?? 5}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 font-medium">Fixtures Logged</div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Live Now Strip */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
              Live Matches Now
            </h2>
          </div>
          <Link
            to="/live-scores"
            className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>View All Matches</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <LoadingSkeleton rows={1} type="card" />
        ) : error ? (
          <ErrorState message={error} />
        ) : liveMatches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {liveMatches.map((match) => (
              <div
                key={match.match_id}
                className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white border border-slate-700/80 shadow-card flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                    <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px]">
                      {match.tournament_name || 'Premier Cricket League'}
                    </span>
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-bold text-[10px] border border-rose-500/30">
                      <Radio className="w-3 h-3 animate-pulse" />
                      LIVE
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-base font-extrabold text-white">
                        {match.team1_name}
                      </span>
                      <span className="font-mono text-sm font-bold text-emerald-400">
                        Batting (1st Inn)
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-base font-extrabold text-slate-300">
                        {match.team2_name}
                      </span>
                      <span className="font-mono text-xs text-slate-400">Bowling</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mt-4 pt-3 border-t border-slate-700/60 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {match.venue_name || 'Stadium'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {match.overs} Overs Match
                    </span>
                  </div>
                </div>

                <div className="mt-5">
                  <Link
                    to={`/matches/${match.match_id}`}
                    className="w-full inline-flex items-center justify-center gap-2 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-sm transition"
                  >
                    <span>Launch Live Scorecard</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
            <Radio className="w-6 h-6 text-slate-400 mx-auto mb-2" />
            <p className="font-medium text-slate-700 dark:text-slate-300">
              No Matches Currently in Progress
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Check the upcoming fixtures tab to see upcoming scheduled matches.
            </p>
          </div>
        )}
      </section>

      {/* 3. 4 Feature Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-black text-slate-900 dark:text-white">
            Architected for Precision Cricket Management
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
            Layered architecture enforcing clean separation between pure domain rules and real-time presentation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featureCards.map((card, idx) => (
            <Link
              key={idx}
              to={card.link}
              className="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition transform hover:-translate-y-1 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span
                    className={`p-2.5 rounded-xl border ${card.color} group-hover:scale-110 transition`}
                  >
                    <card.icon className="w-5 h-5" />
                  </span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {card.badge}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition">
                  {card.title}
                </h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">{card.desc}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/80 flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400 group-hover:translate-x-1 transition">
                <span>Explore Module</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
