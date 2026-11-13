from dataclasses import dataclass
from typing import List, Tuple


def batting_average(runs: int, dismissals: int) -> float:
    """Calculate batting average.

    If dismissals > 0: runs / dismissals
    If never dismissed (dismissals == 0): returns float(runs) if runs > 0 else 0.0
    """
    if dismissals > 0:
        return round(float(runs) / float(dismissals), 2)
    return float(runs) if runs > 0 else 0.0


def batting_strike_rate(runs: int, balls_faced: int) -> float:
    """Calculate batting strike rate: (runs / balls_faced) * 100.

    Division-safe: returns 0.0 if balls_faced == 0.
    """
    if balls_faced > 0:
        return round((float(runs) / float(balls_faced)) * 100.0, 2)
    return 0.0


def bowling_economy(runs_conceded: int, balls_bowled: int) -> float:
    """Calculate bowling economy rate: runs_conceded / overs_bowled.

    Division-safe: returns 0.0 if balls_bowled == 0.
    """
    if balls_bowled > 0:
        overs = float(balls_bowled) / 6.0
        return round(float(runs_conceded) / overs, 2)
    return 0.0


def bowling_average(runs_conceded: int, wickets: int) -> float:
    """Calculate bowling average: runs_conceded / wickets.

    Division-safe: returns 0.0 if wickets == 0.
    """
    if wickets > 0:
        return round(float(runs_conceded) / float(wickets), 2)
    return 0.0


def count_milestones(scores: List[int]) -> Tuple[int, int]:
    """Count batting milestones (fifties, hundreds) from a list of innings scores.

    - Fifty: 50 <= score < 100
    - Hundred: score >= 100
    """
    fifties = sum(1 for s in scores if 50 <= s < 100)
    hundreds = sum(1 for s in scores if s >= 100)
    return fifties, hundreds


@dataclass
class PlayerCareerMetrics:
    matches_played: int
    runs: int
    balls_faced: int
    wickets: int
    runs_conceded: int
    balls_bowled: int
    overs_display: str
    batting_average: float
    strike_rate: float
    bowling_average: float
    economy: float
    fifties: int
    hundreds: int


def compute_career_metrics(
    matches_played: int,
    runs: int,
    balls_faced: int,
    dismissals: int,
    wickets: int,
    runs_conceded: int,
    balls_bowled: int,
    innings_scores: List[int],
) -> PlayerCareerMetrics:
    """Pure domain function aggregating career metrics for a player."""
    avg = batting_average(runs, dismissals)
    sr = batting_strike_rate(runs, balls_faced)
    bw_avg = bowling_average(runs_conceded, wickets)
    econ = bowling_economy(runs_conceded, balls_bowled)
    fifties, hundreds = count_milestones(innings_scores)

    overs_str = f"{balls_bowled // 6}.{balls_bowled % 6}"

    return PlayerCareerMetrics(
        matches_played=matches_played,
        runs=runs,
        balls_faced=balls_faced,
        wickets=wickets,
        runs_conceded=runs_conceded,
        balls_bowled=balls_bowled,
        overs_display=overs_str,
        batting_average=avg,
        strike_rate=sr,
        bowling_average=bw_avg,
        economy=econ,
        fifties=fifties,
        hundreds=hundreds,
    )
