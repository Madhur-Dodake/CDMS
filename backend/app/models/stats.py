import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.tournament import Tournament
    from app.models.team import Team


class PlayerStats(Base):
    __tablename__ = "player_stats"

    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.player_id", ondelete="CASCADE"),
        primary_key=True,
    )
    matches_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overs_bowled: Mapped[Decimal] = mapped_column(
        Numeric(5, 1),
        nullable=False,
        default=Decimal("0.0"),
    )
    strike_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    economy: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Relationships
    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="stats",
    )


class PointsTable(Base):
    __tablename__ = "points_table"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.tournament_id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.team_id", ondelete="CASCADE"),
        primary_key=True,
    )
    played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nrr: Mapped[Decimal] = mapped_column(
        Numeric(6, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Relationships
    tournament: Mapped["Tournament"] = relationship(
        "Tournament",
        back_populates="points_table_entries",
    )
    team: Mapped["Team"] = relationship(
        "Team",
    )

