import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.player import Player


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"

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


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    coach_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    players: Mapped[List["Player"]] = relationship(
        "Player",
        back_populates="team",
    )
    tournaments: Mapped[List["Tournament"]] = relationship(
        "Tournament",
        secondary="tournament_teams",
        back_populates="teams",
    )

