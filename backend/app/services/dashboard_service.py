from datetime import datetime
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.dashboard import ActivityItem, DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    tournaments_count = (
        db.scalar(select(func.count()).select_from(Tournament)) or 0
    )
    teams_count = db.scalar(select(func.count()).select_from(Team)) or 0
    players_count = db.scalar(select(func.count()).select_from(Player)) or 0
    scheduled_matches_count = (
        db.scalar(
            select(func.count())
            .select_from(Match)
            .where(Match.status == MatchStatus.SCHEDULED)
        )
        or 0
    )

    activities: List[ActivityItem] = []

    # Recent tournaments
    tournaments = db.scalars(
        select(Tournament).order_by(Tournament.created_at.desc()).limit(5)
    ).all()
    for t in tournaments:
        activities.append(
            ActivityItem(
                id=str(t.tournament_id),
                type="tournament",
                description=f"Tournament '{t.name}' was created",
                timestamp=t.created_at,
            )
        )

    # Recent teams
    teams = db.scalars(select(Team).order_by(Team.created_at.desc()).limit(5)).all()
    for tm in teams:
        activities.append(
            ActivityItem(
                id=str(tm.team_id),
                type="team",
                description=f"Team '{tm.team_name}' ({tm.city}) was registered",
                timestamp=tm.created_at,
            )
        )

    # Recent players
    players = db.scalars(
        select(Player).order_by(Player.created_at.desc()).limit(5)
    ).all()
    for p in players:
        activities.append(
            ActivityItem(
                id=str(p.player_id),
                type="player",
                description=f"Player '{p.name}' was registered",
                timestamp=p.created_at,
            )
        )

    # Recent matches
    matches = db.scalars(
        select(Match).order_by(Match.created_at.desc()).limit(5)
    ).all()
    for m in matches:
        activities.append(
            ActivityItem(
                id=str(m.match_id),
                type="match",
                description=f"Match was scheduled for {m.match_date.strftime('%Y-%m-%d') if m.match_date else 'TBD'}",
                timestamp=m.created_at,
            )
        )

    # Recent users
    users = db.scalars(select(User).order_by(User.created_at.desc()).limit(5)).all()
    for u in users:
        activities.append(
            ActivityItem(
                id=str(u.user_id),
                type="user",
                description=f"User '{u.name}' ({u.role.value}) was created",
                timestamp=u.created_at,
            )
        )

    # Sort combined activities descending by timestamp and slice top 5
    activities.sort(key=lambda a: a.timestamp, reverse=True)
    recent_activities = activities[:5]

    return DashboardSummary(
        tournaments_count=tournaments_count,
        teams_count=teams_count,
        players_count=players_count,
        scheduled_matches_count=scheduled_matches_count,
        recent_activities=recent_activities,
    )
