// routes/AppRoutes.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';

// Auth pages
import Login    from '../pages/auth/Login';
import Register from '../pages/auth/Register';

// Farmer pages
import FarmerDashboard        from '../pages/farmer/Dashboard';
import CropRecommendation     from '../pages/farmer/CropRecommendation';
import DiseaseDetection       from '../pages/farmer/DiseaseDetection';
import Weather                from '../pages/farmer/Weather';
import Market                 from '../pages/farmer/Market';
import Irrigation             from '../pages/farmer/Irrigation';
import Analytics              from '../pages/farmer/Analytics';
import AIAssistant            from '../pages/farmer/AIAssistant';

// Expert pages
import ExpertDashboard        from '../pages/expert/Dashboard';

// Admin pages
import AdminDashboard         from '../pages/admin/Dashboard';

// Misc
import NotFound               from '../pages/NotFound';

const FARMER = ['FARMER'];
const EXPERT = ['AGRICULTURAL_EXPERT'];
const ADMIN  = ['ADMIN'];

const AppRoutes = () => (
  <Routes>
    {/* Public */}
    <Route path="/"         element={<Navigate to="/login" replace />} />
    <Route path="/login"    element={<Login />} />
    <Route path="/register" element={<Register />} />

    {/* Farmer */}
    <Route path="/farmer/dashboard"           element={<ProtectedRoute roles={FARMER}><FarmerDashboard /></ProtectedRoute>} />
    <Route path="/farmer/crop-recommendation" element={<ProtectedRoute roles={FARMER}><CropRecommendation /></ProtectedRoute>} />
    <Route path="/farmer/disease-detection"   element={<ProtectedRoute roles={FARMER}><DiseaseDetection /></ProtectedRoute>} />
    <Route path="/farmer/weather"             element={<ProtectedRoute roles={FARMER}><Weather /></ProtectedRoute>} />
    <Route path="/farmer/market"              element={<ProtectedRoute roles={FARMER}><Market /></ProtectedRoute>} />
    <Route path="/farmer/irrigation"          element={<ProtectedRoute roles={FARMER}><Irrigation /></ProtectedRoute>} />
    <Route path="/farmer/analytics"           element={<ProtectedRoute roles={FARMER}><Analytics /></ProtectedRoute>} />
    <Route path="/farmer/ai-assistant"        element={<ProtectedRoute roles={FARMER}><AIAssistant /></ProtectedRoute>} />

    {/* Expert */}
    <Route path="/expert/dashboard" element={<ProtectedRoute roles={EXPERT}><ExpertDashboard /></ProtectedRoute>} />

    {/* Admin */}
    <Route path="/admin/dashboard"  element={<ProtectedRoute roles={ADMIN}><AdminDashboard /></ProtectedRoute>} />

    {/* 404 */}
    <Route path="*" element={<NotFound />} />
  </Routes>
);

export default AppRoutes;
