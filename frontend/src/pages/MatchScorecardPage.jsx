import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  Radio,
  RefreshCw,
  Trophy,
  Wifi,
  WifiOff,
} from 'lucide-react';
import useMatchSocket from '../hooks/useMatchSocket';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/UIFeedback';

export default function MatchScorecardPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'scorecard' | 'info'
  const [selectedInnings, setSelectedInnings] = useState(1);

  const { scorecard, liveData, isConnected, isPolling, loading, error, refresh } =
    useMatchSocket(id);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="h-8 w-40 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse" />
        <LoadingSkeleton rows={1} type="card" />
        <LoadingSkeleton rows={2} type="list" />
      </div>
    );
  }

  if (error || !scorecard) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          to="/live-scores"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-emerald-500 mb-4 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Live Scores</span>
        </Link>
        <ErrorState message={error || 'Match not found'} onRetry={refresh} />
      </div>
    );
  }

  // Derive live snapshot figures (prefer liveData over scorecard.live)
  const live = liveData || scorecard.live || {};
  const isMatchLive = scorecard.status === 'live';

  const team1Name = scorecard.team1?.name || 'Team 1';
  const team2Name = scorecard.team2?.name || 'Team 2';

  const scoreDisplay = `${live.score ?? 0}/${live.wickets ?? 0}`;
  const oversDisplay = live.overs ?? '0.0';
  const crrDisplay = live.run_rate ? Number(live.run_rate).toFixed(2) : '0.00';
  const rrrDisplay = live.required_rate ? Number(live.required_rate).toFixed(2) : null;
  const targetDisplay = live.target ?? null;

  const recentBalls = live.recent_balls || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumb & Status Connection Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            to="/live-scores"
            className="p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500">
                {scorecard.tournament_name || 'Premier Cricket League'}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs text-slate-500">{scorecard.overs} Overs Match</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white">
              {team1Name} vs {team2Name}
            </h1>
          </div>
        </div>

        {/* Real-time Connection Indicator & Refresh Button */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {isMatchLive && (
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border transition ${
                isConnected
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                  : isPolling
                  ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                  : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
              }`}
            >
              {isConnected ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-500" />
                  <span>WS Live</span>
                </>
              ) : isPolling ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-500" />
                  <span>Polling (5s)</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-rose-500" />
                  <span>Offline</span>
                </>
              )}
            </span>
          )}

          <button
            onClick={refresh}
            title="Manual refresh"
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Scoreboard Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              {scorecard.status === 'live' ? (
                <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 text-[10px] font-bold border border-rose-500/30">
                  <Radio className="w-3 h-3 animate-pulse" />
                  <span>LIVE MATCH</span>
                </span>
              ) : scorecard.status === 'completed' ? (
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold border border-emerald-500/30">
                  COMPLETED
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-bold">
                  SCHEDULED
                </span>
              )}
              <span className="text-xs text-slate-400">
                {scorecard.venue || 'Stadium'} • {new Date(scorecard.match_date).toLocaleDateString()}
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-black text-white">
              {team1Name} <span className="text-slate-500 font-normal">vs</span> {team2Name}
            </h2>

            {scorecard.result_summary ? (
              <p className="mt-2 text-sm font-bold text-emerald-400">{scorecard.result_summary}</p>
            ) : scorecard.toss_decision ? (
              <p className="mt-2 text-xs text-slate-400">
                Toss won by {scorecard.toss_winner_id === scorecard.team1?.id ? team1Name : team2Name}, elected to{' '}
                {scorecard.toss_decision} first
              </p>
            ) : null}
          </div>

          {/* Big Score Display */}
          <div className="text-left md:text-right">
            <div className="text-4xl sm:text-5xl font-black text-white tracking-tight">
              {scoreDisplay}
              <span className="text-lg sm:text-xl font-bold text-slate-400 ml-2">
                ({oversDisplay} Ov)
              </span>
            </div>
            <div className="flex items-center md:justify-end gap-3 mt-1.5 text-xs">
              <span className="font-semibold text-emerald-400">CRR: {crrDisplay}</span>
              {rrrDisplay && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="font-semibold text-amber-400">RRR: {rrrDisplay}</span>
                </>
              )}
              {targetDisplay && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="text-slate-400 font-medium">Target: {targetDisplay}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* This-Over Ball Ribbon */}
        {recentBalls.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <span className="text-xs font-semibold text-slate-400">Recent Deliveries:</span>
            <div className="flex items-center gap-1.5">
              {recentBalls.map((b, idx) => {
                let badgeColor = 'bg-slate-800 text-slate-300 border-slate-700';
                if (b === 'W') {
                  badgeColor = 'bg-rose-500 text-white border-rose-400 font-black animate-pulse';
                } else if (b === '4') {
                  badgeColor = 'bg-emerald-500 text-white border-emerald-400 font-black';
                } else if (b === '6') {
                  badgeColor = 'bg-purple-600 text-white border-purple-400 font-black';
                } else if (b === '0') {
                  badgeColor = 'bg-slate-800 text-slate-400 border-slate-700';
                } else if (b.includes('Wd') || b.includes('Nb')) {
                  badgeColor = 'bg-amber-500 text-white border-amber-400 font-bold';
                } else if (b !== '0') {
                  badgeColor = 'bg-teal-700 text-white border-teal-500 font-bold';
                }

                return (
                  <span
                    key={idx}
                    className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs border shadow-sm ${badgeColor}`}
                  >
                    {b}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Live Active Striker, Non-Striker & Bowler Strip */}
        {isMatchLive && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                Striker *
              </span>
              <p className="font-bold text-white text-sm mt-0.5 truncate">
                {live.striker_name || live.striker || 'On Strike'}
              </p>
            </div>
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Non-Striker
              </span>
              <p className="font-bold text-slate-200 text-sm mt-0.5 truncate">
                {live.non_striker_name || live.non_striker || 'Non-Striker'}
              </p>
            </div>
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">
                Current Bowler
              </span>
              <p className="font-bold text-slate-200 text-sm mt-0.5 truncate">
                {live.bowler_name || live.bowler || 'Current Bowler'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs: Live Summary vs Full Scorecard vs Match Info */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-4">
        <button
          onClick={() => setActiveTab('live')}
          className={`pb-3 px-2 text-xs sm:text-sm font-bold border-b-2 transition ${
            activeTab === 'live'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Live Summary
        </button>
        <button
          onClick={() => setActiveTab('scorecard')}
          className={`pb-3 px-2 text-xs sm:text-sm font-bold border-b-2 transition ${
            activeTab === 'scorecard'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Full Scorecard
        </button>
        <button
          onClick={() => setActiveTab('info')}
          className={`pb-3 px-2 text-xs sm:text-sm font-bold border-b-2 transition ${
            activeTab === 'info'
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Match Info
        </button>
      </div>

      {/* Tab 1: Live Summary Tables */}
      {activeTab === 'live' && (
        <div className="space-y-6">
          {scorecard.innings && scorecard.innings.length > 0 ? (
            scorecard.innings.map((inn) => (
              <div
                key={inn.innings_no}
                className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4"
              >
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                    {inn.batting_team} Innings{' '}
                    <span className="font-normal text-slate-500 text-xs">
                      ({inn.runs}/{inn.wickets} in {inn.overs} Ov)
                    </span>
                  </h3>
                  <span className="text-xs font-semibold text-emerald-500">
                    Innings {inn.innings_no}
                  </span>
                </div>

                {/* Batters Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                        <th className="py-2.5 px-3">Batter</th>
                        <th className="py-2.5 px-3">Dismissal</th>
                        <th className="py-2.5 px-3 text-right">R</th>
                        <th className="py-2.5 px-3 text-right">B</th>
                        <th className="py-2.5 px-3 text-right">4s</th>
                        <th className="py-2.5 px-3 text-right">6s</th>
                        <th className="py-2.5 px-3 text-right">SR</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {inn.batters && inn.batters.length > 0 ? (
                        inn.batters.map((b, i) => (
                          <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                              {b.name}
                            </td>
                            <td className="py-2.5 px-3 text-slate-500">{b.dismissal}</td>
                            <td className="py-2.5 px-3 text-right font-black text-slate-900 dark:text-white">
                              {b.runs}
                            </td>
                            <td className="py-2.5 px-3 text-right text-slate-500">{b.balls}</td>
                            <td className="py-2.5 px-3 text-right text-slate-500">{b.fours}</td>
                            <td className="py-2.5 px-3 text-right text-slate-500">{b.sixes}</td>
                            <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                              {b.strike_rate}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="py-4 text-center text-slate-400">
                            No batting events recorded yet
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Bowlers Table */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Bowling
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                          <th className="py-2 px-3">Bowler</th>
                          <th className="py-2 px-3 text-right">O</th>
                          <th className="py-2 px-3 text-right">M</th>
                          <th className="py-2 px-3 text-right">R</th>
                          <th className="py-2 px-3 text-right">W</th>
                          <th className="py-2 px-3 text-right">Econ</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {inn.bowlers && inn.bowlers.length > 0 ? (
                          inn.bowlers.map((bw, idx) => (
                            <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                              <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                                {bw.name}
                              </td>
                              <td className="py-2 px-3 text-right font-mono text-slate-700 dark:text-slate-300">
                                {bw.overs}
                              </td>
                              <td className="py-2 px-3 text-right text-slate-500">{bw.maidens}</td>
                              <td className="py-2 px-3 text-right font-bold text-slate-900 dark:text-white">
                                {bw.runs_conceded}
                              </td>
                              <td className="py-2 px-3 text-right font-black text-emerald-600 dark:text-emerald-400">
                                {bw.wickets}
                              </td>
                              <td className="py-2 px-3 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                                {bw.economy}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={6} className="py-3 text-center text-slate-400">
                              No bowler statistics recorded yet
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              title="No innings started yet"
              description="Match is scheduled or waiting for toss details to be recorded."
            />
          )}
        </div>
      )}

      {/* Tab 2: Full Scorecard */}
      {activeTab === 'scorecard' && (
        <div className="space-y-6">
          {scorecard.innings && scorecard.innings.length > 0 ? (
            <div>
              {/* Innings Selector Buttons */}
              <div className="flex gap-2 mb-4">
                {scorecard.innings.map((inn) => (
                  <button
                    key={inn.innings_no}
                    onClick={() => setSelectedInnings(inn.innings_no)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                      selectedInnings === inn.innings_no
                        ? 'bg-emerald-500 text-white shadow-sm'
                        : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    {inn.batting_team} Innings
                  </button>
                ))}
              </div>

              {scorecard.innings
                .filter((inn) => inn.innings_no === selectedInnings)
                .map((inn) => (
                  <div
                    key={inn.innings_no}
                    className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-6"
                  >
                    <div>
                      <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                        {inn.batting_team} Batting Scorecard
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Total: {inn.runs}/{inn.wickets} ({inn.overs} Overs)
                      </p>
                    </div>

                    {/* Batters */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                            <th className="py-2.5 px-3">Batter</th>
                            <th className="py-2.5 px-3">Dismissal</th>
                            <th className="py-2.5 px-3 text-right">R</th>
                            <th className="py-2.5 px-3 text-right">B</th>
                            <th className="py-2.5 px-3 text-right">4s</th>
                            <th className="py-2.5 px-3 text-right">6s</th>
                            <th className="py-2.5 px-3 text-right">SR</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {inn.batters?.map((b, i) => (
                            <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                              <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                                {b.name}
                              </td>
                              <td className="py-2.5 px-3 text-slate-500">{b.dismissal}</td>
                              <td className="py-2.5 px-3 text-right font-black text-slate-900 dark:text-white">
                                {b.runs}
                              </td>
                              <td className="py-2.5 px-3 text-right text-slate-500">{b.balls}</td>
                              <td className="py-2.5 px-3 text-right text-slate-500">{b.fours}</td>
                              <td className="py-2.5 px-3 text-right text-slate-500">{b.sixes}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                                {b.strike_rate}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Extras */}
                    {inn.extras && (
                      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          Extras: {inn.extras.total}
                        </span>
                        <span className="text-slate-500">
                          (b {inn.extras.byes}, lb {inn.extras.leg_byes}, w {inn.extras.wides}, nb{' '}
                          {inn.extras.no_balls})
                        </span>
                      </div>
                    )}

                    {/* Fall of Wickets */}
                    {inn.fall_of_wickets && inn.fall_of_wickets.length > 0 && (
                      <div className="pt-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                          Fall of Wickets
                        </h4>
                        <div className="flex flex-wrap gap-2 text-xs">
                          {inn.fall_of_wickets.map((fw, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                            >
                              <strong>
                                {fw.score}/{fw.wicket_number}
                              </strong>{' '}
                              ({fw.player_name}, {fw.overs} ov)
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Bowlers Table */}
                    <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                        Bowling Figures
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                              <th className="py-2 px-3">Bowler</th>
                              <th className="py-2 px-3 text-right">O</th>
                              <th className="py-2 px-3 text-right">M</th>
                              <th className="py-2 px-3 text-right">R</th>
                              <th className="py-2 px-3 text-right">W</th>
                              <th className="py-2 px-3 text-right">Econ</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {inn.bowlers?.map((bw, idx) => (
                              <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                                <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                                  {bw.name}
                                </td>
                                <td className="py-2 px-3 text-right font-mono text-slate-700 dark:text-slate-300">
                                  {bw.overs}
                                </td>
                                <td className="py-2 px-3 text-right text-slate-500">{bw.maidens}</td>
                                <td className="py-2 px-3 text-right font-bold text-slate-900 dark:text-white">
                                  {bw.runs_conceded}
                                </td>
                                <td className="py-2 px-3 text-right font-black text-emerald-600 dark:text-emerald-400">
                                  {bw.wickets}
                                </td>
                                <td className="py-2 px-3 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                                  {bw.economy}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <EmptyState title="No innings recorded yet" />
          )}
        </div>
      )}

      {/* Tab 3: Match Info */}
      {activeTab === 'info' && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4 text-xs">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Match Details</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Tournament</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {scorecard.tournament_name || 'Standard League'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Venue</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {scorecard.venue || 'Stadium'}, {scorecard.city || 'India'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Match Date</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {new Date(scorecard.match_date).toLocaleString()}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Format</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {scorecard.overs} Overs per side
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
