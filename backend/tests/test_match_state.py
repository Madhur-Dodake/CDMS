import pytest
from app.models.match import MatchStatus
from app.services.match_state import (
    InvalidMatchStateTransitionError,
    MatchEvent,
    STATE_TRANSITIONS,
    transition,
)


# -------------------------------------------------------------
# 1. TEST ALL VALID TRANSITIONS (TABLE-DRIVEN)
# -------------------------------------------------------------

VALID_TRANSITIONS = [
    # Scheduled
    (MatchStatus.SCHEDULED, MatchEvent.START_TOSS, MatchStatus.LIVE),
    (MatchStatus.SCHEDULED, MatchEvent.ABANDON, MatchStatus.ABANDONED),
    # Live
    (MatchStatus.LIVE, MatchEvent.INNINGS_END, MatchStatus.INNINGS_BREAK),
    (MatchStatus.LIVE, MatchEvent.SUSPEND, MatchStatus.SUSPENDED),
    (MatchStatus.LIVE, MatchEvent.COMPLETE, MatchStatus.COMPLETED),
    (MatchStatus.LIVE, MatchEvent.ABANDON, MatchStatus.ABANDONED),
    # Innings Break
    (MatchStatus.INNINGS_BREAK, MatchEvent.RESUME, MatchStatus.LIVE),
    (MatchStatus.INNINGS_BREAK, MatchEvent.SUSPEND, MatchStatus.SUSPENDED),
    (MatchStatus.INNINGS_BREAK, MatchEvent.ABANDON, MatchStatus.ABANDONED),
    # Suspended
    (MatchStatus.SUSPENDED, MatchEvent.RESUME, MatchStatus.LIVE),
    (MatchStatus.SUSPENDED, MatchEvent.ABANDON, MatchStatus.ABANDONED),
]


@pytest.mark.parametrize("initial_status, event, expected_status", VALID_TRANSITIONS)
def test_valid_state_transitions(
    initial_status: MatchStatus, event: MatchEvent, expected_status: MatchStatus
) -> None:
    """Verify all valid state transitions succeed and produce the expected status."""
    result = transition(initial_status, event)
    assert result == expected_status

    # Also verify string representation inputs work identically
    result_str = transition(initial_status.value, event.value)
    assert result_str == expected_status


# -------------------------------------------------------------
# 2. TEST ALL INVALID TRANSITIONS (COMPREHENSIVE MATRIX)
# -------------------------------------------------------------

def test_all_invalid_state_transitions_raise() -> None:
    """Verify every status x event combination NOT in STATE_TRANSITIONS raises an error."""
    all_statuses = list(MatchStatus)
    all_events = list(MatchEvent)

    invalid_combinations_tested = 0

    for current_status in all_statuses:
        allowed = STATE_TRANSITIONS.get(current_status, {})
        for event in all_events:
            if event not in allowed:
                with pytest.raises(InvalidMatchStateTransitionError) as exc_info:
                    transition(current_status, event)
                assert f"Invalid transition from state '{current_status.value}'" in str(
                    exc_info.value
                )
                invalid_combinations_tested += 1

    # Total combinations = 6 statuses * 6 events = 36
    # Valid transitions = 11
    # Invalid transitions tested = 25
    assert invalid_combinations_tested == 25


def test_completed_is_terminal() -> None:
    """COMPLETED match cannot transition on any event."""
    for event in MatchEvent:
        with pytest.raises(InvalidMatchStateTransitionError):
            transition(MatchStatus.COMPLETED, event)


def test_abandoned_is_terminal() -> None:
    """ABANDONED match cannot transition on any event."""
    for event in MatchEvent:
        with pytest.raises(InvalidMatchStateTransitionError):
            transition(MatchStatus.ABANDONED, event)


def test_unknown_status_raises_error() -> None:
    """Passing an unmapped status string raises InvalidMatchStateTransitionError."""
    with pytest.raises(InvalidMatchStateTransitionError) as exc_info:
        transition("not_a_real_status", MatchEvent.START_TOSS)
    assert "Unknown match status" in str(exc_info.value)


def test_unknown_event_raises_error() -> None:
    """Passing an unmapped event string raises InvalidMatchStateTransitionError."""
    with pytest.raises(InvalidMatchStateTransitionError) as exc_info:
        transition(MatchStatus.SCHEDULED, "super_over")
    assert "Unknown match event" in str(exc_info.value)
