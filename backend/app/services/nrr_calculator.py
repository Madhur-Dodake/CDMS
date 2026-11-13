from dataclasses import dataclass
from typing import List, Optional


def _validate_fractional_parts(overs: int, balls: int, raw_str: str) -> None:
    """Validate non-negative overs and legal balls range (0-5)."""
    if overs < 0:
        raise ValueError("Overs component cannot be negative")
    if not (0 <= balls <= 5):
        raise ValueError(f"Balls component must be between 0 and 5, got {balls} in '{raw_str}'")


def _parse_fractional_overs(clean_str: str, raw_str: str) -> float:
    """Parse fractional cricket overs ('X.Y') into decimal overs."""
    parts = clean_str.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid overs format '{raw_str}'")

    try:
        overs = int(parts[0])
        balls = int(parts[1])
    except ValueError:
        raise ValueError(f"Non-integer components in overs string '{raw_str}'")

    _validate_fractional_parts(overs, balls, raw_str)
    return round(float(overs) + (balls / 6.0), 6)


def _parse_whole_overs(clean_str: str, raw_str: str) -> float:
    """Parse whole number cricket overs ('X') into float."""
    try:
        overs = int(clean_str)
    except ValueError:
        raise ValueError(f"Invalid overs string '{raw_str}'")

    if overs < 0:
        raise ValueError("Overs component cannot be negative")

    return float(overs)


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
        return _parse_fractional_overs(clean_str, overs_str)
    return _parse_whole_overs(clean_str, overs_str)


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


def _calculate_effective_overs(overs_faced: float, is_all_out: bool, max_overs: Optional[float]) -> float:
    """Return max_overs if team was bowled all out and max_overs is specified."""
    if is_all_out and max_overs is not None:
        return float(max_overs)
    return overs_faced


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
    effective_overs_faced = _calculate_effective_overs(overs_faced, is_all_out, max_overs)

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


def _get_entry_overs(overs: float, is_out: bool, max_ov: float) -> float:
    """Helper to determine effective overs for a single tournament match entry."""
    if is_out and max_ov > 0:
        return float(max_ov)
    return overs


def _compute_run_rates(
    runs_for: int,
    overs_for: float,
    runs_against: int,
    overs_against: float,
) -> float:
    """Compute run rate difference with zero-division protection."""
    if overs_for <= 0.0 and overs_against <= 0.0:
        return 0.0

    rr_for = (runs_for / overs_for) if overs_for > 0.0 else 0.0
    rr_against = (runs_against / overs_against) if overs_against > 0.0 else 0.0
    return round(rr_for - rr_against, 3)


def calculate_cumulative_nrr(match_entries: List[MatchNRREntry]) -> float:
    """Recomputes cumulative NRR from all completed matches for a team in a tournament.

    Does not accumulate incrementally to avoid precision errors.
    Formula:
      Cumulative NRR = (Total Runs Scored / Total Effective Overs Faced)
                     - (Total Runs Conceded / Total Effective Overs Bowled)
    """
    if not match_entries:
        return 0.0

    total_runs_scored = sum(m.runs_scored for m in match_entries)
    total_effective_overs_faced = sum(
        _get_entry_overs(m.overs_faced, m.is_all_out, m.max_overs) for m in match_entries
    )

    total_runs_conceded = sum(m.runs_conceded for m in match_entries)
    total_effective_overs_bowled = sum(
        _get_entry_overs(m.overs_bowled, m.opponent_all_out, m.max_overs) for m in match_entries
    )

    return _compute_run_rates(
        total_runs_scored,
        total_effective_overs_faced,
        total_runs_conceded,
        total_effective_overs_bowled,
    )
