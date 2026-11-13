import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  Radio,
  Trophy,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { matchesService } from '../services/api';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function LiveScoresPage() {
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'upcoming' | 'completed'
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMatches = async (tab) => {
    try {
      setLoading(true);
      setError(null);
      const statusParam = tab === 'live' ? 'live' : tab === 'upcoming' ? 'scheduled' : 'completed';
      const data = await matchesService.list({ status: statusParam, page_size: 20 });
      setMatches(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch match fixtures');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatches(activeTab);
  }, [activeTab]);

  const tabs = [
    { id: 'live', label: 'Live Now', icon: Radio, count: null },
    { id: 'upcoming', label: 'Upcoming Fixtures', icon: Calendar, count: null },
    { id: 'completed', label: 'Completed Results', icon: CheckCircle2, count: null },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-rose-500 animate-pulse" />
            <span>Match Center & Live Scores</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time cricket ball updates, upcoming tournament fixtures, and official match scorecards
          </p>
        </div>

        <button
          onClick={() => fetchMatches(activeTab)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-2 sm:space-x-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 px-2 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition ${
                isActive
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${tab.id === 'live' && isActive ? 'text-rose-500 animate-pulse' : ''}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Match Cards List */}
      {loading ? (
        <LoadingSkeleton rows={3} type="card" />
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchMatches(activeTab)} />
      ) : matches.length === 0 ? (
        <EmptyState
          title={`No ${activeTab} matches found`}
          description={
            activeTab === 'live'
              ? 'There are currently no active live matches in progress. Check the Upcoming Fixtures tab!'
              : `No ${activeTab} fixtures are available in the schedule at this moment.`
          }
          icon={activeTab === 'live' ? Radio : Calendar}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {matches.map((match) => (
            <div
              key={match.match_id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card hover:shadow-card-hover transition flex flex-col justify-between"
            >
              <div>
                {/* Tournament & Status Badge */}
                <div className="flex items-center justify-between text-xs mb-3 pb-2.5 border-b border-slate-100 dark:border-slate-800">
                  <span className="font-semibold text-slate-500 text-[11px] truncate max-w-[180px]">
                    {match.tournament_name || 'Tournament Fixture'}
                  </span>
                  {match.status === 'live' ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-500 border border-rose-500/20 text-[10px] font-bold">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
                      LIVE
                    </span>
                  ) : match.status === 'completed' ? (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-[10px] border border-emerald-500/20">
                      COMPLETED
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold text-[10px]">
                      SCHEDULED
                    </span>
                  )}
                </div>

                {/* Team 1 vs Team 2 */}
                <div className="space-y-2 py-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      {match.team1_name}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">
                      {match.overs} Ov
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      {match.team2_name}
                    </span>
                  </div>
                </div>

                {/* Result or Status Summary */}
                {match.result_summary && (
                  <p className="mt-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 p-2 rounded-xl">
                    {match.result_summary}
                  </p>
                )}

                {/* Venue and Date */}
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1 truncate max-w-[150px]">
                    <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span>{match.venue_name || 'Standard Stadium'}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span>{new Date(match.match_date).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
                  </span>
                </div>
              </div>

              {/* Action Link */}
              <div className="mt-5">
                <Link
                  to={`/matches/${match.match_id}`}
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-emerald-500 dark:hover:bg-emerald-500 hover:text-white dark:hover:text-white text-slate-700 dark:text-slate-300 font-semibold text-xs transition"
                >
                  <span>{match.status === 'live' ? 'View Live Scorecard' : 'Match Details'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
