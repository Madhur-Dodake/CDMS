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

// Auth Service Helpers
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

export default apiClient;
