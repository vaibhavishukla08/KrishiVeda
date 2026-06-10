// pages/auth/Login.jsx
import { useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sprout, Mail, Lock, AlertCircle } from 'lucide-react';
import useAuthStore from '../../hooks/useAuthStore';

const schema = z.object({
  email:    z.string().email('Valid email required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

const Login = () => {
  const { t, i18n } = useTranslation();
  const navigate    = useNavigate();
  const location    = useLocation();
  const { login, isLoading, error, clearError, isLoggedIn } = useAuthStore();

  const from = location.state?.from?.pathname || '/farmer/dashboard';

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  // If already logged in redirect away
  useEffect(() => {
    if (isLoggedIn) navigate(from, { replace: true });
  }, [isLoggedIn, navigate, from]);

  useEffect(() => { return () => clearError(); }, [clearError]);

  const onSubmit = async (data) => {
    try {
      const redirectTo = await login(data);
      navigate(redirectTo, { replace: true });
    } catch (_) {}
  };

  const toggleLang = () => {
    const next = i18n.language === 'hi' ? 'en' : 'hi';
    i18n.changeLanguage(next);
    localStorage.setItem('krishiveda_lang', next);
  };

  return (
    <div className="min-h-screen bg-[#0a150a] flex">
      {/* Left panel — illustration / brand */}
      <div className="hidden lg:flex w-1/2 bg-[#0d1f0d] flex-col justify-between p-12 border-r border-[#1e3a1e]">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-[#639922] flex items-center justify-center">
            <Sprout size={20} color="white" />
          </div>
          <span className="text-white font-bold text-xl">KrishiVeda</span>
        </div>

        <div>
          <h2 className="text-white text-4xl font-bold leading-tight mb-4">
            AI-powered farming<br />
            <span className="text-[#639922]">for every Indian farmer.</span>
          </h2>
          <p className="text-[#5a7a3a] text-base leading-relaxed">
            Crop recommendations, disease detection, smart irrigation, and market
            insights — in Hindi and English.
          </p>
          {/* Feature chips */}
          <div className="flex flex-wrap gap-2 mt-8">
            {['Crop Recommendation', 'Disease Detection', 'Market Prices', 'AI Assistant', 'Smart Irrigation'].map((f) => (
              <span key={f} className="px-3 py-1.5 rounded-full border border-[#2a4a2a] text-[#8aab6a] text-xs font-medium">
                {f}
              </span>
            ))}
          </div>
        </div>

        <p className="text-[#3a5a3a] text-xs">
          © 2025 KrishiVeda · Built for Indian farmers
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        {/* Mobile logo */}
        <div className="flex lg:hidden items-center gap-2 mb-8">
          <div className="w-9 h-9 rounded-xl bg-[#639922] flex items-center justify-center">
            <Sprout size={20} color="white" />
          </div>
          <span className="text-white font-bold text-xl">KrishiVeda</span>
        </div>

        <div className="w-full max-w-sm">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-white text-2xl font-bold mb-1">
              {t('auth.welcomeBack')} 👋
            </h1>
            <p className="text-[#5a7a3a] text-sm">
              {t('auth.hasAccount').replace('?', '')} — {' '}
              <Link to="/register" className="text-[#639922] hover:underline font-medium">
                {t('auth.register')}
              </Link>
            </p>
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700/50 mb-5">
              <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-[#8aab6a] text-sm font-medium mb-1.5">
                {t('auth.email')}
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a6a4a]" />
                <input
                  {...register('email')}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  className={`
                    w-full pl-9 pr-4 py-2.5 rounded-lg bg-[#0d1f0d] border text-white text-sm
                    placeholder:text-[#3a5a3a] outline-none transition-colors
                    ${errors.email
                      ? 'border-red-600 focus:border-red-500'
                      : 'border-[#2a4a2a] focus:border-[#639922]'}
                  `}
                />
              </div>
              {errors.email && (
                <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-[#8aab6a] text-sm font-medium mb-1.5">
                {t('auth.password')}
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a6a4a]" />
                <input
                  {...register('password')}
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`
                    w-full pl-9 pr-4 py-2.5 rounded-lg bg-[#0d1f0d] border text-white text-sm
                    placeholder:text-[#3a5a3a] outline-none transition-colors
                    ${errors.password
                      ? 'border-red-600 focus:border-red-500'
                      : 'border-[#2a4a2a] focus:border-[#639922]'}
                  `}
                />
              </div>
              {errors.password && (
                <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-lg bg-[#639922] hover:bg-[#74b028] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors mt-2"
            >
              {isLoading ? 'Logging in...' : t('auth.loginBtn')}
            </button>
          </form>

          {/* Language toggle */}
          <button
            onClick={toggleLang}
            className="w-full mt-4 py-2 rounded-lg border border-[#2a4a2a] text-[#5a7a3a] hover:text-white hover:border-[#639922] text-sm transition-colors"
          >
            {i18n.language === 'hi' ? 'Switch to English' : 'हिंदी में बदलें'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
