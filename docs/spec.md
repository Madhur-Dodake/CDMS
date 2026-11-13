# Cricket Data Management System (CDMS) - Project Specification

> Academic Software Engineering Project Report Specification  
> **Course:** Software Engineering Lab (Sem 5, T.Y. B.Tech IT, VJTI Mumbai)  
> **Project:** Cricket Data Management System (CDMS)  
> **Authors:** Pranav Deshmukh, Ninad Dhote, Madhur Dodake, Nathan Julian Dsouza  
> **Advisor:** Mrs. P. M. Chawan  

---

## 1. Executive Summary & Problem Statement

### 1.1 Problem Definition
Currently, cricket enthusiasts, local tournament organizers, and players lack a unified, lightweight, ad-free platform to manage and track cricket matches. Existing platforms (e.g. Cricbuzz, ESPNcricinfo) are bloated, ad-heavy, closed-ecosystem, and overwhelmingly focused on commercial international cricket. Local, domestic, collegiate, and club tournaments suffer from:
- Fragmented, manual scheduling on paper or spreadsheets.
- Inability to broadcast low-latency live ball-by-ball updates.
- Inaccurate or manual Net Run Rate (NRR) and points table calculations.
- Disconnected player career statistics and match records.

### 1.2 Objectives
1. Provide **role-based workflows** for tournament administrators, match scorers, and public viewers.
2. Deliver **sub-second real-time scoring updates** via native WebSockets.
3. Enforce **pure, deterministic computational engines** for ball-by-ball scoring, strike rotation, NRR calculation, and player statistics without side effects.
4. Support **fault-tolerant scoring operations** with undo/ball-replay mechanics.
5. Provide a responsive, modern frontend with zero visual clutter.

---

## 2. Role Model & Access Control (RBAC)

The system defines three core roles with strict boundaries:

| Role | Access Scope | Key Permissions & Responsibilities |
| :--- | :--- | :--- |
| **Administrator (dmin)** | Protected Admin Portal | • Create and manage tournaments, teams, venues, and players.<br>• Schedule matches and assign verified scorers.<br>• Manage user accounts and elevated roles. |
| **Match Scorer (scorer)** | Scorer Console | • Record toss decisions and playing XI rosters.<br>• Log ball-by-ball events (runs, extras, dismissals, strike rotation).<br>• Undo erroneous deliveries (delete last ball event and replay state).<br>• Conclude innings and declare match outcomes. |
| **Public Viewer (iewer)** | Open Public Pages | • Unauthenticated real-time match tracking.<br>• Ball-by-ball commentary, live wagon/run rate, and scorecards.<br>• Tournament fixtures, standings/points table with live NRR, and player profiles. |

---

## 3. System Architecture & Tech Stack

- **Backend Framework:** FastAPI (Python 3.11+)
- **Database & ORM:** PostgreSQL with SQLAlchemy 2.0 (declarative async/sync mapped models) & Alembic migrations
- **Configuration & Validation:** Pydantic v2 schemas and pydantic-settings (.env management)
- **Real-Time Communication:** Native FastAPI WebSockets (WebSocketEndpoint / broadcast manager)
- **Testing Suite:** pytest with pure unit tests and HTTP test clients
- **Frontend Stack:** React 18+ bootstrapped with Vite, Tailwind CSS, React Router v6, Axios

---

## 4. Key Architectural & Domain Decisions

1. **Integer Ball Storage:**
   - Overs are stored and calculated strictly as total integer legal balls (e.g., 1 over = 6 balls, 19.4 overs = 118 balls).
   - Display formatting (alls // 6 . balls % 6) is decoupled from storage and computation to eliminate floating-point rounding errors.

2. **Pure Domain Logic (Zero DB Coupling):**
   - Scoring logic, strike rotation, extras evaluation, Net Run Rate (NRR), and player statistical aggregations are written as **pure, side-effect-free functions**.
   - Input: Current state + Ball event / Match data -> Output: New state.
   - Database operations, persistence, and WebSocket broadcasting reside strictly in service coordinators.

3. **Undo Mechanics (Event Sourcing Replay):**
   - An undo action deletes the most recent all_event record for the active innings and deterministically replays the innings from ball 0 to restore batting, bowling, strike, and extras state.

4. **Tournament Points System:**
   - Standard 2/1/0 rule:
     - **Win:** 2 points
     - **Tie / No Result / Abandoned:** 1 point
     - **Loss:** 0 points
   - Net Run Rate (NRR) determines tiebreakers in group standings:
     \text{NRR} = \left( \frac{\text{Total Runs Scored}}{\text{Total Overs Faced}} \right) - \left( \frac{\text{Total Runs Conceded}}{\text{Total Overs Bowled}} \right)
     *(All-out innings count as full allocated quota of overs).*

---

## 5. Entity Relationship Model & Data Dictionary

### Core Entities:
- **User**: id, 
ame, email, hashed_password, 
ole (dmin, scorer, iewer), created_at.
- **Tournament**: id, 
ame, level (local, club, domestic, international), ormat (T20, ODI, Test, Other), start_date, end_date, created_by.
- **Team**: id, 	eam_name, short_code, city, coach_name, logo_url.
- **Player**: id, 	eam_id, 
ame, dob, atting_style, owling_style, 
ole.
- **Venue**: id, enue_name, city, capacity.
- **Match**: id, 	ournament_id, 	eam1_id, 	eam2_id, enue_id, scorer_id, match_date, overs_allocated, status (scheduled, 	oss, live, innings_break, completed, bandoned), 	oss_winner_id, 	oss_decision, winner_id, 
esult_summary.
- **Innings**: id, match_id, atting_team_id, owling_team_id, innings_number, 	otal_runs, wickets, alls_bowled, is_completed, 	arget_runs.
- **BallEvent**: id, innings_id, over_number, all_number, striker_id, 
on_striker_id, owler_id, 
uns_batter, extras_type (wide, 
o_ball, ye, leg_bye, penalty, 
one), extras_runs, is_wicket, wicket_type, dismissed_player_id, 	imestamp.

---

## 6. Functional Workflows & State Machines

### 6.1 Match State Transition
`
[ Scheduled ]
      │
      ▼ (Toss & Playing XI Recorded)
[ Toss / Ready ]
      │
      ▼ (First ball bowled)
[ Live (Innings 1) ]
      │
      ▼ (All out or overs completed)
[ Innings Break ]
      │
      ▼ (Second innings start)
[ Live (Innings 2) ]
      │
      ▼ (Target chased, all out, or overs finished)
[ Completed ]
`

### 6.2 Scorer Ball Event Processing
1. Scorer inputs ball parameters (runs scored, batter, bowler, extras, wicket).
2. Service validates ball constraints (correct bowler, active batters, valid delivery).
3. Pure scoring function computes new state:
   - Increments runs and deliveries (if legal ball).
   - Handles strike rotation on odd runs (1, 3, 5) and at the completion of each over (6 legal balls).
   - Records dismissals and prompts for next batter.
4. Database commits event and updated innings snapshot in a single atomic transaction.
5. WebSocket connection manager broadcasts updated state payload to all connected clients on /ws/matches/{match_id}.

---

## 7. Quality Assurance & Basis Path Testing
- **Coverage Criteria:** Complete branch coverage on scoring state updates, NRR computations, and role guards.
- **Pure Functions:** Fully isolated unit test suites verifying all boundary conditions:
  - Strike rotation on extras (no balls, wides, overthrows).
  - Net Run Rate when a team is bowled out inside allocated overs.
  - Multi-match standings ordering with equal points and NRR tiebreaker.
