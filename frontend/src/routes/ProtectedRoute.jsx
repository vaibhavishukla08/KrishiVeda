// routes/ProtectedRoute.jsx
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../hooks/useAuthStore';

// Usage:
// <ProtectedRoute>                        → any logged-in user
// <ProtectedRoute roles={['FARMER']}>    → only farmers
const ProtectedRoute = ({ children, roles }) => {
  const { isLoggedIn, user, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0f1a0f]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-[#639922] border-t-transparent rounded-full animate-spin" />
          <span className="text-[#639922] font-medium text-sm">Loading KrishiVeda...</span>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (roles && !roles.includes(user?.role)) {
    // Wrong role — redirect to their own dashboard
    const fallback = {
      FARMER:              '/farmer/dashboard',
      AGRICULTURAL_EXPERT: '/expert/dashboard',
      ADMIN:               '/admin/dashboard',
    }[user?.role] || '/login';
    return <Navigate to={fallback} replace />;
  }

  return children;
};

export default ProtectedRoute;
