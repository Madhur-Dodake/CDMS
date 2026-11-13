import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.innings import Innings
    from app.models.player import Player


class ExtrasType(str, enum.Enum):
    WIDE = "wide"
    NO_BALL = "no_ball"
    BYE = "bye"
    LEG_BYE = "leg_bye"
    PENALTY = "penalty"
    NONE = "none"


class WicketType(str, enum.Enum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    NONE = "none"


class BallEvent(Base):
    __tablename__ = "ball_events"

    ball_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    innings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("innings.innings_id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # Deviation from spec: sequence_no unique per innings
    over_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    ball_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    striker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.player_id", ondelete="RESTRICT"),
        nullable=False,
    )
    non_striker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.player_id", ondelete="RESTRICT"),
        nullable=False,
    )
    bowler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.player_id", ondelete="RESTRICT"),
        nullable=False,
    )
    runs_scored: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    extras_type: Mapped[ExtrasType] = mapped_column(
        Enum(
            ExtrasType,
            name="extras_type_enum",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ExtrasType.NONE,
        nullable=False,
    )
    extras_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_legal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )  # Deviation from spec: is_legal boolean flag
    is_wicket: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    wicket_type: Mapped[WicketType] = mapped_column(
        Enum(
            WicketType,
            name="wicket_type_enum",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=WicketType.NONE,
        nullable=False,
    )
    dismissed_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.player_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    innings: Mapped["Innings"] = relationship(
        "Innings",
        back_populates="ball_events",
    )
    striker: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[striker_id],
    )
    non_striker: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[non_striker_id],
    )
    bowler: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[bowler_id],
    )
    dismissed_player: Mapped[Optional["Player"]] = relationship(
        "Player",
        foreign_keys=[dismissed_player_id],
    )

    __table_args__ = (
        UniqueConstraint("innings_id", "sequence_no", name="uq_ball_events_innings_sequence"),
        CheckConstraint("runs_scored >= 0 AND runs_scored <= 6", name="check_runs_scored_range"),
        Index("ix_ball_events_innings_id_sequence_no", "innings_id", "sequence_no"),
    )
