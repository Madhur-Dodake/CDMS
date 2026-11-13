"""Database seed script for CDMS.

Creates:
- 1 Admin user (admin@cdms.com / admin123)
- 2 Scorer users (scorer1@cdms.com, scorer2@cdms.com)
- 4 Teams with 15 players each (total 60 players)
- 3 Venues
- 2 Tournaments with tournament_teams and points_table entries
- Scheduled matches assigned to scorers and venues
"""

import sys
import os
from datetime import date, datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.auth import get_password_hash
from app.core.database import SessionLocal, engine
from app.models import (
    Base,
    User,
    UserRole,
    Team,
    TournamentTeam,
    Tournament,
    TournamentLevel,
    MatchFormat,
    Player,
    Venue,
    Match,
    MatchStatus,
    TossDecision,
    PlayerStats,
    PointsTable,
)


def seed_database() -> None:
    session = SessionLocal()
    try:
        print("Starting CDMS database seeding...")

        # Clear existing records in reverse dependency order for clean idempotent run
        session.query(PointsTable).delete()
        session.query(TournamentTeam).delete()
        session.query(Match).delete()
        session.query(PlayerStats).delete()
        session.query(Player).delete()
        session.query(Venue).delete()
        session.query(Tournament).delete()
        session.query(Team).delete()
        session.query(User).delete()
        session.commit()
        print("Cleaned existing database records.")

        # 1. Create Users
        admin_user = User(
            name="System Administrator",
            email="admin@cdms.com",
            password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
        )
        scorer_1 = User(
            name="Ramesh Tendulkar (Scorer)",
            email="scorer1@cdms.com",
            password=get_password_hash("scorer123"),
            role=UserRole.SCORER,
        )
        scorer_2 = User(
            name="Sunil Gavaskar (Scorer)",
            email="scorer2@cdms.com",
            password=get_password_hash("scorer123"),
            role=UserRole.SCORER,
        )
        viewer_user = User(
            name="Cricket Fan (Viewer)",
            email="viewer@cdms.com",
            password=get_password_hash("viewer123"),
            role=UserRole.VIEWER,
        )
        session.add_all([admin_user, scorer_1, scorer_2, viewer_user])
        session.flush()
        print(f"Created 4 users (1 Admin: {admin_user.email}, 2 Scorers, 1 Viewer: {viewer_user.email}).")

        # 2. Create Venues
        venues = [
            Venue(venue_name="Wankhede Stadium", city="Mumbai", capacity=33108),
            Venue(venue_name="Arun Jaitley Stadium", city="Delhi", capacity=41842),
            Venue(venue_name="M. Chinnaswamy Stadium", city="Bangalore", capacity=40000),
        ]
        session.add_all(venues)
        session.flush()
        print(f"Created {len(venues)} venues.")

        # 3. Create Teams
        teams_data = [
            {"name": "Mumbai Masters", "code": "MM", "city": "Mumbai", "coach": "Mahela Jayawardene"},
            {"name": "Delhi Dynamos", "code": "DD", "city": "Delhi", "coach": "Ricky Ponting"},
            {"name": "Bangalore Blasters", "code": "BB", "city": "Bangalore", "coach": "Andy Flower"},
            {"name": "Chennai Champions", "code": "CC", "city": "Chennai", "coach": "Stephen Fleming"},
        ]

        teams = []
        for t in teams_data:
            team = Team(
                team_name=t["name"],
                short_code=t["code"],
                city=t["city"],
                coach_name=t["coach"],
            )
            teams.append(team)
            session.add(team)
        session.flush()
        print(f"Created {len(teams)} teams.")

        # 4. Create 15 Players for each Team (total 60 players)
        first_names = [
            "Rohit", "Virat", "Jasprit", "Ravindra", "Hardik", "Shubman", "Surya", "Rishabh",
            "Mohammed", "Kuldeep", "Axar", "Shreyas", "Yuzvendra", "Sanju", "Ishan",
            "KL", "Arshdeep", "Shardul", "Deepak", "Washington", "Ruturaj", "Tilak", "Rinku",
            "Jitesh", "Shivam", "Mukesh", "Avesh", "Prasidh", "Umran", "Mayank", "Yashasvi",
            "Dhruv", "Sai", "Abhishek", "Harshit", "Nitish", "Varun", "Ravi", "Khaleel",
            "Tushar", "Rahul", "Dinesh", "Krunal", "Devdutt", "Ayush", "Mohit", "Piyush",
            "Shahbaz", "Anuj", "Suyash", "Akash", "Simarjeet", "Vijay", "Manish", "Karun",
            "Jaydev", "Siddharth", "Chetan", "Swapnil", "Anukul",
        ]
        last_names = [
            "Sharma", "Kohli", "Bumrah", "Jadeja", "Pandya", "Gill", "Yadav", "Pant",
            "Siraj", "Patel", "Iyer", "Chahal", "Samson", "Kishan", "Rahul",
            "Singh", "Thakur", "Chahar", "Sundar", "Gaikwad", "Varma", "Reddy",
            "Dubey", "Kumar", "Khan", "Krishna", "Malik", "Agarwal", "Jaiswal",
            "Jurel", "Sudarshan", "Rana", "Bishnoi", "Ahmed", "Deshpande", "Tewatia",
            "Karthik", "Rawat", "Deep", "Shankar", "Pandey", "Nair", "Unadkat", "Kaul",
            "Sakariya", "Roy", "Gowtham", "Gopal", "Lomror", "Samad", "Markande", "Sen",
            "Tyagi", "Warrier", "Bawa", "Hangargekar", "Ostwal", "Chauhan", "Dagar", "Vyas"
        ]

        roles_cycle = ["Batter", "Batter", "Batter", "Batter", "Batter",
                       "All-rounder", "All-rounder", "All-rounder",
                       "Wicketkeeper", "Wicketkeeper",
                       "Bowler", "Bowler", "Bowler", "Bowler", "Bowler"]

        player_count = 0
        name_idx = 0
        for team in teams:
            for i in range(15):
                p_name = f"{first_names[name_idx % len(first_names)]} {last_names[name_idx % len(last_names)]}"
                name_idx += 1
                role = roles_cycle[i % len(roles_cycle)]
                batting_style = "Left-hand bat" if (i % 3 == 0) else "Right-hand bat"
                bowling_style = "Slow left-arm" if (i % 4 == 0) else "Right-arm fast"

                player = Player(
                    team_id=team.team_id,
                    name=p_name,
                    dob=date(1995 + (i % 10), 1 + (i % 12), 1 + (i % 28)),
                    batting_style=batting_style,
                    bowling_style=bowling_style,
                    role=role,
                )
                session.add(player)
                session.flush()

                # Seed initialized PlayerStats record
                stats = PlayerStats(
                    player_id=player.player_id,
                    matches_played=0,
                    runs=0,
                    balls_faced=0,
                    wickets=0,
                    runs_conceded=0,
                )
                session.add(stats)
                player_count += 1

        session.flush()
        print(f"Created {player_count} players (15 per team) with initialized stats records.")

        # 5. Create 2 Tournaments
        t1 = Tournament(
            name="Premier Cricket League 2026",
            level=TournamentLevel.DOMESTIC,
            format=MatchFormat.T20,
            start_date=date(2026, 3, 15),
            end_date=date(2026, 4, 15),
            created_by=admin_user.user_id,
        )
        t2 = Tournament(
            name="National Club Championship 2026",
            level=TournamentLevel.CLUB,
            format=MatchFormat.T20,
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 25),
            created_by=admin_user.user_id,
        )
        session.add_all([t1, t2])
        session.flush()
        print(f"Created 2 tournaments: '{t1.name}' and '{t2.name}'.")

        # Associate all 4 teams with both tournaments and initialize points tables
        for tourney in [t1, t2]:
            for team in teams:
                tt = TournamentTeam(
                    tournament_id=tourney.tournament_id,
                    team_id=team.team_id,
                )
                pt = PointsTable(
                    tournament_id=tourney.tournament_id,
                    team_id=team.team_id,
                    played=0,
                    won=0,
                    lost=0,
                    tied=0,
                    nr=0,
                    points=0,
                )
                session.add_all([tt, pt])
        session.flush()
        print("Associated teams and initialized points tables for both tournaments.")

        # 6. Create Scheduled Matches
        now_utc = datetime.now(timezone.utc)
        matches = [
            Match(
                tournament_id=t1.tournament_id,
                team1_id=teams[0].team_id,
                team2_id=teams[1].team_id,
                venue_id=venues[0].venue_id,
                scorer_id=scorer_1.user_id,
                match_date=now_utc + timedelta(days=2, hours=14),
                overs=20,
                status=MatchStatus.SCHEDULED,
            ),
            Match(
                tournament_id=t1.tournament_id,
                team1_id=teams[2].team_id,
                team2_id=teams[3].team_id,
                venue_id=venues[2].venue_id,
                scorer_id=scorer_2.user_id,
                match_date=now_utc + timedelta(days=3, hours=19),
                overs=20,
                status=MatchStatus.SCHEDULED,
            ),
            Match(
                tournament_id=t1.tournament_id,
                team1_id=teams[0].team_id,
                team2_id=teams[2].team_id,
                venue_id=venues[0].venue_id,
                scorer_id=scorer_1.user_id,
                match_date=now_utc + timedelta(days=5, hours=19),
                overs=20,
                status=MatchStatus.SCHEDULED,
            ),
            Match(
                tournament_id=t2.tournament_id,
                team1_id=teams[1].team_id,
                team2_id=teams[3].team_id,
                venue_id=venues[1].venue_id,
                scorer_id=scorer_2.user_id,
                match_date=now_utc + timedelta(days=20, hours=15),
                overs=20,
                status=MatchStatus.SCHEDULED,
            ),
        ]
        session.add_all(matches)
        session.commit()
        print(f"Created {len(matches)} scheduled matches.")

        print("\nDatabase seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()

