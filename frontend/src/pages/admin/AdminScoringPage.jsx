import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  PlayCircle,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Radio,
  UserCheck,
  Shield,
  Layers,
  ChevronRight,
  ArrowRightLeft,
  X,
  Plus,
  Clock,
  MapPin,
  Trophy,
  Award,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { matchesService, scoringService, playersService } from '../../services/api';
import { LoadingSkeleton, EmptyState } from '../../components/UIFeedback';

export default function AdminScoringPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlMatchId = searchParams.get('matchId');

  // Match and Rosters state
  const [matches, setMatches] = useState([]);
  const [selectedMatchId, setSelectedMatchId] = useState(urlMatchId || '');
  const [matchDetails, setMatchDetails] = useState(null);
  const [team1Players, setTeam1Players] = useState([]);
  const [team2Players, setTeam2Players] = useState([]);
  const [playerMap, setPlayerMap] = useState({});

  // Live scoring state
  const [scoringState, setScoringState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Setup Wizard State
  const [tossWinnerId, setTossWinnerId] = useState('');
  const [tossDecision, setTossDecision] = useState('bat');
  const [team1Xi, setTeam1Xi] = useState([]);
  const [team2Xi, setTeam2Xi] = useState([]);
  const [strikerId, setStrikerId] = useState('');
  const [nonStrikerId, setNonStrikerId] = useState('');
  const [openingBowlerId, setOpeningBowlerId] = useState('');

  // Active delivery configuration (strike rotation, active bowler)
  const [activeStrikerId, setActiveStrikerId] = useState('');
  const [activeNonStrikerId, setActiveNonStrikerId] = useState('');
  const [activeBowlerId, setActiveBowlerId] = useState('');

  // Modals state
  const [isWicketModalOpen, setIsWicketModalOpen] = useState(false);
  const [wicketType, setWicketType] = useState('bowled');
  const [dismissedBatterId, setDismissedBatterId] = useState('');
  const [nextBatterId, setNextBatterId] = useState('');

  const [isExtrasModalOpen, setIsExtrasModalOpen] = useState(false);
  const [selectedExtrasType, setSelectedExtrasType] = useState('wide'); // wide, no_ball, bye, leg_bye
  const [extrasExtraRuns, setExtrasExtraRuns] = useState(0);

  const [isBowlerModalOpen, setIsBowlerModalOpen] = useState(false);
  const [selectedNextBowlerId, setSelectedNextBowlerId] = useState('');

  // Fetch matches list
  const fetchMatchesList = async () => {
    try {
      const data = await matchesService.list({ page_size: 50 });
      setMatches(data.items || []);
      if (!selectedMatchId && data.items?.length > 0) {
        // Prefer LIVE or SCHEDULED match
        const active = data.items.find((m) => m.status === 'LIVE' || m.status === 'SCHEDULED');
        const idToSelect = active ? active.match_id : data.items[0].match_id;
        setSelectedMatchId(idToSelect);
      }
    } catch (err) {
      toast.error('Failed to load matches list');
    }
  };

  useEffect(() => {
    fetchMatchesList();
  }, []);

  // Sync url param
  useEffect(() => {
    if (urlMatchId && urlMatchId !== selectedMatchId) {
      setSelectedMatchId(urlMatchId);
    }
  }, [urlMatchId]);

  // When selectedMatchId changes, load match details, rosters & scoring state
  const loadMatchData = useCallback(async (matchId) => {
    if (!matchId) return;
    setLoading(true);
    try {
      const [mRes, scRes] = await Promise.all([
        matchesService.getById(matchId),
        matchesService.getScorecard(matchId).catch(() => null),
      ]);
      setMatchDetails(mRes);

      // Load rosters for both teams
      const [t1Roster, t2Roster] = await Promise.all([
        playersService.list({ team_id: mRes.team1_id, page_size: 50 }),
        playersService.list({ team_id: mRes.team2_id, page_size: 50 }),
      ]);

      const t1List = t1Roster.items || [];
      const t2List = t2Roster.items || [];
      setTeam1Players(t1List);
      setTeam2Players(t2List);

      // Build player map
      const map = {};
      t1List.forEach((p) => {
        map[p.player_id] = p.name;
      });
      t2List.forEach((p) => {
        map[p.player_id] = p.name;
      });
      setPlayerMap(map);

      // Default setup wizard values
      setTossWinnerId(mRes.team1_id);
      setTossDecision('bat');
      setTeam1Xi(t1List.slice(0, 11).map((p) => p.player_id));
      setTeam2Xi(t2List.slice(0, 11).map((p) => p.player_id));
      if (t1List.length >= 2) {
        setStrikerId(t1List[0].player_id);
        setNonStrikerId(t1List[1].player_id);
      }
      if (t2List.length >= 1) {
        setOpeningBowlerId(t2List[0].player_id);
      }

      // If match is LIVE or INNINGS_BREAK, load active state
      if (mRes.status === 'LIVE' || mRes.status === 'INNINGS_BREAK' || mRes.status === 'COMPLETED') {
        const liveRes = await matchesService.getLiveState(matchId).catch(() => null);
        if (liveRes && scRes) {
          // Reconstruct state
          const activeInnings = scRes.innings?.[scRes.innings.length - 1];
          const st = {
            match_id: matchId,
            match_status: mRes.status,
            innings_no: activeInnings?.innings_no || 1,
            batting_team_id: activeInnings?.batting_team === mRes.team1_name ? mRes.team1_id : mRes.team2_id,
            bowling_team_id: activeInnings?.batting_team === mRes.team1_name ? mRes.team2_id : mRes.team1_id,
            total_runs: liveRes.score || 0,
            wickets: liveRes.wickets || 0,
            legal_balls: activeInnings?.runs !== undefined ? Math.round(parseFloat(liveRes.overs || '0') * 6) : 0,
            overs_formatted: liveRes.overs || '0.0',
            striker_id: liveRes.striker || '',
            non_striker_id: liveRes.non_striker || '',
            current_bowler_id: liveRes.bowler || '',
            current_run_rate: liveRes.run_rate || 0,
            required_run_rate: liveRes.required_rate || null,
            recent_balls: liveRes.recent_balls || [],
            is_completed: mRes.status === 'COMPLETED',
            target_runs: liveRes.target || null,
            result_summary: mRes.result_summary || null,
            batters: {},
            bowlers: {},
          };

          // Populate batters and bowlers dicts from scorecard
          if (activeInnings?.batters) {
            activeInnings.batters.forEach((b) => {
              st.batters[b.player_id] = b;
            });
          }
          if (activeInnings?.bowlers) {
            activeInnings.bowlers.forEach((bw) => {
              st.bowlers[bw.player_id] = bw;
            });
          }

          setScoringState(st);
          setActiveStrikerId(st.striker_id);
          setActiveNonStrikerId(st.non_striker_id);
          setActiveBowlerId(st.current_bowler_id);
        }
      } else {
        setScoringState(null);
      }
    } catch (err) {
      toast.error('Failed to load match scoring data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedMatchId) {
      loadMatchData(selectedMatchId);
    }
  }, [selectedMatchId, loadMatchData]);

  // Determine Batting and Bowling XI for active innings
  const { battingXi, bowlingXi, battingTeamName, bowlingTeamName } = useMemo(() => {
    if (!matchDetails) {
      return { battingXi: [], bowlingXi: [], battingTeamName: '', bowlingTeamName: '' };
    }

    let isTeam1Batting = true;
    if (scoringState) {
      isTeam1Batting = scoringState.batting_team_id === matchDetails.team1_id;
    } else {
      // In setup wizard
      if (tossWinnerId === matchDetails.team1_id) {
        isTeam1Batting = tossDecision === 'bat';
      } else {
        isTeam1Batting = tossDecision !== 'bat';
      }
    }

    const batXi = isTeam1Batting ? team1Xi : team2Xi;
    const bowlXi = isTeam1Batting ? team2Xi : team1Xi;
    const batName = isTeam1Batting ? matchDetails.team1_name : matchDetails.team2_name;
    const bowlName = isTeam1Batting ? matchDetails.team2_name : matchDetails.team1_name;

    return { battingXi: batXi, bowlingXi: bowlXi, battingTeamName: batName, bowlingTeamName: bowlName };
  }, [matchDetails, scoringState, tossWinnerId, tossDecision, team1Xi, team2Xi]);

  // Update active positions when scoringState arrives from server
  const applyServerScoringState = (res) => {
    setScoringState(res);
    setActiveStrikerId(res.striker_id);
    setActiveNonStrikerId(res.non_striker_id);
    setActiveBowlerId(res.current_bowler_id || activeBowlerId);

    // Auto-trigger bowler change modal after 6th legal ball of over
    if (res.legal_balls > 0 && res.legal_balls % 6 === 0 && !res.is_completed) {
      setIsBowlerModalOpen(true);
    }
  };

  // -------------------------------------------------------------
  // MATCH SETUP WIZARD ACTIONS
  // -------------------------------------------------------------
  const handleStartMatch = async () => {
    if (team1Xi.length < 2 || team2Xi.length < 2) {
      toast.error('Please select at least 2 players in each playing XI');
      return;
    }
    if (!strikerId || !nonStrikerId || !openingBowlerId) {
      toast.error('Please assign opening striker, non-striker, and opening bowler');
      return;
    }
    if (strikerId === nonStrikerId) {
      toast.error('Striker and non-striker must be different players');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        toss_winner_id: tossWinnerId,
        toss_decision: tossDecision,
        team1_xi: team1Xi,
        team2_xi: team2Xi,
        striker_id: strikerId,
        non_striker_id: nonStrikerId,
        opening_bowler_id: openingBowlerId,
      };

      const res = await scoringService.startMatch(selectedMatchId, payload);
      toast.success('Match started! Ready for delivery 0.1');
      applyServerScoringState(res);
      setMatchDetails((prev) => ({ ...prev, status: 'LIVE' }));
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start match';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // -------------------------------------------------------------
  // SCORING CONSOLE ACTIONS
  // -------------------------------------------------------------

  // Record a standard run delivery (0-6)
  const handleRecordRuns = async (runs) => {
    if (isSubmitting || !scoringState || scoringState.is_completed) return;
    if (!activeStrikerId || !activeNonStrikerId || !activeBowlerId) {
      toast.error('Please verify active striker, non-striker, and bowler');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        striker_id: activeStrikerId,
        non_striker_id: activeNonStrikerId,
        bowler_id: activeBowlerId,
        runs_batter: runs,
        extras_type: null,
        extras_runs: 0,
        is_wicket: false,
      };

      const res = await scoringService.recordBall(selectedMatchId, payload);
      applyServerScoringState(res);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to record ball';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Extras Picker
  const handleOpenExtras = (type) => {
    setSelectedExtrasType(type);
    setExtrasExtraRuns(0);
    setIsExtrasModalOpen(true);
  };

  // Submit Extras
  const handleSubmitExtras = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);

    try {
      let extrasRuns = 0;
      let runsBatter = 0;

      if (selectedExtrasType === 'wide') {
        // 1 penalty run for wide + any runs taken
        extrasRuns = 1 + Number(extrasExtraRuns);
        runsBatter = 0;
      } else if (selectedExtrasType === 'no_ball') {
        // 1 penalty run + runs off bat
        extrasRuns = 1;
        runsBatter = Number(extrasExtraRuns);
      } else if (selectedExtrasType === 'bye' || selectedExtrasType === 'leg_bye') {
        extrasRuns = Number(extrasExtraRuns) || 1;
        runsBatter = 0;
      }

      const payload = {
        striker_id: activeStrikerId,
        non_striker_id: activeNonStrikerId,
        bowler_id: activeBowlerId,
        runs_batter: runsBatter,
        extras_type: selectedExtrasType,
        extras_runs: extrasRuns,
        is_wicket: false,
      };

      const res = await scoringService.recordBall(selectedMatchId, payload);
      applyServerScoringState(res);
      setIsExtrasModalOpen(false);
      toast.success(`Recorded ${selectedExtrasType.replace('_', ' ').toUpperCase()} (+${extrasRuns + runsBatter})`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to record extras';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Wicket Modal
  const handleOpenWicket = () => {
    setDismissedBatterId(activeStrikerId);
    setWicketType('bowled');

    // Pick first available batter not currently batting and not out
    const dismissedSet = new Set(
      Object.keys(scoringState?.batters || {}).filter((k) => scoringState.batters[k].is_out)
    );
    dismissedSet.add(activeStrikerId);
    dismissedSet.add(activeNonStrikerId);

    const available = battingXi.find((pId) => !dismissedSet.has(pId));
    setNextBatterId(available || '');
    setIsWicketModalOpen(true);
  };

  // Submit Wicket
  const handleSubmitWicket = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);

    try {
      const payload = {
        striker_id: activeStrikerId,
        non_striker_id: activeNonStrikerId,
        bowler_id: activeBowlerId,
        runs_batter: 0,
        extras_type: null,
        extras_runs: 0,
        is_wicket: true,
        wicket_type: wicketType,
        dismissed_player_id: dismissedBatterId || activeStrikerId,
        next_batter_id: nextBatterId || null,
      };

      const res = await scoringService.recordBall(selectedMatchId, payload);
      applyServerScoringState(res);
      setIsWicketModalOpen(false);
      toast.success(`Wicket recorded: ${playerMap[payload.dismissed_player_id] || 'Batter'} (${wicketType})`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to record wicket';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Rotate Strike manually
  const handleRotateStrike = () => {
    const temp = activeStrikerId;
    setActiveStrikerId(activeNonStrikerId);
    setActiveNonStrikerId(temp);
    toast.success('Strike rotated manually');
  };

  // Undo Last Ball
  const handleUndo = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);
    try {
      const res = await scoringService.undoBall(selectedMatchId);
      applyServerScoringState(res);
      toast.success('Undid last delivery successfully');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to undo delivery';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Change Bowler
  const handleChangeBowler = (bowlerId) => {
    setActiveBowlerId(bowlerId);
    setIsBowlerModalOpen(false);
    toast.success(`Bowler changed to ${playerMap[bowlerId] || 'Bowler'}`);
  };

  // End Innings (for Innings 1)
  const handleEndInnings = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);
    try {
      const res = await scoringService.endInnings(selectedMatchId);
      applyServerScoringState(res);
      setMatchDetails((prev) => ({ ...prev, status: 'INNINGS_BREAK' }));
      toast.success(`Innings 1 concluded! Target set to ${res.target_runs} runs.`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to conclude innings';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Resume Match (Start Innings 2)
  const handleResumeMatch = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);
    try {
      const res = await scoringService.resumeMatch(selectedMatchId);
      applyServerScoringState(res);
      setMatchDetails((prev) => ({ ...prev, status: 'LIVE' }));
      toast.success('Innings 2 started! Chase is on.');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start Innings 2';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Complete Match
  const handleCompleteMatch = async () => {
    if (isSubmitting || !scoringState) return;
    setIsSubmitting(true);
    try {
      const res = await scoringService.completeMatch(selectedMatchId);
      applyServerScoringState(res);
      setMatchDetails((prev) => ({
        ...prev,
        status: 'COMPLETED',
        result_summary: res.result_summary,
      }));
      toast.success('Match completed officially!');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to complete match';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // -------------------------------------------------------------
  // DESKTOP KEYBOARD SHORTCUTS
  // -------------------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input, textarea or select
      const tag = e.target.tagName.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (isWicketModalOpen || isExtrasModalOpen || isBowlerModalOpen) return;
      if (!scoringState || matchDetails?.status !== 'LIVE' || isSubmitting) return;

      if (['0', '1', '2', '3', '4', '5', '6'].includes(e.key)) {
        e.preventDefault();
        handleRecordRuns(parseInt(e.key, 10));
      } else if (e.key === 'w' || e.key === 'W') {
        e.preventDefault();
        handleOpenWicket();
      } else if (e.key === 'u' || e.key === 'U') {
        e.preventDefault();
        handleUndo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    scoringState,
    matchDetails,
    isSubmitting,
    isWicketModalOpen,
    isExtrasModalOpen,
    isBowlerModalOpen,
    activeStrikerId,
    activeNonStrikerId,
    activeBowlerId,
  ]);

  if (loading && !matchDetails) {
    return <LoadingSkeleton rows={4} type="card" />;
  }

  const isLive = matchDetails?.status === 'LIVE';
  const isScheduled = matchDetails?.status === 'SCHEDULED';
  const isInningsBreak = matchDetails?.status === 'INNINGS_BREAK';
  const isCompleted = matchDetails?.status === 'COMPLETED';

  // Active batter stats
  const strikerStats = scoringState?.batters?.[activeStrikerId] || {
    runs: 0,
    balls: 0,
    fours: 0,
    sixes: 0,
  };
  const nonStrikerStats = scoringState?.batters?.[activeNonStrikerId] || {
    runs: 0,
    balls: 0,
    fours: 0,
    sixes: 0,
  };
  const bowlerStats = scoringState?.bowlers?.[activeBowlerId] || {
    overs: '0.0',
    runs: 0,
    wickets: 0,
    dots: 0,
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Match Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-emerald-500" />
            <span>Match Scorer Console</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time ball-by-ball recording with pure domain engine & deterministic undo
          </p>
        </div>

        {/* Match Selector Dropdown */}
        <div className="flex items-center gap-3">
          <select
            value={selectedMatchId}
            onChange={(e) => {
              setSelectedMatchId(e.target.value);
              setSearchParams({ matchId: e.target.value });
            }}
            className="px-3 py-2 text-xs font-semibold rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 shadow-sm"
          >
            {matches.map((m) => (
              <option key={m.match_id} value={m.match_id}>
                {m.team1_name} vs {m.team2_name} ({m.status})
              </option>
            ))}
          </select>

          {matchDetails && (
            <Link
              to={`/match/${matchDetails.match_id}`}
              target="_blank"
              className="inline-flex items-center gap-1 px-3 py-2 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 shadow-sm transition"
              title="Open Live Public Scorecard"
            >
              <span>Public View</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* STATE 1: MATCH SETUP WIZARD (FOR SCHEDULED MATCHES)           */}
      {/* ------------------------------------------------------------- */}
      {isScheduled && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">
                Pre-Match Preparation
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                Match Setup Wizard: {matchDetails.team1_name} vs {matchDetails.team2_name}
              </h3>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
              SETUP REQUIRED
            </span>
          </div>

          {/* Step 1: Toss */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
              <Trophy className="w-4 h-4 text-emerald-500" />
              <span>Step 1: Official Toss & Decision</span>
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Toss Winner
                </label>
                <select
                  value={tossWinnerId}
                  onChange={(e) => setTossWinnerId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value={matchDetails.team1_id}>{matchDetails.team1_name} (Home)</option>
                  <option value={matchDetails.team2_id}>{matchDetails.team2_name} (Away)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Elected To
                </label>
                <div className="flex items-center gap-3 mt-1">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      value="bat"
                      checked={tossDecision === 'bat'}
                      onChange={() => setTossDecision('bat')}
                      className="text-emerald-500 focus:ring-emerald-500"
                    />
                    <span>Bat First</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      value="bowl"
                      checked={tossDecision === 'bowl'}
                      onChange={() => setTossDecision('bowl')}
                      className="text-emerald-500 focus:ring-emerald-500"
                    />
                    <span>Bowl First</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Playing XIs */}
          <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-emerald-500" />
              <span>Step 2: Confirm Playing XIs</span>
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Team 1 XI */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {matchDetails.team1_name} XI ({team1Xi.length} selected)
                  </span>
                  <button
                    onClick={() => setTeam1Xi(team1Players.slice(0, 11).map((p) => p.player_id))}
                    className="text-[11px] font-semibold text-emerald-500 hover:text-emerald-600"
                  >
                    Select First 11
                  </button>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                  {team1Players.map((p) => {
                    const checked = team1Xi.includes(p.player_id);
                    return (
                      <label
                        key={p.player_id}
                        className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-xs cursor-pointer"
                      >
                        <span className="font-medium text-slate-800 dark:text-slate-200">{p.name}</span>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) setTeam1Xi([...team1Xi, p.player_id]);
                            else setTeam1Xi(team1Xi.filter((id) => id !== p.player_id));
                          }}
                          className="rounded text-emerald-500 focus:ring-emerald-500"
                        />
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Team 2 XI */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {matchDetails.team2_name} XI ({team2Xi.length} selected)
                  </span>
                  <button
                    onClick={() => setTeam2Xi(team2Players.slice(0, 11).map((p) => p.player_id))}
                    className="text-[11px] font-semibold text-emerald-500 hover:text-emerald-600"
                  >
                    Select First 11
                  </button>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                  {team2Players.map((p) => {
                    const checked = team2Xi.includes(p.player_id);
                    return (
                      <label
                        key={p.player_id}
                        className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-xs cursor-pointer"
                      >
                        <span className="font-medium text-slate-800 dark:text-slate-200">{p.name}</span>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) setTeam2Xi([...team2Xi, p.player_id]);
                            else setTeam2Xi(team2Xi.filter((id) => id !== p.player_id));
                          }}
                          className="rounded text-emerald-500 focus:ring-emerald-500"
                        />
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Openers & Bowler */}
          <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-emerald-500" />
              <span>Step 3: Opening Batters & Bowler</span>
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Opening Striker ({battingTeamName})
                </label>
                <select
                  value={strikerId}
                  onChange={(e) => setStrikerId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {battingXi.map((pId) => (
                    <option key={pId} value={pId}>
                      {playerMap[pId] || pId}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Opening Non-Striker ({battingTeamName})
                </label>
                <select
                  value={nonStrikerId}
                  onChange={(e) => setNonStrikerId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {battingXi.map((pId) => (
                    <option key={pId} value={pId}>
                      {playerMap[pId] || pId}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Opening Bowler ({bowlingTeamName})
                </label>
                <select
                  value={openingBowlerId}
                  onChange={(e) => setOpeningBowlerId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                >
                  {bowlingXi.map((pId) => (
                    <option key={pId} value={pId}>
                      {playerMap[pId] || pId}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Action button */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
            <button
              onClick={handleStartMatch}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold text-xs shadow-md transition"
            >
              <PlayCircle className="w-4 h-4" />
              <span>{isSubmitting ? 'Starting Match...' : 'Confirm Toss & Start Match'}</span>
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* STATE 2 & 3: LIVE CONSOLE / INNINGS BREAK / COMPLETED MATCH   */}
      {/* ------------------------------------------------------------- */}
      {!isScheduled && scoringState && (
        <>
          {/* Main Scoreboard Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-850 to-slate-900 text-white shadow-card border border-slate-700/60">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400">
                    {scoringState.innings_no === 1 ? '1st Innings' : '2nd Innings (Chase)'}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      isLive
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
                        : isInningsBreak
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-emerald-500/20 text-emerald-300'
                    }`}
                  >
                    {matchDetails.status}
                  </span>
                </div>
                <h3 className="text-2xl font-black mt-1">
                  {battingTeamName}{' '}
                  <span className="text-sm font-normal text-slate-400">vs {bowlingTeamName}</span>
                </h3>
              </div>

              <div className="text-right">
                <div className="text-3xl font-black tracking-tight text-white">
                  {scoringState.total_runs}/{scoringState.wickets}
                  <span className="text-base font-semibold text-slate-400 ml-2">
                    ({scoringState.overs_formatted} Ov)
                  </span>
                </div>
                <p className="text-xs text-emerald-400 font-medium mt-0.5">
                  CRR: {scoringState.current_run_rate}
                  {scoringState.target_runs && (
                    <span className="ml-2 text-slate-300">
                      • Target: {scoringState.target_runs} (RRR: {scoringState.required_run_rate || '—'})
                    </span>
                  )}
                </p>
              </div>
            </div>

            {/* Striker / Non-Striker / Bowler Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 text-xs">
              {/* Striker */}
              <div className="p-3.5 rounded-xl bg-slate-800/90 border border-emerald-500/40 relative shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider flex items-center gap-1">
                    <span>On Strike</span>
                    <span className="text-emerald-400 font-bold">*</span>
                  </span>
                  <span className="text-[11px] font-semibold text-slate-300">
                    SR:{' '}
                    {strikerStats.balls > 0
                      ? Math.round((strikerStats.runs / strikerStats.balls) * 100)
                      : '0'}
                  </span>
                </div>
                <p className="font-bold text-white text-sm mt-1">
                  {playerMap[activeStrikerId] || 'Striker'}
                </p>
                <p className="text-xs text-emerald-300 font-semibold mt-0.5">
                  {strikerStats.runs} <span className="font-normal text-slate-400">({strikerStats.balls}b)</span> •{' '}
                  {strikerStats.fours} 4s • {strikerStats.sixes} 6s
                </p>
              </div>

              {/* Non-Striker */}
              <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">
                    Non-Striker
                  </span>
                  <span className="text-[11px] font-semibold text-slate-400">
                    SR:{' '}
                    {nonStrikerStats.balls > 0
                      ? Math.round((nonStrikerStats.runs / nonStrikerStats.balls) * 100)
                      : '0'}
                  </span>
                </div>
                <p className="font-bold text-white text-sm mt-1">
                  {playerMap[activeNonStrikerId] || 'Non-Striker'}
                </p>
                <p className="text-xs text-slate-300 font-semibold mt-0.5">
                  {nonStrikerStats.runs} <span className="font-normal text-slate-400">({nonStrikerStats.balls}b)</span> •{' '}
                  {nonStrikerStats.fours} 4s • {nonStrikerStats.sixes} 6s
                </p>
              </div>

              {/* Bowler */}
              <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">
                    Current Bowler
                  </span>
                  <button
                    onClick={() => setIsBowlerModalOpen(true)}
                    className="text-[10px] text-emerald-400 hover:text-emerald-300 font-bold"
                  >
                    Change
                  </button>
                </div>
                <p className="font-bold text-white text-sm mt-1">
                  {playerMap[activeBowlerId] || 'Bowler'}
                </p>
                <p className="text-xs text-slate-300 font-semibold mt-0.5">
                  {bowlerStats.overs} Ov • {bowlerStats.runs} Runs •{' '}
                  <span className="text-emerald-400 font-bold">{bowlerStats.wickets} Wkts</span>
                </p>
              </div>
            </div>

            {/* Recent Balls Strip */}
            <div className="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between overflow-x-auto">
              <span className="text-xs text-slate-400 font-medium whitespace-nowrap mr-3">
                Recent Deliveries:
              </span>
              <div className="flex items-center gap-1.5">
                {scoringState.recent_balls.length === 0 ? (
                  <span className="text-xs text-slate-500 italic">No deliveries recorded in this innings yet</span>
                ) : (
                  scoringState.recent_balls.map((b, idx) => (
                    <span
                      key={idx}
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        b === 'W'
                          ? 'bg-rose-500 text-white animate-pulse'
                          : b === '4' || b === '6'
                          ? 'bg-emerald-500 text-white'
                          : b.startsWith('Wd') || b.startsWith('Nb')
                          ? 'bg-amber-500 text-white text-[10px]'
                          : 'bg-slate-700 text-slate-200'
                      }`}
                    >
                      {b}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Innings Break Notification Bar */}
          {isInningsBreak && (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-500 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="font-bold text-sm">Innings Break</p>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                  1st Innings concluded. Target for {bowlingTeamName} is{' '}
                  <span className="font-bold underline">{scoringState.target_runs} runs</span>.
                </p>
              </div>
              <button
                onClick={handleResumeMatch}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-sm transition"
              >
                Start Innings 2 Chase
              </button>
            </div>
          )}

          {/* Completed Match Result Bar */}
          {isCompleted && (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="font-bold text-sm">Match Completed Officially</p>
                <p className="text-xs mt-0.5 font-medium">{scoringState.result_summary || 'Result Finalized'}</p>
              </div>
              <Link
                to={`/match/${matchDetails.match_id}`}
                target="_blank"
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-sm transition"
              >
                View Full Final Scorecard
              </Link>
            </div>
          )}

          {/* ------------------------------------------------------------- */}
          {/* SCORING CONTROL CONSOLE (DISABLED IF COMPLETED / BREAK)       */}
          {/* ------------------------------------------------------------- */}
          {isLive && (
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-6">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">
                  Live Control Pad (Desktop Shortcuts: 0-6, W, U)
                </h4>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRotateStrike}
                    disabled={isSubmitting}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition"
                  >
                    <ArrowRightLeft className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Rotate Strike</span>
                  </button>
                  <button
                    onClick={handleUndo}
                    disabled={isSubmitting || scoringState.total_runs === 0 && scoringState.legal_balls === 0}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-900/50 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-xs font-semibold text-rose-600 dark:text-rose-400 transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Undo Delivery (U)</span>
                  </button>
                </div>
              </div>

              {/* Large Touch Target Runs Pad */}
              <div>
                <span className="block text-[11px] font-semibold text-slate-500 mb-2">Runs Off Bat</span>
                <div className="grid grid-cols-4 sm:grid-cols-7 gap-2.5">
                  {[0, 1, 2, 3, 4, 5, 6].map((run) => (
                    <button
                      key={run}
                      onClick={() => handleRecordRuns(run)}
                      disabled={isSubmitting}
                      className="h-16 rounded-2xl border-2 border-slate-200 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 bg-slate-50 dark:bg-slate-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 text-xl font-black text-slate-900 dark:text-white transition flex flex-col items-center justify-center disabled:opacity-50 active:scale-95 shadow-sm"
                    >
                      <span>{run}</span>
                      <span className="text-[10px] font-normal text-slate-400">
                        {run === 0 ? 'Dot' : run === 4 ? 'FOUR' : run === 6 ? 'SIX' : 'Run'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Extras & Wicket Pad */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
                <button
                  onClick={() => handleOpenExtras('wide')}
                  disabled={isSubmitting}
                  className="h-14 rounded-xl border border-amber-300 dark:border-amber-800/80 bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-700 dark:text-amber-300 font-bold text-xs flex flex-col items-center justify-center transition disabled:opacity-50 shadow-sm"
                >
                  <span className="text-sm font-black">Wide (Wd)</span>
                  <span className="text-[10px] font-medium opacity-80">+1 & Extras</span>
                </button>

                <button
                  onClick={() => handleOpenExtras('no_ball')}
                  disabled={isSubmitting}
                  className="h-14 rounded-xl border border-amber-300 dark:border-amber-800/80 bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-700 dark:text-amber-300 font-bold text-xs flex flex-col items-center justify-center transition disabled:opacity-50 shadow-sm"
                >
                  <span className="text-sm font-black">No Ball (Nb)</span>
                  <span className="text-[10px] font-medium opacity-80">+1 & Bat Runs</span>
                </button>

                <button
                  onClick={() => handleOpenExtras('bye')}
                  disabled={isSubmitting}
                  className="h-14 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs flex flex-col items-center justify-center transition disabled:opacity-50 shadow-sm"
                >
                  <span className="text-sm font-black">Bye (B)</span>
                  <span className="text-[10px] font-medium opacity-80">Extras Run</span>
                </button>

                <button
                  onClick={() => handleOpenExtras('leg_bye')}
                  disabled={isSubmitting}
                  className="h-14 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs flex flex-col items-center justify-center transition disabled:opacity-50 shadow-sm"
                >
                  <span className="text-sm font-black">Leg Bye (Lb)</span>
                  <span className="text-[10px] font-medium opacity-80">Extras Run</span>
                </button>

                <button
                  onClick={handleOpenWicket}
                  disabled={isSubmitting}
                  className="col-span-2 sm:col-span-1 h-14 rounded-xl bg-rose-500 hover:bg-rose-600 text-white font-bold text-xs flex flex-col items-center justify-center transition disabled:opacity-50 shadow-md active:scale-95"
                >
                  <span className="text-base font-black">WICKET (W)</span>
                  <span className="text-[10px] font-medium opacity-90">Out & Next Batter</span>
                </button>
              </div>

              {/* Innings Management Actions */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <button
                  onClick={() => setIsBowlerModalOpen(true)}
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                >
                  End Over / Pick Bowler
                </button>

                <div className="flex items-center gap-2">
                  {scoringState.innings_no === 1 ? (
                    <button
                      onClick={handleEndInnings}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded-xl bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-bold transition shadow-sm"
                    >
                      End Innings 1
                    </button>
                  ) : (
                    <button
                      onClick={handleCompleteMatch}
                      disabled={isSubmitting}
                      className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold transition shadow-sm"
                    >
                      Declare Official Result
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 1: EXTRAS PICKER ("RUNS ALSO SCORED?")                   */}
      {/* ------------------------------------------------------------- */}
      {isExtrasModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white capitalize">
                {selectedExtrasType.replace('_', ' ')}: Runs Also Scored?
              </h3>
              <button
                onClick={() => setIsExtrasModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              {selectedExtrasType === 'wide'
                ? 'Wide incurs 1 penalty run. Select any additional runs completed by batters or overthrows:'
                : selectedExtrasType === 'no_ball'
                ? 'No-ball incurs 1 penalty run. Select runs hit off the bat:'
                : 'Select total byes/leg-byes taken:'}
            </p>

            <div className="grid grid-cols-5 gap-2">
              {[0, 1, 2, 3, 4].map((r) => (
                <button
                  key={r}
                  onClick={() => setExtrasExtraRuns(r)}
                  className={`py-3 rounded-xl font-black text-sm border transition ${
                    extrasExtraRuns === r
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200'
                  }`}
                >
                  +{r}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setIsExtrasModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitExtras}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-white bg-emerald-500 hover:bg-emerald-600 rounded-xl shadow-sm"
              >
                Confirm Extras
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 2: WICKET DETAILS (TYPE, DISMISSED, NEXT BATTER)         */}
      {/* ------------------------------------------------------------- */}
      {isWicketModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-rose-500 flex items-center gap-2">
                <span>Record Fall of Wicket</span>
              </h3>
              <button
                onClick={() => setIsWicketModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Wicket Type */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Dismissal Type
              </label>
              <select
                value={wicketType}
                onChange={(e) => setWicketType(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 capitalize"
              >
                <option value="bowled">Bowled</option>
                <option value="caught">Caught</option>
                <option value="lbw">LBW</option>
                <option value="run_out">Run Out</option>
                <option value="stumped">Stumped</option>
                <option value="hit_wicket">Hit Wicket</option>
              </select>
            </div>

            {/* Dismissed Batter */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Dismissed Player
              </label>
              <div className="grid grid-cols-2 gap-3 mt-1">
                <label
                  onClick={() => setDismissedBatterId(activeStrikerId)}
                  className={`p-3 rounded-xl border text-xs font-semibold cursor-pointer transition ${
                    dismissedBatterId === activeStrikerId
                      ? 'border-rose-500 bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      : 'border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <span className="block text-[10px] text-slate-400 font-normal">Striker</span>
                  <span>{playerMap[activeStrikerId] || 'Striker'}</span>
                </label>

                <label
                  onClick={() => setDismissedBatterId(activeNonStrikerId)}
                  className={`p-3 rounded-xl border text-xs font-semibold cursor-pointer transition ${
                    dismissedBatterId === activeNonStrikerId
                      ? 'border-rose-500 bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      : 'border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <span className="block text-[10px] text-slate-400 font-normal">Non-Striker</span>
                  <span>{playerMap[activeNonStrikerId] || 'Non-Striker'}</span>
                </label>
              </div>
            </div>

            {/* Next Batter */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Next Batter In
              </label>
              <select
                value={nextBatterId}
                onChange={(e) => setNextBatterId(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="">No more batters (All Out)</option>
                {battingXi
                  .filter((pId) => pId !== activeStrikerId && pId !== activeNonStrikerId)
                  .map((pId) => (
                    <option key={pId} value={pId}>
                      {playerMap[pId] || pId}
                    </option>
                  ))}
              </select>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setIsWicketModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitWicket}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-500 hover:bg-rose-600 rounded-xl shadow-sm"
              >
                Confirm Wicket
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 3: NEXT BOWLER PICKER (END OF OVER)                     */}
      {/* ------------------------------------------------------------- */}
      {isBowlerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-emerald-500" />
                <span>Select Next Bowler</span>
              </h3>
              <button
                onClick={() => setIsBowlerModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Over complete! Choose the bowler for the next over. (Consecutive overs by the same bowler are prohibited).
            </p>

            <div className="space-y-1.5 max-h-56 overflow-y-auto">
              {bowlingXi.map((pId) => {
                const isCurrent = pId === activeBowlerId;
                return (
                  <button
                    key={pId}
                    disabled={isCurrent}
                    onClick={() => handleChangeBowler(pId)}
                    className={`w-full p-2.5 rounded-xl border text-left text-xs font-semibold flex items-center justify-between transition ${
                      isCurrent
                        ? 'opacity-40 cursor-not-allowed border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-800'
                        : 'border-slate-200 dark:border-slate-700 hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-slate-800 dark:text-slate-200'
                    }`}
                  >
                    <span>{playerMap[pId] || pId}</span>
                    {isCurrent ? (
                      <span className="text-[10px] text-rose-500 font-bold">Bowled Last Over</span>
                    ) : (
                      <span className="text-[10px] text-emerald-500 font-bold">Select</span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setIsBowlerModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
