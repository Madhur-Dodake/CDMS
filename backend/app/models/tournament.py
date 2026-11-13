import enum
import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.team import Team
    from app.models.match import Match
    from app.models.stats import PointsTable


class TournamentLevel(str, enum.Enum):
    LOCAL = "local"
    CLUB = "club"
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class MatchFormat(str, enum.Enum):
    T20 = "T20"
    ODI = "ODI"
    TEST = "Test"
    OTHER = "Other"


class Tournament(Base):
    __tablename__ = "tournaments"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[TournamentLevel] = mapped_column(
        Enum(
            TournamentLevel,
            name="tournament_level",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    format: Mapped[MatchFormat] = mapped_column(
        Enum(
            MatchFormat,
            name="match_format",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="tournaments_created",
    )
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        secondary="tournament_teams",
        back_populates="tournaments",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    points_table_entries: Mapped[List["PointsTable"]] = relationship(
        "PointsTable",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
