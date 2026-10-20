// components/layout/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard, Sprout, ScanLine, CloudSun,
  TrendingUp, Droplets, BarChart3, Bot, LogOut,
  ChevronLeft, ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import useAuthStore from '../../hooks/useAuthStore';

const farmerNav = [
  { key: 'dashboard',          icon: LayoutDashboard, to: '/farmer/dashboard' },
  { key: 'cropRecommendation', icon: Sprout,           to: '/farmer/crop-recommendation' },
  { key: 'diseaseDetection',   icon: ScanLine,         to: '/farmer/disease-detection' },
  { key: 'weather',            icon: CloudSun,         to: '/farmer/weather' },
  { key: 'market',             icon: TrendingUp,       to: '/farmer/market' },
  { key: 'irrigation',         icon: Droplets,         to: '/farmer/irrigation' },
  { key: 'analytics',          icon: BarChart3,        to: '/farmer/analytics' },
  { key: 'aiAssistant',        icon: Bot,              to: '/farmer/ai-assistant' },
];

const Sidebar = () => {
  const { t } = useTranslation();
  const { logout, user } = useAuthStore();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside
      className={`
        flex flex-col bg-[#0d1f0d] border-r border-[#1e3a1e] min-h-screen
        transition-all duration-300
        ${collapsed ? 'w-[64px]' : 'w-[220px]'}
      `}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-[#1e3a1e]">
        <div className="w-8 h-8 rounded-lg bg-[#639922] flex items-center justify-center flex-shrink-0">
          <Sprout size={18} color="white" />
        </div>
        {!collapsed && (
          <span className="text-white font-bold text-base tracking-wide">
            KrishiVeda
          </span>
        )}
      </div>

      {/* User badge */}
      {!collapsed && user && (
        <div className="mx-3 mt-4 px-3 py-2 rounded-lg bg-[#1a2e1a]">
          <p className="text-[#639922] text-xs font-semibold truncate">{user.name}</p>
          <p className="text-[#5a7a3a] text-[10px] truncate">{user.role}</p>
        </div>
      )}

      {/* Nav links */}
      <nav className="flex-1 mt-4 px-2 space-y-1">
        {farmerNav.map(({ key, icon: Icon, to }) => (
          <NavLink
            key={key}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
               ${isActive
                 ? 'bg-[#639922] text-white'
                 : 'text-[#8aab6a] hover:bg-[#1a2e1a] hover:text-white'
               }`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{t(`nav.${key}`)}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom: collapse toggle + logout */}
      <div className="px-2 pb-4 space-y-1 border-t border-[#1e3a1e] pt-3">
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#5a7a3a] hover:bg-[#1a2e1a] hover:text-white transition-colors text-sm"
        >
          {collapsed ? <ChevronRight size={18} /> : <><ChevronLeft size={18} /><span>Collapse</span></>}
        </button>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#5a7a3a] hover:bg-red-900/30 hover:text-red-400 transition-colors text-sm"
        >
          <LogOut size={18} className="flex-shrink-0" />
          {!collapsed && <span>{t('nav.logout')}</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
