// constants/roles.js
export const ROLES = {
  FARMER:              'FARMER',
  AGRICULTURAL_EXPERT: 'AGRICULTURAL_EXPERT',
  ADMIN:               'ADMIN',
};

export const ROLE_LABELS = {
  FARMER:              'Farmer / किसान',
  AGRICULTURAL_EXPERT: 'Agricultural Expert / कृषि विशेषज्ञ',
  ADMIN:               'Admin / प्रशासक',
};

// Which role goes to which dashboard after login
export const ROLE_DEFAULT_ROUTE = {
  FARMER:              '/farmer/dashboard',
  AGRICULTURAL_EXPERT: '/expert/dashboard',
  ADMIN:               '/admin/dashboard',
};
