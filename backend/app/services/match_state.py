import enum
from typing import Union

from app.models.match import MatchStatus


class MatchEvent(str, enum.Enum):
    START_TOSS = "start_toss"
    INNINGS_END = "innings_end"
    RESUME = "resume"
    SUSPEND = "suspend"
    COMPLETE = "complete"
    ABANDON = "abandon"


class InvalidMatchStateTransitionError(ValueError):
    """Raised when an invalid state transition is requested on a match."""
    pass


# Deterministic State Transition Table
# Maps (Current MatchStatus, MatchEvent) -> New MatchStatus
STATE_TRANSITIONS: dict[MatchStatus, dict[MatchEvent, MatchStatus]] = {
    MatchStatus.SCHEDULED: {
        MatchEvent.START_TOSS: MatchStatus.LIVE,
        MatchEvent.ABANDON: MatchStatus.ABANDONED,
    },
    MatchStatus.LIVE: {
        MatchEvent.INNINGS_END: MatchStatus.INNINGS_BREAK,
        MatchEvent.SUSPEND: MatchStatus.SUSPENDED,
        MatchEvent.COMPLETE: MatchStatus.COMPLETED,
        MatchEvent.ABANDON: MatchStatus.ABANDONED,
    },
    MatchStatus.INNINGS_BREAK: {
        MatchEvent.RESUME: MatchStatus.LIVE,
        MatchEvent.SUSPEND: MatchStatus.SUSPENDED,
        MatchEvent.ABANDON: MatchStatus.ABANDONED,
    },
    MatchStatus.SUSPENDED: {
        MatchEvent.RESUME: MatchStatus.LIVE,
        MatchEvent.ABANDON: MatchStatus.ABANDONED,
    },
    MatchStatus.COMPLETED: {},
    MatchStatus.ABANDONED: {},
}


def transition(
    current_status: Union[MatchStatus, str],
    event: Union[MatchEvent, str],
) -> MatchStatus:
    """Pure domain function executing match state transitions.

    Zero database, network, or external side effects.
    Raises InvalidMatchStateTransitionError on any invalid or unrecognized transition.
    """
    try:
        status_enum = (
            current_status
            if isinstance(current_status, MatchStatus)
            else MatchStatus(str(current_status).lower())
        )
    except ValueError:
        raise InvalidMatchStateTransitionError(
            f"Unknown match status: '{current_status}'"
        )

    try:
        event_enum = (
            event
            if isinstance(event, MatchEvent)
            else MatchEvent(str(event).lower())
        )
    except ValueError:
        raise InvalidMatchStateTransitionError(
            f"Unknown match event: '{event}'"
        )

    allowed_events = STATE_TRANSITIONS.get(status_enum, {})
    if event_enum not in allowed_events:
        raise InvalidMatchStateTransitionError(
            f"Invalid transition from state '{status_enum.value}' via event '{event_enum.value}'"
        )

    return allowed_events[event_enum]
