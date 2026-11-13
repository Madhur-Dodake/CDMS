import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.team import Team
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.innings import Innings


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    INNINGS_BREAK = "innings_break"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TossDecision(str, enum.Enum):
    BAT = "bat"
    BOWL = "bowl"


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.tournament_id", ondelete="CASCADE"),
        nullable=False,
    )
    team1_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="RESTRICT"),
        nullable=False,
    )
    team2_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="RESTRICT"),
        nullable=False,
    )
    venue_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("venues.venue_id", ondelete="SET NULL"),
        nullable=True,
    )
    scorer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    match_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    overs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(
            MatchStatus,
            name="match_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=MatchStatus.SCHEDULED,
        nullable=False,
    )
    toss_winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="SET NULL"),
        nullable=True,
    )
    toss_decision: Mapped[Optional[TossDecision]] = mapped_column(
        Enum(
            TossDecision,
            name="toss_decision",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="SET NULL"),
        nullable=True,
    )
    result_summary: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tournament: Mapped["Tournament"] = relationship(
        "Tournament",
        back_populates="matches",
    )
    team1: Mapped["Team"] = relationship(
        "Team",
        foreign_keys=[team1_id],
    )
    team2: Mapped["Team"] = relationship(
        "Team",
        foreign_keys=[team2_id],
    )
    venue: Mapped[Optional["Venue"]] = relationship(
        "Venue",
        back_populates="matches",
    )
    scorer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="matches_scored",
    )
    toss_winner: Mapped[Optional["Team"]] = relationship(
        "Team",
        foreign_keys=[toss_winner_id],
    )
    winner: Mapped[Optional["Team"]] = relationship(
        "Team",
        foreign_keys=[winner_id],
    )
    innings: Mapped[List["Innings"]] = relationship(
        "Innings",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="Innings.innings_no",
    )

    __table_args__ = (
        CheckConstraint("team1_id <> team2_id", name="check_match_different_teams"),
        Index("ix_matches_tournament_id_match_date", "tournament_id", "match_date"),
    )
