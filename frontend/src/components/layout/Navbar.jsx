// components/layout/Navbar.jsx
import { useTranslation } from 'react-i18next';
import { Bell, Globe } from 'lucide-react';
import useAuthStore from '../../hooks/useAuthStore';

const Navbar = ({ title }) => {
  const { t, i18n } = useTranslation();
  const { user } = useAuthStore();

  const toggleLang = () => {
    const next = i18n.language === 'hi' ? 'en' : 'hi';
    i18n.changeLanguage(next);
    localStorage.setItem('krishiveda_lang', next);
  };

  return (
    <header className="h-14 bg-[#0d1f0d] border-b border-[#1e3a1e] flex items-center justify-between px-6">
      {/* Page title */}
      <h1 className="text-white font-semibold text-base">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2a4a2a] text-[#8aab6a] hover:border-[#639922] hover:text-white transition-colors text-sm"
        >
          <Globe size={14} />
          <span className="font-medium">{i18n.language === 'hi' ? 'EN' : 'हिं'}</span>
        </button>

        {/* Notifications */}
        <button className="relative w-9 h-9 flex items-center justify-center rounded-lg border border-[#2a4a2a] text-[#8aab6a] hover:border-[#639922] hover:text-white transition-colors">
          <Bell size={16} />
          {/* Notification dot — show conditionally when you have notifications */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#639922] rounded-full" />
        </button>

        {/* Avatar */}
        <div className="w-9 h-9 rounded-lg bg-[#639922] flex items-center justify-center">
          <span className="text-white font-bold text-sm">
            {user?.name?.charAt(0)?.toUpperCase() || 'K'}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
