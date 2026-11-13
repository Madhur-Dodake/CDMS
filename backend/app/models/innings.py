import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.team import Team
    from app.models.ball_event import BallEvent


class Innings(Base):
    __tablename__ = "innings"

    innings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
    )
    batting_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="RESTRICT"),
        nullable=False,
    )
    bowling_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="RESTRICT"),
        nullable=False,
    )
    innings_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    total_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    wickets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    balls_bowled: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )  # Deviation from spec: integer balls instead of decimal overs
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    target_runs: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="innings",
    )
    batting_team: Mapped["Team"] = relationship(
        "Team",
        foreign_keys=[batting_team_id],
    )
    bowling_team: Mapped["Team"] = relationship(
        "Team",
        foreign_keys=[bowling_team_id],
    )
    ball_events: Mapped[List["BallEvent"]] = relationship(
        "BallEvent",
        back_populates="innings",
        cascade="all, delete-orphan",
        order_by="BallEvent.sequence_no",
    )

    __table_args__ = (
        UniqueConstraint("match_id", "innings_no", name="uq_innings_match_innings_no"),
    )

