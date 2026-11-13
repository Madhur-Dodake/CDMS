from dataclasses import dataclass
from typing import List, Optional


def overs_to_decimal(overs_str: str) -> float:
    """Convert cricket overs notation (e.g. '45.3') to decimal overs (45.5).

    The balls component (after the dot) must be between 0 and 5 inclusive.
    Raises ValueError on invalid formats or balls >= 6.
    """
    if not isinstance(overs_str, str):
        overs_str = str(overs_str)

    clean_str = overs_str.strip()
    if not clean_str:
        return 0.0

    if "." in clean_str:
        parts = clean_str.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid overs format '{overs_str}'")

        try:
            overs = int(parts[0])
            balls = int(parts[1])
        except ValueError:
            raise ValueError(f"Non-integer components in overs string '{overs_str}'")

        if overs < 0:
            raise ValueError("Overs component cannot be negative")
        if balls < 0 or balls > 5:
            raise ValueError(
                f"Balls component must be between 0 and 5, got {balls} in '{overs_str}'"
            )

        return round(float(overs) + (balls / 6.0), 6)
    else:
        try:
            overs = int(clean_str)
        except ValueError:
            raise ValueError(f"Invalid overs string '{overs_str}'")

        if overs < 0:
            raise ValueError("Overs component cannot be negative")

        return float(overs)


def decimal_to_overs(overs_decimal: float) -> str:
    """Convert decimal overs back to cricket notation (e.g. 45.5 -> '45.3')."""
    if overs_decimal <= 0:
        return "0.0"

    total_balls = int(round(overs_decimal * 6.0))
    overs = total_balls // 6
    balls = total_balls % 6
    return f"{overs}.{balls}"


def balls_to_decimal_overs(balls: int) -> float:
    """Convert total integer balls to decimal overs (e.g. 118 balls -> 19.666667)."""
    if balls <= 0:
        return 0.0
    return round(balls / 6.0, 6)


def calculate_nrr(
    runs_scored: int,
    overs_faced: float,
    runs_conceded: int,
    overs_bowled: float,
    is_all_out: bool = False,
    max_overs: Optional[float] = None,
) -> float:
    """Pure domain Net Run Rate (NRR) calculator.

    Formula:
      NRR = (Runs Scored / Overs Faced) - (Runs Conceded / Overs Bowled)

    Rules:
      1. If a team is all out, overs_faced counts as the full allocated quota (max_overs).
      2. If overs faced or bowled is 0, that component defaults to 0.0 (division guard).
      3. Returns NRR rounded to 3 decimal places.
    """
    effective_overs_faced = float(max_overs) if (is_all_out and max_overs is not None) else overs_faced

    if effective_overs_faced <= 0.0 and overs_bowled <= 0.0:
        return 0.0

    run_rate_for = (runs_scored / effective_overs_faced) if effective_overs_faced > 0.0 else 0.0
    run_rate_against = (runs_conceded / overs_bowled) if overs_bowled > 0.0 else 0.0

    return round(run_rate_for - run_rate_against, 3)


@dataclass
class MatchNRREntry:
    """Data record for an individual match in cumulative tournament NRR calculation."""

    runs_scored: int
    overs_faced: float
    is_all_out: bool
    max_overs: float
    runs_conceded: int
    overs_bowled: float
    opponent_all_out: bool


def calculate_cumulative_nrr(match_entries: List[MatchNRREntry]) -> float:
    """Recomputes cumulative NRR from all completed matches for a team in a tournament.

    Does not accumulate incrementally to avoid precision errors.
    Formula:
      Cumulative NRR = (Total Runs Scored / Total Effective Overs Faced)
                     - (Total Runs Conceded / Total Effective Overs Bowled)
    """
    if not match_entries:
        return 0.0

    total_runs_scored = 0
    total_effective_overs_faced = 0.0
    total_runs_conceded = 0
    total_effective_overs_bowled = 0.0

    for m in match_entries:
        total_runs_scored += m.runs_scored
        if m.is_all_out and m.max_overs > 0:
            total_effective_overs_faced += float(m.max_overs)
        else:
            total_effective_overs_faced += m.overs_faced

        total_runs_conceded += m.runs_conceded
        if m.opponent_all_out and m.max_overs > 0:
            total_effective_overs_bowled += float(m.max_overs)
        else:
            total_effective_overs_bowled += m.overs_bowled

    if total_effective_overs_faced <= 0.0 and total_effective_overs_bowled <= 0.0:
        return 0.0

    rr_for = (total_runs_scored / total_effective_overs_faced) if total_effective_overs_faced > 0.0 else 0.0
    rr_against = (total_runs_conceded / total_effective_overs_bowled) if total_effective_overs_bowled > 0.0 else 0.0

    return round(rr_for - rr_against, 3)
