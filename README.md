# CDMS - Cricket Data Management System

A lightweight, responsive, and ad-free cricket tournament management, real-time live scoring, and statistics tracking system.

---

## 1. Monorepo Architecture

```
CDMS/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # Thin HTTP & WebSocket API routers
│   │   ├── core/             # Configuration (pydantic-settings), database engine
│   │   ├── models/           # SQLAlchemy 2.0 declarative database models
│   │   ├── schemas/          # Pydantic v2 validation schemas
│   │   ├── services/         # Business logic layer (scoring, NRR, stats)
│   │   ├── ws/               # Native WebSocket connection manager
│   │   └── main.py           # FastAPI entrypoint, middleware, root health
│   ├── tests/                # Pytest unit & integration test suite
│   ├── requirements.txt      # Python dependencies
│   ├── pytest.ini            # Test runner configuration
│   └── .env.example          # Environment variables template
│
├── frontend/                 # React 18 + Vite SPA
│   ├── src/
│   │   ├── pages/            # View components (Home, etc.)
│   │   ├── services/         # Axios API client
│   │   ├── App.jsx           # React Router navigation shell
│   │   └── main.jsx          # Vite React entry point
│   ├── package.json          # Node scripts & dependencies
│   ├── tailwind.config.js    # Tailwind CSS styling configuration
│   └── .env.example          # Frontend environment variables template
│
├── docs/
│   └── spec.md               # Complete CDMS project specification & lab report
│
├── docker-compose.yml        # PostgreSQL database service
├── AGENTS.md                 # Agent instructions, architecture rules & conventions
└── README.md                 # Project documentation & run guide
```

---

## 2. Core Architectural Decisions

- **Integer Ball Storage**: All over calculations and database representations store deliveries as integer balls (e.g., 20 overs = 120 balls; 19.4 overs = 118 balls). Over notation (e.g. `19.4`) is strictly for UI display to avoid floating point errors.
- **Pure Function Domain Engine**: Scoring logic, strike rotation, NRR calculation, and player stats are pure functions without DB or network access.
- **Native WebSockets**: FastAPI native WebSocket endpoints broadcast live ball-by-ball score updates without third-party brokers.
- **Delivery Undo**: Undoing a ball deletes the latest event and deterministically replays the active innings from ball zero.
- **Tournament Points**: 2 points for a win, 1 point for a tie / no-result / abandonment, 0 points for a loss.

---

## 3. Getting Started & Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (for PostgreSQL)

---

### Step 1: Start PostgreSQL

Launch the dedicated PostgreSQL database container:

```bash
docker compose up -d
```

The database will be reachable on `localhost:5432` with:
- **Database**: `cdms_db`
- **Username**: `cdms_user`
- **Password**: `cdms_password`

---

### Step 2: Backend Setup & Run

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   # Copy sample environment configuration
   cp .env.example .env
   ```

5. Run test suite:
   ```bash
   pytest
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

- **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 3: Frontend Setup & Run

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)

---

## 4. Branch & Git Strategy

- **`main`**: Protected, stable release branch. Direct commits are restricted. Merges occur only upon completion of verified phases.
- **`dev`**: Default active development branch for daily commits and feature branches.
