import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      role: null,

      login: (token, user) => {
        set({
          token,
          user,
          isAuthenticated: true,
          role: user?.role || 'viewer',
        });
      },

      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          role: null,
        });
      },

      updateUser: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData },
          role: userData.role || state.role,
        }));
      },
    }),
    {
      name: 'cdms-auth',
    }
  )
);

