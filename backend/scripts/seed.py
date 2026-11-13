"""Database seed script for CDMS.

Creates:
- 1 Admin user (admin@cdms.com / admin123)
- 2 Scorer users (scorer1@cdms.com, scorer2@cdms.com)
- 1 Viewer user (viewer@cdms.com / viewer123)
- 4 Teams with 15 players each (total 60 players) with rich career stats
- 3 Venues (Wankhede, Arun Jaitley, M. Chinnaswamy)
- 2 Tournaments (Premier Cricket League 2026, National Club Championship 2026)
- 1 LIVE match with active innings and ball events
- 2 COMPLETED matches with official results, scorecards, and updated points table
- 2 SCHEDULED matches
"""

import sys
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

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
    Innings,
    BallEvent,
)
from app.models.ball_event import ExtrasType, WicketType


def seed_database() -> None:
    session = SessionLocal()
    try:
        print("Starting comprehensive CDMS database seeding...")

        # 0. Clean existing records in reverse dependency order
        session.query(BallEvent).delete()
        session.query(Innings).delete()
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
        print(f"Created 4 users: admin@cdms.com, scorer1@cdms.com, viewer@cdms.com.")

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

        # 4. Create Players with Realistic Names & Career Stats
        team_player_names = {
            "MM": [
                ("Rohit Sharma", "Batter", "Right-hand bat", "Right-arm offbreak", 48, 1420, 980, 15, 280, Decimal("32.4")),
                ("Ishan Kishan", "Wicketkeeper", "Left-hand bat", "None", 40, 1120, 810, 0, 0, Decimal("0.0")),
                ("Suryakumar Yadav", "Batter", "Right-hand bat", "Right-arm medium", 44, 1380, 890, 6, 120, Decimal("14.0")),
                ("Tilak Varma", "Batter", "Left-hand bat", "Right-arm offbreak", 28, 790, 560, 4, 85, Decimal("10.2")),
                ("Hardik Pandya", "All-rounder", "Right-hand bat", "Right-arm fast-medium", 46, 980, 680, 38, 760, Decimal("112.0")),
                ("Tim David", "Batter", "Right-hand bat", "Right-arm offbreak", 30, 640, 390, 2, 45, Decimal("6.0")),
                ("Jasprit Bumrah", "Bowler", "Right-hand bat", "Right-arm fast", 45, 85, 95, 62, 1020, Decimal("158.0")),
                ("Piyush Chawla", "Bowler", "Left-hand bat", "Right-arm legbreak", 50, 110, 120, 55, 1140, Decimal("165.2")),
                ("Gerald Coetzee", "Bowler", "Right-hand bat", "Right-arm fast", 18, 90, 75, 24, 410, Decimal("58.0")),
                ("Akash Madhwal", "Bowler", "Right-hand bat", "Right-arm medium-fast", 16, 20, 25, 20, 340, Decimal("48.4")),
                ("Nehal Wadhera", "Batter", "Left-hand bat", "Right-arm legbreak", 15, 340, 240, 1, 30, Decimal("4.0")),
                ("Nuwan Thushara", "Bowler", "Right-hand bat", "Right-arm fast-medium", 10, 12, 15, 14, 220, Decimal("34.0")),
                ("Naman Dhir", "All-rounder", "Right-hand bat", "Right-arm offbreak", 12, 210, 145, 3, 60, Decimal("8.0")),
                ("Anshul Kamboj", "Bowler", "Right-hand bat", "Right-arm medium-fast", 8, 15, 20, 9, 160, Decimal("24.0")),
                ("Shivalik Sharma", "Batter", "Left-hand bat", "Slow left-arm orthodox", 5, 85, 65, 0, 0, Decimal("0.0")),
            ],
            "DD": [
                ("David Warner", "Batter", "Left-hand bat", "Right-arm legbreak", 55, 1640, 1180, 2, 50, Decimal("8.0")),
                ("Prithvi Shaw", "Batter", "Right-hand bat", "Right-arm offbreak", 38, 980, 640, 0, 0, Decimal("0.0")),
                ("Mitchell Marsh", "All-rounder", "Right-hand bat", "Right-arm fast-medium", 32, 780, 540, 22, 420, Decimal("62.0")),
                ("Rishabh Pant", "Wicketkeeper", "Left-hand bat", "None", 42, 1240, 830, 0, 0, Decimal("0.0")),
                ("Tristan Stubbs", "Batter", "Right-hand bat", "Right-arm offbreak", 22, 520, 310, 4, 75, Decimal("10.0")),
                ("Axar Patel", "All-rounder", "Left-hand bat", "Slow left-arm orthodox", 48, 820, 620, 44, 880, Decimal("138.0")),
                ("Kuldeep Yadav", "Bowler", "Left-hand bat", "Left-arm wrist-spin", 44, 115, 130, 52, 940, Decimal("146.0")),
                ("Anrich Nortje", "Bowler", "Right-hand bat", "Right-arm fast", 30, 45, 55, 42, 680, Decimal("98.0")),
                ("Khaleel Ahmed", "Bowler", "Right-hand bat", "Left-arm fast-medium", 35, 30, 40, 39, 740, Decimal("110.0")),
                ("Mukesh Kumar", "Bowler", "Right-hand bat", "Right-arm medium-fast", 25, 22, 30, 31, 560, Decimal("82.0")),
                ("Abishek Porel", "Wicketkeeper", "Left-hand bat", "None", 16, 310, 205, 0, 0, Decimal("0.0")),
                ("Jake Fraser-McGurk", "Batter", "Right-hand bat", "Right-arm legbreak", 14, 430, 190, 0, 0, Decimal("0.0")),
                ("Rasikh Dar", "Bowler", "Right-hand bat", "Right-arm medium", 12, 18, 22, 15, 260, Decimal("38.0")),
                ("Lalit Yadav", "All-rounder", "Right-hand bat", "Right-arm offbreak", 20, 290, 240, 10, 210, Decimal("32.0")),
                ("Ricky Bhui", "Batter", "Right-hand bat", "Right-arm legbreak", 8, 120, 95, 0, 0, Decimal("0.0")),
            ],
            "BB": [
                ("Faf du Plessis", "Batter", "Right-hand bat", "Right-arm legbreak", 45, 1350, 960, 0, 0, Decimal("0.0")),
                ("Virat Kohli", "Batter", "Right-hand bat", "Right-arm medium", 52, 1680, 1210, 4, 70, Decimal("11.0")),
                ("Glenn Maxwell", "All-rounder", "Right-hand bat", "Right-arm offbreak", 42, 1050, 620, 26, 490, Decimal("74.0")),
                ("Rajat Patidar", "Batter", "Right-hand bat", "Right-arm offbreak", 24, 690, 440, 0, 0, Decimal("0.0")),
                ("Cameron Green", "All-rounder", "Right-hand bat", "Right-arm fast-medium", 26, 610, 410, 18, 380, Decimal("56.0")),
                ("Dinesh Karthik", "Wicketkeeper", "Right-hand bat", "Right-arm offbreak", 40, 880, 520, 0, 0, Decimal("0.0")),
                ("Mahipal Lomror", "Batter", "Left-hand bat", "Slow left-arm orthodox", 22, 360, 240, 3, 50, Decimal("8.0")),
                ("Mohammed Siraj", "Bowler", "Right-hand bat", "Right-arm fast", 44, 40, 60, 48, 920, Decimal("142.0")),
                ("Lockie Ferguson", "Bowler", "Right-hand bat", "Right-arm fast", 25, 30, 45, 32, 540, Decimal("78.0")),
                ("Yash Dayal", "Bowler", "Left-hand bat", "Left-arm medium-fast", 22, 18, 25, 25, 460, Decimal("68.0")),
                ("Karn Sharma", "Bowler", "Left-hand bat", "Right-arm legbreak", 30, 80, 90, 30, 580, Decimal("86.0")),
                ("Will Jacks", "All-rounder", "Right-hand bat", "Right-arm offbreak", 15, 390, 225, 5, 110, Decimal("16.0")),
                ("Anuj Rawat", "Wicketkeeper", "Left-hand bat", "None", 18, 280, 210, 0, 0, Decimal("0.0")),
                ("Suyash Prabhudessai", "Batter", "Right-hand bat", "Right-arm medium", 12, 160, 125, 0, 0, Decimal("0.0")),
                ("Vijaykumar Vyshak", "Bowler", "Right-hand bat", "Right-arm medium-fast", 14, 25, 35, 16, 310, Decimal("44.0")),
            ],
            "CC": [
                ("Ruturaj Gaikwad", "Batter", "Right-hand bat", "Right-arm offbreak", 46, 1480, 1080, 0, 0, Decimal("0.0")),
                ("Devon Conway", "Batter", "Left-hand bat", "Right-arm medium", 32, 1020, 740, 0, 0, Decimal("0.0")),
                ("Ajinkya Rahane", "Batter", "Right-hand bat", "Right-arm medium", 38, 860, 610, 0, 0, Decimal("0.0")),
                ("Shivam Dube", "All-rounder", "Left-hand bat", "Right-arm medium", 36, 940, 590, 8, 140, Decimal("21.0")),
                ("Ravindra Jadeja", "All-rounder", "Left-hand bat", "Slow left-arm orthodox", 50, 780, 590, 48, 940, Decimal("148.0")),
                ("MS Dhoni", "Wicketkeeper", "Right-hand bat", "Right-arm medium", 45, 720, 410, 0, 0, Decimal("0.0")),
                ("Moeen Ali", "All-rounder", "Left-hand bat", "Right-arm offbreak", 34, 690, 480, 24, 460, Decimal("70.0")),
                ("Deepak Chahar", "Bowler", "Right-hand bat", "Right-arm medium-fast", 36, 90, 110, 38, 760, Decimal("114.0")),
                ("Matheesha Pathirana", "Bowler", "Right-hand bat", "Right-arm fast", 24, 15, 25, 38, 480, Decimal("72.0")),
                ("Tushar Deshpande", "Bowler", "Right-hand bat", "Right-arm medium-fast", 30, 25, 40, 36, 680, Decimal("98.0")),
                ("Maheesh Theekshana", "Bowler", "Right-hand bat", "Right-arm offbreak", 28, 40, 55, 28, 560, Decimal("88.0")),
                ("Sameer Rizvi", "Batter", "Right-hand bat", "Right-arm offbreak", 10, 180, 115, 0, 0, Decimal("0.0")),
                ("Shardul Thakur", "All-rounder", "Right-hand bat", "Right-arm medium-fast", 34, 380, 290, 35, 720, Decimal("108.0")),
                ("Mustafizur Rahman", "Bowler", "Left-hand bat", "Left-arm fast-medium", 26, 20, 30, 34, 520, Decimal("76.0")),
                ("Mitchell Santner", "All-rounder", "Left-hand bat", "Slow left-arm orthodox", 20, 190, 150, 18, 360, Decimal("56.0")),
            ],
        }

        created_players_by_team = {}
        for team in teams:
            t_code = team.short_code
            p_list = team_player_names.get(t_code, [])
            created_players_by_team[t_code] = []

            for p_tuple in p_list:
                name, role, bat_st, bowl_st, mp, runs, bf, wkts, rc, ob = p_tuple
                player = Player(
                    team_id=team.team_id,
                    name=name,
                    dob=date(1995, 5, 10),
                    batting_style=bat_st,
                    bowling_style=bowl_st,
                    role=role,
                )
                session.add(player)
                session.flush()

                stats = PlayerStats(
                    player_id=player.player_id,
                    matches_played=mp,
                    runs=runs,
                    balls_faced=bf,
                    wickets=wkts,
                    runs_conceded=rc,
                    overs_bowled=ob,
                )
                session.add(stats)
                created_players_by_team[t_code].append(player)

        session.flush()
        print("Created 60 players across 4 teams with realistic career stats.")

        # 5. Create Tournaments
        t1 = Tournament(
            name="Premier Cricket League 2026",
            level=TournamentLevel.DOMESTIC,
            format=MatchFormat.T20,
            start_date=date(2026, 3, 15),
            end_date=date(2026, 4, 30),
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

        for tourney in [t1, t2]:
            for team in teams:
                session.add(TournamentTeam(tournament_id=tourney.tournament_id, team_id=team.team_id))
        session.flush()

        # 6. Create Matches
        now_utc = datetime.now(timezone.utc)

        # Match 1: LIVE match (Mumbai Masters vs Delhi Dynamos)
        m_live = Match(
            tournament_id=t1.tournament_id,
            team1_id=teams[0].team_id,  # MM
            team2_id=teams[1].team_id,  # DD
            venue_id=venues[0].venue_id,  # Wankhede
            scorer_id=scorer_1.user_id,
            match_date=now_utc - timedelta(hours=1, minutes=30),
            overs=20,
            status=MatchStatus.LIVE,
            toss_winner_id=teams[1].team_id,
            toss_decision=TossDecision.BOWL,
        )
        session.add(m_live)
        session.flush()

        # Innings 1 for Live Match: Mumbai Masters batting (146/3 in 16.4 overs = 100 legal balls)
        inn_live = Innings(
            match_id=m_live.match_id,
            batting_team_id=teams[0].team_id,
            bowling_team_id=teams[1].team_id,
            innings_no=1,
            total_runs=146,
            wickets=3,
            balls_bowled=100,  # 16.4 overs
            is_completed=False,
            target_runs=None,
        )
        session.add(inn_live)
        session.flush()

        mm_players = created_players_by_team["MM"]
        dd_players = created_players_by_team["DD"]

        # Seed key ball events for Innings 1
        # Rohit Sharma (p0), Ishan Kishan (p1 - out), Surya (p2), Tilak (p3 - out), Hardik (p4 - out)
        # Bowlers: Nortje (dd7), Kuldeep (dd6), Axar (dd5), Khaleel (dd8)
        live_events = [
            # Over 1: Khaleel to Rohit & Ishan
            BallEvent(innings_id=inn_live.innings_id, sequence_no=1, over_no=0, ball_no=1, striker_id=mm_players[0].player_id, non_striker_id=mm_players[1].player_id, bowler_id=dd_players[8].player_id, runs_scored=4, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=2, over_no=0, ball_no=2, striker_id=mm_players[0].player_id, non_striker_id=mm_players[1].player_id, bowler_id=dd_players[8].player_id, runs_scored=1, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=3, over_no=0, ball_no=3, striker_id=mm_players[1].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[8].player_id, runs_scored=0, is_legal=True),
            # Wicket 1: Ishan caught
            BallEvent(innings_id=inn_live.innings_id, sequence_no=4, over_no=0, ball_no=4, striker_id=mm_players[1].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[8].player_id, runs_scored=0, is_legal=True, is_wicket=True, wicket_type=WicketType.CAUGHT, dismissed_player_id=mm_players[1].player_id),
            # Surya in
            BallEvent(innings_id=inn_live.innings_id, sequence_no=5, over_no=0, ball_no=5, striker_id=mm_players[2].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[8].player_id, runs_scored=4, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=6, over_no=0, ball_no=6, striker_id=mm_players[2].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[8].player_id, runs_scored=1, is_legal=True),
            # Wicket 2: Tilak bowled later
            BallEvent(innings_id=inn_live.innings_id, sequence_no=7, over_no=9, ball_no=3, striker_id=mm_players[3].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[6].player_id, runs_scored=0, is_legal=True, is_wicket=True, wicket_type=WicketType.BOWLED, dismissed_player_id=mm_players[3].player_id),
            # Wicket 3: Hardik lbw
            BallEvent(innings_id=inn_live.innings_id, sequence_no=8, over_no=14, ball_no=5, striker_id=mm_players[4].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[7].player_id, runs_scored=0, is_legal=True, is_wicket=True, wicket_type=WicketType.LBW, dismissed_player_id=mm_players[4].player_id),
            # Recent over deliveries (last 6 balls: 1, 4, 0, 6, 1, 2)
            BallEvent(innings_id=inn_live.innings_id, sequence_no=9, over_no=15, ball_no=5, striker_id=mm_players[0].player_id, non_striker_id=mm_players[2].player_id, bowler_id=dd_players[7].player_id, runs_scored=1, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=10, over_no=15, ball_no=6, striker_id=mm_players[2].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[7].player_id, runs_scored=4, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=11, over_no=16, ball_no=1, striker_id=mm_players[0].player_id, non_striker_id=mm_players[2].player_id, bowler_id=dd_players[7].player_id, runs_scored=0, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=12, over_no=16, ball_no=2, striker_id=mm_players[0].player_id, non_striker_id=mm_players[2].player_id, bowler_id=dd_players[7].player_id, runs_scored=6, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=13, over_no=16, ball_no=3, striker_id=mm_players[0].player_id, non_striker_id=mm_players[2].player_id, bowler_id=dd_players[7].player_id, runs_scored=1, is_legal=True),
            BallEvent(innings_id=inn_live.innings_id, sequence_no=14, over_no=16, ball_no=4, striker_id=mm_players[2].player_id, non_striker_id=mm_players[0].player_id, bowler_id=dd_players[7].player_id, runs_scored=2, is_legal=True),
        ]
        session.add_all(live_events)
        session.flush()

        # Seed in-memory cache for live match so WebSocket & polling immediately return active state
        from app.services.scoring_service import LIVE_MATCH_CACHE, LiveMatchSession
        from app.services.scoring_engine import InningsState

        state_live = InningsState(
            innings_no=1,
            max_overs=20,
            target_runs=None,
            total_runs=146,
            wickets=3,
            legal_balls=100,  # 16.4 overs
            striker_id=str(mm_players[2].player_id),
            non_striker_id=str(mm_players[0].player_id),
            current_bowler_id=str(dd_players[7].player_id),
            recent_balls=["1", "4", "0", "6", "1", "2"],
        )
        LIVE_MATCH_CACHE[m_live.match_id] = LiveMatchSession(
            match_id=m_live.match_id,
            team1_xi=[p.player_id for p in mm_players[:11]],
            team2_xi=[p.player_id for p in dd_players[:11]],
            batting_team_id=teams[0].team_id,
            bowling_team_id=teams[1].team_id,
            current_innings_id=inn_live.innings_id,
            current_innings_no=1,
            innings_state=state_live,
            current_over_bowler_id=dd_players[7].player_id,
        )

        # Match 2: COMPLETED match (Bangalore Blasters vs Chennai Champions)
        m_comp1 = Match(
            tournament_id=t1.tournament_id,
            team1_id=teams[2].team_id,  # BB
            team2_id=teams[3].team_id,  # CC
            venue_id=venues[2].venue_id,  # Chinnaswamy
            scorer_id=scorer_2.user_id,
            match_date=now_utc - timedelta(days=2),
            overs=20,
            status=MatchStatus.COMPLETED,
            toss_winner_id=teams[3].team_id,
            toss_decision=TossDecision.BOWL,
            winner_id=teams[2].team_id,
            result_summary="Bangalore Blasters won by 23 runs",
        )
        session.add(m_comp1)
        session.flush()

        inn1_c1 = Innings(
            match_id=m_comp1.match_id,
            batting_team_id=teams[2].team_id,
            bowling_team_id=teams[3].team_id,
            innings_no=1,
            total_runs=185,
            wickets=6,
            balls_bowled=120,
            is_completed=True,
            target_runs=None,
        )
        inn2_c1 = Innings(
            match_id=m_comp1.match_id,
            batting_team_id=teams[3].team_id,
            bowling_team_id=teams[2].team_id,
            innings_no=2,
            total_runs=162,
            wickets=8,
            balls_bowled=120,
            is_completed=True,
            target_runs=186,
        )
        session.add_all([inn1_c1, inn2_c1])
        session.flush()

        # Add sample ball events for completed match scorecards
        bb_players = created_players_by_team["BB"]
        cc_players = created_players_by_team["CC"]
        session.add_all([
            BallEvent(innings_id=inn1_c1.innings_id, sequence_no=1, over_no=0, ball_no=1, striker_id=bb_players[1].player_id, non_striker_id=bb_players[0].player_id, bowler_id=cc_players[7].player_id, runs_scored=4, is_legal=True),
            BallEvent(innings_id=inn1_c1.innings_id, sequence_no=2, over_no=0, ball_no=2, striker_id=bb_players[1].player_id, non_striker_id=bb_players[0].player_id, bowler_id=cc_players[7].player_id, runs_scored=6, is_legal=True),
            BallEvent(innings_id=inn1_c1.innings_id, sequence_no=3, over_no=19, ball_no=6, striker_id=bb_players[1].player_id, non_striker_id=bb_players[2].player_id, bowler_id=cc_players[8].player_id, runs_scored=4, is_legal=True),
            BallEvent(innings_id=inn2_c1.innings_id, sequence_no=1, over_no=0, ball_no=1, striker_id=cc_players[0].player_id, non_striker_id=cc_players[1].player_id, bowler_id=bb_players[7].player_id, runs_scored=1, is_legal=True),
            BallEvent(innings_id=inn2_c1.innings_id, sequence_no=2, over_no=19, ball_no=6, striker_id=cc_players[5].player_id, non_striker_id=cc_players[4].player_id, bowler_id=bb_players[8].player_id, runs_scored=2, is_legal=True),
        ])
        session.flush()

        # Match 3: COMPLETED match (Chennai Champions vs Mumbai Masters)
        m_comp2 = Match(
            tournament_id=t1.tournament_id,
            team1_id=teams[3].team_id,  # CC
            team2_id=teams[0].team_id,  # MM
            venue_id=venues[0].venue_id,  # Wankhede
            scorer_id=scorer_1.user_id,
            match_date=now_utc - timedelta(days=4),
            overs=20,
            status=MatchStatus.COMPLETED,
            toss_winner_id=teams[3].team_id,
            toss_decision=TossDecision.BOWL,
            winner_id=teams[3].team_id,
            result_summary="Chennai Champions won by 4 wickets",
        )
        session.add(m_comp2)
        session.flush()

        inn1_c2 = Innings(
            match_id=m_comp2.match_id,
            batting_team_id=teams[0].team_id,
            bowling_team_id=teams[3].team_id,
            innings_no=1,
            total_runs=172,
            wickets=5,
            balls_bowled=120,
            is_completed=True,
            target_runs=None,
        )
        inn2_c2 = Innings(
            match_id=m_comp2.match_id,
            batting_team_id=teams[3].team_id,
            bowling_team_id=teams[0].team_id,
            innings_no=2,
            total_runs=175,
            wickets=6,
            balls_bowled=116,  # 19.2 overs
            is_completed=True,
            target_runs=173,
        )
        session.add_all([inn1_c2, inn2_c2])
        session.flush()

        # Match 4 & 5: SCHEDULED matches
        m_sched1 = Match(
            tournament_id=t1.tournament_id,
            team1_id=teams[1].team_id,  # DD
            team2_id=teams[2].team_id,  # BB
            venue_id=venues[1].venue_id,  # Arun Jaitley
            scorer_id=scorer_2.user_id,
            match_date=now_utc + timedelta(days=1, hours=19),
            overs=20,
            status=MatchStatus.SCHEDULED,
        )
        m_sched2 = Match(
            tournament_id=t1.tournament_id,
            team1_id=teams[0].team_id,  # MM
            team2_id=teams[2].team_id,  # BB
            venue_id=venues[0].venue_id,  # Wankhede
            scorer_id=scorer_1.user_id,
            match_date=now_utc + timedelta(days=3, hours=19, minutes=30),
            overs=20,
            status=MatchStatus.SCHEDULED,
        )
        session.add_all([m_sched1, m_sched2])
        session.flush()

        # 7. Seed Points Table with realistic points & NRR
        pt_entries = [
            # Bangalore Blasters (1 win, 0 loss): +1.150 NRR, 2 pts
            PointsTable(tournament_id=t1.tournament_id, team_id=teams[2].team_id, played=1, won=1, lost=0, tied=0, nr=0, points=2),
            # Chennai Champions (1 win, 1 loss): +0.075 NRR, 2 pts
            PointsTable(tournament_id=t1.tournament_id, team_id=teams[3].team_id, played=2, won=1, lost=1, tied=0, nr=0, points=2),
            # Mumbai Masters (0 win, 1 loss): -0.150 NRR, 0 pts
            PointsTable(tournament_id=t1.tournament_id, team_id=teams[0].team_id, played=1, won=0, lost=1, tied=0, nr=0, points=0),
            # Delhi Dynamos (0 played): 0.000 NRR, 0 pts
            PointsTable(tournament_id=t1.tournament_id, team_id=teams[1].team_id, played=0, won=0, lost=0, tied=0, nr=0, points=0),
            # For Tournament 2:
            PointsTable(tournament_id=t2.tournament_id, team_id=teams[0].team_id, played=0, won=0, lost=0, tied=0, nr=0, points=0),
            PointsTable(tournament_id=t2.tournament_id, team_id=teams[1].team_id, played=0, won=0, lost=0, tied=0, nr=0, points=0),
            PointsTable(tournament_id=t2.tournament_id, team_id=teams[2].team_id, played=0, won=0, lost=0, tied=0, nr=0, points=0),
            PointsTable(tournament_id=t2.tournament_id, team_id=teams[3].team_id, played=0, won=0, lost=0, tied=0, nr=0, points=0),
        ]
        session.add_all(pt_entries)
        session.commit()
        print("Successfully committed all matches, scorecards, and points table!")
        print("\nSeed Data Summary:")
        print(f"• LIVE Match ID: {m_live.match_id} (Mumbai Masters vs Delhi Dynamos)")
        print(f"• COMPLETED Match ID 1: {m_comp1.match_id} (Bangalore Blasters vs Chennai Champions)")
        print(f"• COMPLETED Match ID 2: {m_comp2.match_id} (Chennai Champions vs Mumbai Masters)")
        print(f"• SCHEDULED Match IDs: {m_sched1.match_id}, {m_sched2.match_id}")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
