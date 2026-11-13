# CDMS Cloud Deployment Guide

Complete step-by-step production deployment instructions for the **Cricket Data Management System (CDMS)**.

- **Backend & Database:** [Render](https://render.com) or [Railway](https://railway.app) (FastAPI + Managed PostgreSQL 16)
- **Frontend:** [Vercel](https://vercel.com) (React 18 + Vite SPA)
- **Protocol:** HTTPS (`https://`) and Secure WebSockets (`wss://`)

---

## 1. Managed PostgreSQL Setup

### Option A: Render Managed PostgreSQL
1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\to$ **PostgreSQL**.
3. Configure the database:
   - **Name:** `cdms-postgres`
   - **Database:** `cdms_db`
   - **User:** `cdms_user`
   - **Region:** Pick the region closest to your target audience (e.g. `Frankfurt`, `Oregon`, `Singapore`).
   - **Plan:** Free or Starter.
4. Click **Create Database**.
5. Once provisioned, copy the **Internal Database URL** (if deploying backend on Render) or **External Database URL**.
   *(Note: CDMS automatically converts `postgres://` or `postgresql://` URIs to `postgresql+psycopg2://` at runtime).*

### Option B: Railway PostgreSQL
1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** $\to$ **Provision PostgreSQL**.
3. Railway immediately provides a high-performance managed Postgres container. Under the **Connect** tab, copy the `DATABASE_URL`.

---

## 2. Backend Deployment (FastAPI on Render or Railway)

### Deploying on Render
1. In the Render Dashboard, click **New +** $\to$ **Web Service**.
2. Connect your GitHub repository (`Madhur-Dodake/CDMS`) and select the `main` or `dev` branch.
3. Configure the service settings:
   - **Name:** `cdms-backend`
   - **Region:** Same region as your PostgreSQL instance.
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && alembic upgrade head && python scripts/seed.py
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
4. Add **Environment Variables**:
   | Key | Value / Source |
   | :--- | :--- |
   | `DATABASE_URL` | *Paste Render PostgreSQL Internal Database URL* |
   | `JWT_SECRET_KEY` | *Generate a strong 64-char random hex string* |
   | `JWT_ALGORITHM` | `HS256` |
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `False` |
   | `BACKEND_CORS_ORIGINS` | `https://your-frontend.vercel.app,http://localhost:5173` |
5. Click **Create Web Service**.
6. Verify deployment by checking:
   `https://cdms-backend.onrender.com/health` (should return `{"status": "ok", "environment": "production"}`).

---

## 3. Frontend Deployment (React + Vite on Vercel)

1. Log in to the [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\to$ **Project**.
3. Select your repository `Madhur-Dodake/CDMS`.
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and choose `frontend`.
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Configure **Environment Variables**:
   | Variable | Value | Purpose |
   | :--- | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://cdms-backend.onrender.com` | Base URL for REST API calls |
   | `VITE_WS_BASE_URL` | `wss://cdms-backend.onrender.com` | Base URL for secure WebSocket streams |
6. Click **Deploy**.
7. Vercel automatically deploys the frontend and reads `frontend/vercel.json` to handle client-side Single Page Application (SPA) routing rewrites.

---

## 4. WebSocket (`wss://`) Production Notes

Real-time ball-by-ball delivery updates rely on native FastAPI WebSockets mounted at:
`/ws/matches/{match_id}`

When running behind cloud reverse proxies (Render, Cloudflare, Nginx, Railway), follow these critical production rules:

### 1. Secure Protocol (`wss://`)
Browsers require `wss://` whenever the parent page is served over `https://`. Connecting via unencrypted `ws://` on an HTTPS origin will trigger a `Mixed Content` security block.
```javascript
// In frontend/src/services/api.js:
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ||
  (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;
```

### 2. Reverse Proxy Connection Upgrading
If deploying your own Nginx or Traefik reverse proxy in front of uvicorn, HTTP headers must explicitly upgrade the TCP socket:
```nginx
location /ws/ {
    proxy_pass http://backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
}
```

### 3. Idle Timeout & Heartbeat Keepalives
Most cloud proxies (including Render free instances and AWS ALB) terminate idle TCP sockets after 60 to 100 seconds of inactivity.
- **Client Heartbeat:** The frontend `useMatchSocket` hook sends a lightweight `"ping"` frame every 25 seconds.
- **Server Keepalive:** The backend WebSocket loop responds with `"pong"` and purges disconnected connections.
- **Fallback Polling:** If the WebSocket fails to establish or disconnects due to network instability, `useMatchSocket` falls back to HTTP polling (`/api/scoring/matches/{id}/state`) every 5 seconds.
