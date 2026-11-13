import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Inject Bearer JWT token if user is authenticated
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 Unauthorized (expired or revoked token)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const currentPath = window.location.pathname;
      if (currentPath !== '/login') {
        useAuthStore.getState().logout();
        window.location.href = `/login?from=${encodeURIComponent(currentPath)}`;
      }
    }
    return Promise.reject(error);
  }
);

// Auth Service
export const authService = {
  login: async (email, password, role) => {
    const res = await apiClient.post('/api/auth/login', { email, password, role });
    return res.data;
  },
  getCurrentUser: async () => {
    const res = await apiClient.get('/api/auth/me');
    return res.data;
  },
};

// Dashboard Service
export const dashboardService = {
  getSummary: async () => {
    const res = await apiClient.get('/api/dashboard/summary');
    return res.data;
  },
};

// Matches & Live Scoring Service
export const matchesService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/matches', { params });
    return res.data;
  },
  getById: async (matchId) => {
    const res = await apiClient.get(`/api/matches/${matchId}`);
    return res.data;
  },
  getLiveState: async (matchId) => {
    const res = await apiClient.get(`/api/matches/${matchId}/live`);
    return res.data;
  },
  getScorecard: async (matchId) => {
    const res = await apiClient.get(`/api/matches/${matchId}/scorecard`);
    return res.data;
  },
  schedule: async (data) => {
    const res = await apiClient.post('/api/matches', data);
    return res.data;
  },
  transition: async (matchId, event) => {
    const res = await apiClient.post(`/api/matches/${matchId}/transition`, { event });
    return res.data;
  },
};

// Scoring Service
export const scoringService = {
  startMatch: async (matchId, payload) => {
    const res = await apiClient.post(`/api/matches/${matchId}/start`, payload);
    return res.data;
  },
  recordBall: async (matchId, payload) => {
    const res = await apiClient.post(`/api/matches/${matchId}/ball`, payload);
    return res.data;
  },
  undoBall: async (matchId) => {
    const res = await apiClient.post(`/api/matches/${matchId}/undo`);
    return res.data;
  },
  endInnings: async (matchId) => {
    const res = await apiClient.post(`/api/matches/${matchId}/end-innings`);
    return res.data;
  },
  completeMatch: async (matchId) => {
    const res = await apiClient.post(`/api/matches/${matchId}/complete`);
    return res.data;
  },
  suspendMatch: async (matchId) => {
    const res = await apiClient.post(`/api/matches/${matchId}/suspend`);
    return res.data;
  },
  resumeMatch: async (matchId) => {
    const res = await apiClient.post(`/api/matches/${matchId}/resume`);
    return res.data;
  },
};

// Tournaments Service
export const tournamentsService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/tournaments', { params });
    return res.data;
  },
  getById: async (tournamentId) => {
    const res = await apiClient.get(`/api/tournaments/${tournamentId}`);
    return res.data;
  },
  create: async (data) => {
    const res = await apiClient.post('/api/tournaments', data);
    return res.data;
  },
  update: async (tournamentId, data) => {
    const res = await apiClient.put(`/api/tournaments/${tournamentId}`, data);
    return res.data;
  },
  delete: async (tournamentId) => {
    const res = await apiClient.delete(`/api/tournaments/${tournamentId}`);
    return res.data;
  },
  getPointsTable: async (tournamentId) => {
    const res = await apiClient.get(`/api/tournaments/${tournamentId}/points-table`);
    return res.data;
  },
  getTeams: async (tournamentId) => {
    const res = await apiClient.get(`/api/tournaments/${tournamentId}/teams`);
    return res.data;
  },
  getFixtures: async (tournamentId) => {
    const res = await apiClient.get('/api/matches', { params: { tournament_id: tournamentId, page_size: 50 } });
    return res.data;
  },
  generateSchedule: async (tournamentId) => {
    const res = await apiClient.post(`/api/tournaments/${tournamentId}/generate-schedule`);
    return res.data;
  },
};

// Teams Service
export const teamsService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/teams', { params });
    return res.data;
  },
  getById: async (teamId) => {
    const res = await apiClient.get(`/api/teams/${teamId}`);
    return res.data;
  },
  create: async (data) => {
    const res = await apiClient.post('/api/teams', data);
    return res.data;
  },
  update: async (teamId, data) => {
    const res = await apiClient.put(`/api/teams/${teamId}`, data);
    return res.data;
  },
  delete: async (teamId) => {
    const res = await apiClient.delete(`/api/teams/${teamId}`);
    return res.data;
  },
  getRoster: async (teamId) => {
    const res = await apiClient.get('/api/players', { params: { team_id: teamId, page_size: 50 } });
    return res.data;
  },
};

// Players Service
export const playersService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/players', { params });
    return res.data;
  },
  getById: async (playerId) => {
    const res = await apiClient.get(`/api/players/${playerId}`);
    return res.data;
  },
  create: async (data) => {
    const res = await apiClient.post('/api/players', data);
    return res.data;
  },
  update: async (playerId, data) => {
    const res = await apiClient.put(`/api/players/${playerId}`, data);
    return res.data;
  },
  delete: async (playerId) => {
    const res = await apiClient.delete(`/api/players/${playerId}`);
    return res.data;
  },
  getStats: async (playerId) => {
    const res = await apiClient.get(`/api/players/${playerId}/stats`);
    return res.data;
  },
};

// Venues Service
export const venuesService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/venues', { params });
    return res.data;
  },
  getById: async (venueId) => {
    const res = await apiClient.get(`/api/venues/${venueId}`);
    return res.data;
  },
  create: async (data) => {
    const res = await apiClient.post('/api/venues', data);
    return res.data;
  },
  update: async (venueId, data) => {
    const res = await apiClient.put(`/api/venues/${venueId}`, data);
    return res.data;
  },
  delete: async (venueId) => {
    const res = await apiClient.delete(`/api/venues/${venueId}`);
    return res.data;
  },
};

// Users Service (Admin only)
export const usersService = {
  list: async (params = {}) => {
    const res = await apiClient.get('/api/users', { params });
    return res.data;
  },
  getById: async (userId) => {
    const res = await apiClient.get(`/api/users/${userId}`);
    return res.data;
  },
  create: async (data) => {
    const res = await apiClient.post('/api/users', data);
    return res.data;
  },
  update: async (userId, data) => {
    const res = await apiClient.put(`/api/users/${userId}`, data);
    return res.data;
  },
  delete: async (userId) => {
    const res = await apiClient.delete(`/api/users/${userId}`);
    return res.data;
  },
};

export default apiClient;
