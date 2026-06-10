// services/authService.js
import api from './api';
import { API_ENDPOINTS } from '../constants/api';

export const authService = {
  register: async (data) => {
    const res = await api.post(API_ENDPOINTS.REGISTER, data);
    return res.data;
  },

  login: async ({ email, password }) => {
    const res = await api.post(API_ENDPOINTS.LOGIN, { email, password });
    if (res.data.accessToken) {
      localStorage.setItem('kv_access_token', res.data.accessToken);
    }
    return res.data;
  },

  logout: async () => {
    await api.post(API_ENDPOINTS.LOGOUT);
    localStorage.removeItem('kv_access_token');
  },

  getMe: async () => {
    const res = await api.get(API_ENDPOINTS.ME);
    return res.data;
  },
};
