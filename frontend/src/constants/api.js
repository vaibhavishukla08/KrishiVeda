// constants/api.js
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const API_ENDPOINTS = {
  // Auth
  REGISTER:         '/auth/register',
  LOGIN:            '/auth/login',
  LOGOUT:           '/auth/logout',
  REFRESH_TOKEN:    '/auth/refresh',
  ME:               '/auth/me',

  // Farms & Crops
  FARMS:            '/farms',
  CROPS:            '/crops',

  // AI Services
  CROP_RECOMMEND:   '/ai/crop-recommend',
  DISEASE_DETECT:   '/ai/detect-disease',
  IRRIGATION:       '/ai/irrigation-advice',
  CHAT:             '/ai/chat',

  // Weather
  WEATHER:          '/weather',

  // Market
  MARKET_PRICES:    '/market/prices',
  MARKET_FORECAST:  '/market/forecast',

  // Analytics
  ANALYTICS:        '/analytics/farm',
};