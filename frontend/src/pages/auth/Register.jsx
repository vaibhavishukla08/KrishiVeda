// pages/auth/Register.jsx
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sprout, Mail, Lock, User, Phone, AlertCircle } from 'lucide-react';
import useAuthStore from '../../hooks/useAuthStore';
import { ROLES, ROLE_LABELS } from '../../constants/roles';

const schema = z.object({
  name:     z.string().min(2, 'Name must be at least 2 characters'),
  email:    z.string().email('Valid email required'),
  phone:    z.string().min(10, 'Valid phone number required'),
  role:     z.enum([ROLES.FARMER, ROLES.AGRICULTURAL_EXPERT]),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirm:  z.string(),
}).refine((d) => d.password === d.confirm, {
  message: "Passwords don't match",
  path:    ['confirm'],
});

const Register = () => {
  const { t }      = useTranslation();
  const navigate   = useNavigate();
  const { register: registerUser, isLoading, error, clearError, isLoggedIn } = useAuthStore();

  const { register, handleSubmit, formState: { errors }, watch } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { role: ROLES.FARMER },
  });

  useEffect(() => {
    if (isLoggedIn) navigate('/farmer/dashboard', { replace: true });
  }, [isLoggedIn, navigate]);

  useEffect(() => { return () => clearError(); }, [clearError]);

  const onSubmit = async (data) => {
    const { confirm, ...payload } = data;
    try {
      const redirectTo = await registerUser(payload);
      navigate(redirectTo, { replace: true });
    } catch (_) {}
  };

  const Field = ({ label, icon: Icon, name, type = 'text', placeholder, autoComplete }) => (
    <div>
      <label className="block text-[#8aab6a] text-sm font-medium mb-1.5">{label}</label>
      <div className="relative">
        <Icon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a6a4a]" />
        <input
          {...register(name)}
          type={type}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={`
            w-full pl-9 pr-4 py-2.5 rounded-lg bg-[#0d1f0d] border text-white text-sm
            placeholder:text-[#3a5a3a] outline-none transition-colors
            ${errors[name]
              ? 'border-red-600 focus:border-red-500'
              : 'border-[#2a4a2a] focus:border-[#639922]'}
          `}
        />
      </div>
      {errors[name] && <p className="text-red-400 text-xs mt-1">{errors[name].message}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a150a] flex flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-9 h-9 rounded-xl bg-[#639922] flex items-center justify-center">
            <Sprout size={20} color="white" />
          </div>
          <span className="text-white font-bold text-xl">KrishiVeda</span>
        </div>

        <div className="mb-7">
          <h1 className="text-white text-2xl font-bold mb-1">{t('auth.joinKrishiVeda')}</h1>
          <p className="text-[#5a7a3a] text-sm">
            {t('auth.hasAccount')}{' '}
            <Link to="/login" className="text-[#639922] hover:underline font-medium">
              {t('auth.login')}
            </Link>
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700/50 mb-5">
            <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Field label={t('auth.name')}     icon={User}  name="name"     placeholder="Ram Kumar"          autoComplete="name" />
          <Field label={t('auth.email')}    icon={Mail}  name="email"    placeholder="you@example.com"    autoComplete="email" />
          <Field label={t('auth.phone')}    icon={Phone} name="phone"    placeholder="9876543210"         autoComplete="tel" />

          {/* Role selector */}
          <div>
            <label className="block text-[#8aab6a] text-sm font-medium mb-1.5">
              {t('auth.role')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[ROLES.FARMER, ROLES.AGRICULTURAL_EXPERT].map((role) => (
                <label
                  key={role}
                  className={`
                    flex items-center gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition-colors
                    ${watch('role') === role
                      ? 'border-[#639922] bg-[#639922]/10 text-white'
                      : 'border-[#2a4a2a] text-[#5a7a3a] hover:border-[#3a5a3a]'}
                  `}
                >
                  <input {...register('role')} type="radio" value={role} className="sr-only" />
                  <span className="text-xs font-medium leading-tight">
                    {role === ROLES.FARMER ? 'किसान / Farmer' : 'विशेषज्ञ / Expert'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <Field label={t('auth.password')} icon={Lock}  name="password" type="password" placeholder="Min. 6 characters" autoComplete="new-password" />
          <Field label="Confirm Password"   icon={Lock}  name="confirm"  type="password" placeholder="Repeat password"   autoComplete="new-password" />

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-[#639922] hover:bg-[#74b028] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors mt-2"
          >
            {isLoading ? 'Creating account...' : t('auth.registerBtn')}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Register;
