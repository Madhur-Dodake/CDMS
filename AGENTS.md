# AGENTS.md

Instructions, conventions, architectural patterns, and guidelines for AI agents working in this repository.

---

## 1. Project Overview & Tech Stack
- **Project**: Cricket Data Management System (CDMS)
- **Domain**: Comprehensive cricket tournament, match operations, live scoring, and statistics tracking system.
- **Specification**: Complete academic project specification documented in `docs/spec.md`.

### Core Tech Stack
- **Backend Framework**: **FastAPI** (Python 3.11+)
- **ORM & Database**: **SQLAlchemy 2.0** with **PostgreSQL**
- **Database Migrations**: **Alembic**
- **Configuration & Validation**: **Pydantic v2** (`BaseModel`) and **pydantic-settings** (`BaseSettings` reading from `.env`)
- **Real-Time Communication**: **FastAPI Native WebSockets** (lightweight in-memory connection manager for ball-by-ball broadcasts)
- **Testing**: **Pytest** (unit tests for pure domain functions, API client integration tests)
- **Frontend**: **React** (v18+) with **Vite**, **Tailwind CSS**, **React Router** (v6), and **Axios**
- **Infrastructure**: **Docker Compose** exclusively for local PostgreSQL

---

## 2. Role Model & Access Control (RBAC)

The system enforces three primary user roles:

1. **`admin` (Administrator)**
   - Manages tournaments, teams, venues, and player rosters.
   - Schedules fixtures and assigns authorized scorers to matches.
   - Manages user accounts and promotes user privileges.

2. **`scorer` (Match Scorer)**
   - Authenticated operational user assigned to a match.
   - Records toss details and confirms playing XIs.
   - Enters ball-by-ball events (runs, extras, wickets, dismissals, strike rotation).
   - Can undo erroneous deliveries (delete last ball and replay).
   - Concludes innings and declares official match results.

3. **`viewer` (Public / Viewer)**
   - Public, unauthenticated audience.
   - Accesses real-time live scorecards, ball-by-ball commentary, tournament schedules, team/player statistics, and points tables.

---

## 3. Coding Conventions & Architecture

### Backend Architecture
- **Layered Separation of Concerns**:
  - `backend/app/api/`: Thin HTTP and WebSocket routers. Routers only parse requests, invoke service methods, and return Pydantic schemas. **No direct business logic in routers.**
  - `backend/app/services/`: Services layer holding application workflows, database transactions, coordination, and WebSocket notifications.
  - `backend/app/models/`: SQLAlchemy 2.0 declarative database models with typed attributes.
  - `backend/app/schemas/`: Pydantic v2 schemas (`from_attributes = True`) for request payloads and response contracts.
  - `backend/app/core/`: Configuration (`pydantic-settings`), database engine/session setup, security, and global constants.
  - `backend/app/ws/`: Native WebSocket connection manager and event broadcasters.

### Pure Domain Logic Requirement
- **Scoring Engine, Net Run Rate (NRR) Calculator, and Stats Aggregations MUST be PURE FUNCTIONS.**
- Pure functions take inputs and return outputs with **zero database access, zero network calls, and zero external side effects**.
- This enables deterministic testing, rapid execution in `pytest`, and reliable replay capabilities.

### Coding Standards
- **Strict Type Hints**: Full typing across all Python functions, parameters, and return signatures.
- **Pydantic v2 Validation**: Use `model_config = ConfigDict(from_attributes=True)` and strict field validations.
- **Error Handling**: Use semantic `HTTPException` with clear error detail strings.

---

## 4. Key Architectural & Domain Decisions

1. **Integer Ball Storage**:
   - Overs are stored internally and computed as **integer balls** (e.g., 20 overs = 120 balls; 19.4 overs = 118 balls).
   - Conversion to cricket over notation (e.g. `balls // 6` + `.` + `balls % 6`) is strictly a presentation-layer helper. Never store overs as floats in the database to avoid rounding errors.

2. **FastAPI Native WebSockets**:
   - Native WebSockets handle real-time ball-by-ball broadcast streams (`/ws/matches/{match_id}`).
   - Avoid external message broker dependencies (e.g. Redis) for baseline operations.

3. **Undo Delivery Mechanic**:
   - Undo is implemented as: **delete the last recorded ball event and deterministically replay the innings from ball zero** to reconstruct score, batter/bowler figures, and strike state.

4. **Points System & NRR**:
   - Match points: **2 points for Win, 1 point for Tie / No Result / Abandoned, 0 points for Loss**.
   - Net Run Rate formula:
     $$\text{NRR} = \left( \frac{\text{Runs Scored}}{\text{Overs Faced}} \right) - \left( \frac{\text{Runs Conceded}}{\text{Overs Bowled}} \right)$$
     *(If a team is bowled out, overs faced is considered the full allocated quota of overs for the innings).*

---

## 5. Branch & Git Strategy
- **`main`**: Protected, stable production branch. Never commit directly to `main`. Merges into `main` occur only at the end of completed, verified project phases.
- **`dev`**: Default daily working branch. All active development, feature implementations, and incremental commits must be targeted to `dev`.
- **Commit Messages**: Follow conventional commits format (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`).

---

## 6. Environment & Security
- Never commit secrets, credentials, or `.env` files.
- Keep environment templates documented in `.env.example`.
- Ensure all virtual environments (`venv`, `.venv`) and frontend build artifacts (`node_modules`, `dist`, `.vite`) remain ignored by Git.
