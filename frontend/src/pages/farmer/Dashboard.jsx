// pages/farmer/Dashboard.jsx
import { useTranslation } from 'react-i18next';
import { Sprout, ScanLine, Droplets, TrendingUp, CloudSun, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageLayout from '../../components/layout/PageLayout';
import useAuthStore from '../../hooks/useAuthStore';

const StatCard = ({ icon: Icon, label, value, color, to }) => (
  <Link to={to}>
    <div className="bg-[#0d1f0d] border border-[#1e3a1e] rounded-xl p-5 hover:border-[#639922] transition-colors group cursor-pointer">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${color}`}>
        <Icon size={20} color="white" />
      </div>
      <p className="text-[#5a7a3a] text-xs font-medium mb-0.5">{label}</p>
      <p className="text-white text-xl font-bold">{value}</p>
    </div>
  </Link>
);

const QuickAction = ({ icon: Icon, label, desc, to, color }) => (
  <Link to={to}>
    <div className="bg-[#0d1f0d] border border-[#1e3a1e] rounded-xl p-5 hover:border-[#639922] transition-colors flex items-start gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={18} color="white" />
      </div>
      <div>
        <p className="text-white font-semibold text-sm mb-0.5">{label}</p>
        <p className="text-[#5a7a3a] text-xs leading-relaxed">{desc}</p>
      </div>
    </div>
  </Link>
);

const FarmerDashboard = () => {
  const { t }  = useTranslation();
  const { user } = useAuthStore();

  const stats = [
    { icon: Sprout,   label: t('dashboard.activeCrops'),    value: '3',    color: 'bg-[#2d6a2d]', to: '/farmer/crops' },
    { icon: ScanLine, label: t('dashboard.recentDetections'), value: '2',  color: 'bg-[#5a3e1a]', to: '/farmer/disease-detection' },
    { icon: CloudSun, label: t('dashboard.weatherToday'),   value: '28°C', color: 'bg-[#1a3a5a]', to: '/farmer/weather' },
    { icon: TrendingUp, label: t('dashboard.marketPrices'), value: '₹1,240', color: 'bg-[#3a1a5a]', to: '/farmer/market' },
  ];

  const actions = [
    { icon: ScanLine,   label: 'Disease Detection',     desc: 'Upload a photo of your crop leaf to detect diseases instantly.', to: '/farmer/disease-detection',    color: 'bg-[#5a3e1a]' },
    { icon: Sprout,     label: 'Crop Recommendation',   desc: 'Get AI-powered crop suggestions based on your soil and weather.', to: '/farmer/crop-recommendation', color: 'bg-[#2d6a2d]' },
    { icon: Droplets,   label: 'Irrigation Schedule',   desc: 'Science-based irrigation plan using FAO-56 standard.', to: '/farmer/irrigation',           color: 'bg-[#1a3a5a]' },
    { icon: Bot,        label: 'Ask KrishiMitra AI',    desc: 'Ask any farming question in Hindi or English.',              to: '/farmer/ai-assistant',         color: 'bg-[#3a1a2a]' },
  ];

  return (
    <PageLayout title={t('nav.dashboard')}>
      {/* Greeting */}
      <div className="mb-6">
        <h2 className="text-white text-xl font-bold mb-1">
          {t('dashboard.greeting')}, {user?.name?.split(' ')[0]} 🌱
        </h2>
        <p className="text-[#5a7a3a] text-sm">
          Here's what's happening on your farm today.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      {/* Quick actions */}
      <div className="mb-2">
        <h3 className="text-white font-semibold text-sm mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {actions.map((a) => <QuickAction key={a.label} {...a} />)}
        </div>
      </div>
    </PageLayout>
  );
};

export default FarmerDashboard;
