// constants/routes.js
export const ROUTES = {
  // Public
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',

  // Farmer
  FARMER_DASHBOARD: '/farmer/dashboard',
  FARMER_CROPS: '/farmer/crops',
  FARMER_DISEASE: '/farmer/disease-detection',
  FARMER_CROP_RECOMMENDATION: '/farmer/crop-recommendation',
  FARMER_WEATHER: '/farmer/weather',
  FARMER_MARKET: '/farmer/market',
  FARMER_IRRIGATION: '/farmer/irrigation',
  FARMER_ANALYTICS: '/farmer/analytics',
  FARMER_AI_ASSISTANT: '/farmer/ai-assistant',

  // Expert
  EXPERT_DASHBOARD: '/expert/dashboard',
  EXPERT_QUERIES: '/expert/queries',
  EXPERT_DISEASE_CASES: '/expert/disease-cases',
  EXPERT_ADVISORIES: '/expert/advisories',

  // Admin
  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_USERS: '/admin/users',
  ADMIN_EXPERTS: '/admin/experts',
  ADMIN_ANALYTICS: '/admin/analytics',

  // Fallback
  NOT_FOUND: '*',
};
