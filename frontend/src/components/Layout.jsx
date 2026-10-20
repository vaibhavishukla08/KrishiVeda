import { Suspense, useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BarChart3, CloudSun, Flame, Headset, Home, IndianRupee, Landmark, Languages, Leaf, Menu,
  MessageCircle, Sprout, User, X,
} from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { Loading } from "./ui";

export const NAV = [
  { to: "/", key: "nav_dashboard", icon: Home, mobile: true },
  { to: "/disease", key: "nav_disease", icon: Leaf, mobile: true },
  { to: "/weather", key: "nav_weather", short: "nav_weather_short", icon: CloudSun, mobile: true },
  { to: "/crops", key: "nav_crops", icon: Sprout },
  { to: "/market", key: "nav_market", icon: IndianRupee },
  { to: "/advisory", key: "nav_advisory", icon: MessageCircle, mobile: true },
  { to: "/expert", key: "nav_expert", icon: Headset },
  { to: "/profile", key: "nav_profile", icon: User },
  { to: "/schemes", key: "nav_schemes", icon: Landmark },
  { to: "/stubble", key: "nav_stubble", icon: Flame },
  { to: "/analytics", key: "nav_analytics", icon: BarChart3 },
];

function Logo() {
  const { t } = useApp();
  return (
    <div className="flex items-center gap-2.5">
      <img src="/favicon.svg" alt="" className="h-9 w-9" />
      <div className="leading-tight">
        <div className="font-display text-xl font-bold text-white">{t("app_name")}</div>
        <div className="text-[11px] text-leaf-100/80">AI Smart Agriculture</div>
      </div>
    </div>
  );
}

function LangToggle({ className = "" }) {
  const { lang, setLang, t } = useApp();
  return (
    <button
      onClick={() => setLang(lang === "en" ? "hi" : "en")}
      className={`inline-flex min-h-[40px] items-center gap-1.5 rounded-full border px-3 text-sm font-semibold ${className}`}
      aria-label={t("lang_toggle_label")}
    >
      <Languages size={16} aria-hidden /> {t("lang_toggle")}
    </button>
  );
}

const linkClass = ({ isActive }) =>
  `flex items-center gap-3 rounded-xl px-3 py-2.5 font-medium transition-colors ${
    isActive ? "bg-white/15 text-white" : "text-leaf-100/85 hover:bg-white/10 hover:text-white"
  }`;

export default function Layout() {
  const { t, farmer } = useApp();
  const [moreOpen, setMoreOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setMoreOpen(false), [location.pathname]);

  return (
    <div className="min-h-screen lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:p-2">
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-forest-800 p-4 lg:flex">
        <Logo />
        <nav className="mt-8 flex flex-1 flex-col gap-1 overflow-y-auto" aria-label="Main">
          {NAV.map(({ to, key, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"} className={linkClass}>
              <Icon size={19} aria-hidden /> {t(key)}
            </NavLink>
          ))}
        </nav>
        <p className="mt-4 border-t border-white/10 pt-4 text-xs leading-relaxed text-leaf-100/70">{t("tagline")}</p>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-line bg-cream/90 px-4 py-3 backdrop-blur lg:px-8">
          <div className="lg:hidden">
            <div className="flex items-center gap-2">
              <img src="/favicon.svg" alt="" className="h-8 w-8" />
              <span className="font-display text-lg font-bold text-forest-800">{t("app_name")}</span>
            </div>
          </div>
          <p className="hidden text-sm text-ink-muted lg:block">{t("tagline")}</p>
          <div className="flex items-center gap-2">
            <NavLink to="/profile" className="hidden items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-forest-700 hover:bg-leaf-50 sm:flex">
              <User size={16} aria-hidden /> {farmer?.name || t("nav_profile")}
            </NavLink>
            <LangToggle className="border-forest-700/30 bg-white text-forest-700 hover:bg-leaf-50" />
          </div>
        </header>

        <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-6 lg:px-8 lg:pb-10">
          <Suspense fallback={<Loading />}>
            <Outlet />
          </Suspense>
        </main>
      </div>

      {/* Mobile bottom navigation */}
      <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden" aria-label="Main">
        {NAV.filter((n) => n.mobile).map(({ to, key, short, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex min-h-[60px] flex-col items-center justify-center gap-0.5 px-1 text-[11px] font-medium ${isActive ? "text-forest-700" : "text-ink-muted"}`
            }
          >
            <Icon size={22} aria-hidden />
            <span className="max-w-full truncate">{t(short || key)}</span>
          </NavLink>
        ))}
        <button
          onClick={() => setMoreOpen(true)}
          className="flex min-h-[60px] flex-col items-center justify-center gap-0.5 text-[11px] font-medium text-ink-muted"
          aria-haspopup="dialog"
        >
          <Menu size={22} aria-hidden /> {t("nav_more")}
        </button>
      </nav>

      {/* Mobile "More" sheet */}
      {moreOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label={t("nav_more")}>
          <button className="absolute inset-0 bg-black/40" aria-label={t("cancel")} onClick={() => setMoreOpen(false)} />
          <div className="absolute inset-x-0 bottom-0 rounded-t-3xl bg-forest-800 p-5 pb-[calc(1.25rem+env(safe-area-inset-bottom))]">
            <div className="mb-4 flex items-center justify-between">
              <Logo />
              <button onClick={() => setMoreOpen(false)} className="rounded-full p-2 text-white hover:bg-white/10" aria-label={t("cancel")}>
                <X size={22} />
              </button>
            </div>
            <nav className="grid grid-cols-2 gap-1">
              {NAV.map(({ to, key, icon: Icon }) => (
                <NavLink key={to} to={to} end={to === "/"} className={linkClass}>
                  <Icon size={19} aria-hidden /> {t(key)}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
