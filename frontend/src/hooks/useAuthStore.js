// hooks/useAuthStore.js
import { create } from 'zustand';
import { authService } from '../services/authService';
import { ROLE_DEFAULT_ROUTE } from '../constants/roles';

const useAuthStore = create((set, get) => ({
  user:        null,
  isLoading:   false,
  isLoggedIn:  false,
  error:       null,

  // ── Login ──────────────────────────────────────────────────────────────
  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authService.login(credentials);
      set({ user: data.user, isLoggedIn: true, isLoading: false });
      return ROLE_DEFAULT_ROUTE[data.user.role] || '/farmer/dashboard';
    } catch (err) {
      const msg = err.response?.data?.message || 'Login failed. Please try again.';
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  // ── Register ───────────────────────────────────────────────────────────
  register: async (formData) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authService.register(formData);
      set({ user: data.user, isLoggedIn: true, isLoading: false });
      return ROLE_DEFAULT_ROUTE[data.user.role] || '/farmer/dashboard';
    } catch (err) {
      const msg = err.response?.data?.message || 'Registration failed. Please try again.';
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  // ── Logout ─────────────────────────────────────────────────────────────
  logout: async () => {
    try { await authService.logout(); } catch (_) {}
    set({ user: null, isLoggedIn: false, error: null });
  },

  // ── Restore session on app load ────────────────────────────────────────
  restoreSession: async () => {
    const token = localStorage.getItem('kv_access_token');
    if (!token) return;
    set({ isLoading: true });
    try {
      const data = await authService.getMe();
      set({ user: data.user, isLoggedIn: true, isLoading: false });
    } catch {
      localStorage.removeItem('kv_access_token');
      set({ isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
