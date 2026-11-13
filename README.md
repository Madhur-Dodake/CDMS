# Cricket Data Management System (CDMS)

[![CI](https://github.com/Madhur-Dodake/CDMS/actions/workflows/ci.yml/badge.svg)](https://github.com/Madhur-Dodake/CDMS/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Pytest](https://img.shields.io/badge/Testing-Pytest%20233%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://pytest.org)

> A modern, ad-free, lightweight cricket tournament operations, real-time live scoring, and career statistics tracking platform built for colleges, clubs, and regional cricket leagues.

---

## 1. Project Overview & Key Features

Existing cricket scoring portals (e.g. Cricbuzz, ESPNcricinfo) are ad-heavy, commercialized, and lack operational tooling for grassroots organizers. **CDMS** provides an end-to-end operational suite:

- **3-Tier Role-Based Access Control (RBAC):**
  - **Administrator:** Manage tournaments, venues, teams, rosters, generate round-robin schedules, assign match scorers, and manage user roles.
  - **Match Scorer:** Operational live match scoring wizard, toss details, playing XI confirmation, 0-6 run pad, extras picker, wicket modal, strike rotation, and ball undo.
  - **Public Viewer:** Zero-login access to live ball-by-ball scorecards, match wagon ribbons, tournament standings/points table with live Net Run Rate (NRR), and player career profiles.
- **Sub-Second Native WebSockets:** Real-time push stream (`/ws/matches/{match_id}`) delivering instant score updates with auto-reconnecting client and fallback polling.
- **Pure Functional Domain Engines:**
  - Scoring logic, extras handling, and strike rotation are **100% pure functions** with zero database coupling.
  - Net Run Rate (NRR) calculator handles partial overs, division guards, and all-out quota caps.
- **Deterministic Replay-Based Undo:** Undoing an erroneous delivery deletes the event and reconstructs match state from ball zero without compounding corruption.
- **Production Hardened:** OWASP security headers, in-memory login rate limiting, request logging, global exception handling, and input sanitization.

---

## 2. Visual Walkthrough & Screenshots

```
+-----------------------------------------------------------------------------------+
|  [SCREENSHOT PLACEHOLDER 1: HERO & PUBLIC PORTAL]                                 |
|  Dark Hero Header (#0f172a), Emerald Accent (#10b981), Live Match Ribbon         |
|  `docs/screenshots/01_home_public_portal.png`                                     |
+-----------------------------------------------------------------------------------+
```

```
+-----------------------------------------------------------------------------------+
|  [SCREENSHOT PLACEHOLDER 2: LIVE SCORECARD & BALL-BY-BALL RIBBON]                 |
|  Live Score 146/3 (14.2 Ov), CRR/RRR, Batter/Bowler figures, WebSocket ticker    |
|  `docs/screenshots/02_live_scorecard.png`                                        |
+-----------------------------------------------------------------------------------+
```

```
+-----------------------------------------------------------------------------------+
|  [SCREENSHOT PLACEHOLDER 3: SCORER'S LIVE MATCH CONSOLE]                         |
|  0-6 Run Pad, Wides/No-Balls/Byes, Wicket Modal, Undo Delivery, Bowler Rotation   |
|  `docs/screenshots/03_scorer_console.png`                                         |
+-----------------------------------------------------------------------------------+
```

```
+-----------------------------------------------------------------------------------+
|  [SCREENSHOT PLACEHOLDER 4: ADMIN DASHBOARD & FIXTURE SCHEDULER]                 |
|  Metric cards, Tournament standings with NRR, Round-Robin Schedule Generator      |
|  `docs/screenshots/04_admin_dashboard.png`                                        |
+-----------------------------------------------------------------------------------+
```

---

## 3. Tech Stack Architecture

```
                                  +-----------------------+
                                  |   React 18 + Vite     |
                                  |   (Tailwind CSS)      |
                                  +-----------+-----------+
                                              |
                          HTTP REST API / JWT | Native WebSocket (wss://)
                                              v
+-----------------------------------------------------------------------------------+
| FastAPI Application Layer (backend/app/)                                          |
|                                                                                   |
|  [Middlewares]                                                                    |
|  • SecurityHeadersMiddleware (HSTS, nosniff, DENY, XSS)                           |
|  • RequestLoggingMiddleware (method, path, latency ms)                            |
|  • CORSMiddleware (whitelisted origins)                                           |
|  • InMemoryRateLimiter (10 req/min on /api/auth/login)                            |
|                                                                                   |
|  [API Routers]                                                                    |
|  • /api/auth    • /api/matches   • /api/tournaments   • /api/teams                |
|  • /api/scoring • /api/players   • /api/venues        • /api/dashboard            |
|                                                                                   |
|  [Pure Domain Engines (V(G) <= 5)]                                                |
|  • scoring_engine.py   • nrr_calculator.py   • stats_engine.py                    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | SQLAlchemy 2.0 ORM
                                          v
                               +---------------------+
                               | PostgreSQL 16 (DB)  |
                               +---------------------+
```

---

## 4. Getting Started & Local Setup

### Option A: Complete Docker Compose (Recommended)

Run the full stack (Database, FastAPI Backend, and Nginx-served Frontend) with a single command:

```bash
docker compose up --build -d
```

Once started:
- **Frontend App:** [http://localhost:5173](http://localhost:5173) (or [http://localhost](http://localhost))
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **PostgreSQL Port:** `localhost:5432`

---

### Option B: Manual Local Development

#### Prerequisites
- **Python 3.11+**
- **Node.js 18+ & npm**
- **PostgreSQL 16**

#### 1. Database Setup
Ensure PostgreSQL is running locally and create the database:
```sql
CREATE USER cdms_user WITH PASSWORD 'cdms_password';
CREATE DATABASE cdms_db OWNER cdms_user;
```

#### 2. Backend Setup
```bash
cd backend

# Create & activate virtual environment
python -m venv venv
# On Windows: .\venv\Scripts\Activate.ps1
# On macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed initial tournament, team, player, and live match data
python scripts/seed.py

# Launch development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 3. Frontend Setup
```bash
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev
```

Visit `http://localhost:5173` to access the application.

---

## 5. Default Seed Accounts

The seed script creates initial demonstration accounts:

| Role | Email | Password | Access Area |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@cdms.com` | `admin123` | Full Admin Console (`/admin/*`) |
| **Match Scorer** | `scorer@cdms.com` | `scorer123` | Match Scoring Console (`/admin/scoring/*`) |
| **Public Viewer** | `viewer@cdms.com` | `viewer123` | Public Viewer Pages (`/*`) |

---

## 6. Testing & Quality Assurance

CDMS enforces comprehensive automated testing with **246 total tests**:

### Backend Tests (233 Tests)
Run pytest with branch coverage:
```bash
cd backend
pytest -v --cov=app --cov-branch
```

#### Basis Path Test Breakdown (Academic Report Section 9):
All tested domain functions enforce McCabe Cyclomatic Complexity $V(G) = E - N + 2 \le 5$:
- `auth`: **18 tests** (100% branch coverage)
- `nrr_calculator`: **11 tests** (96% branch coverage)
- `stats_engine`: **11 tests** (100% branch coverage)
- `connection_manager`: **8 tests** (84% branch coverage)
- `scoring logic`: **41 tests** (95% branch coverage)
- **Total Basis Path Suite:** **89 tests** with **93.5%** core branch coverage.

### Frontend Tests (13 Tests)
Run component, store, and routing tests:
```bash
cd frontend
npm test
```

---

## 7. Automated Database Backups

Nightly database backups with rolling 7-day retention:

- **Linux / macOS (Bash):**
  ```bash
  chmod +x scripts/backup_db.sh
  ./scripts/backup_db.sh
  ```
- **Windows / Cross-Platform (Python):**
  ```bash
  python scripts/backup_db.py
  ```

Backups are saved to `backups/cdms_backup_YYYYMMDD_HHMMSS.sql.gz`.

---

## 8. Continuous Integration (CI)

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main` and `dev`:
- Spins up a dedicated PostgreSQL 16 service container.
- Executes backend migrations and the complete 233-test Pytest suite with branch coverage.
- Installs Node dependencies, executes frontend tests, and compiles the production Vite bundle.
