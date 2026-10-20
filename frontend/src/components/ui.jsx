import { AlertTriangle, CheckCircle2, Info, Loader2, RefreshCw } from "lucide-react";
import { useApp } from "../hooks/AppContext";

export function PageHeader({ title, subtitle, icon: Icon, children }) {
  return (
    <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-1 hidden h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-leaf-100 text-forest-700 sm:flex">
            <Icon size={24} aria-hidden />
          </span>
        )}
        <div>
          <h1 className="text-2xl font-bold text-forest-800 sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1 max-w-2xl text-ink-muted">{subtitle}</p>}
        </div>
      </div>
      {children}
    </header>
  );
}

export function Card({ title, icon: Icon, action, children, className = "" }) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-forest-800">
            {Icon && <Icon size={20} className="text-leaf-600" aria-hidden />}
            {title}
          </h2>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const BADGE_STYLES = {
  live: "bg-leaf-100 text-forest-700 border-leaf-500/30",
  demo: "bg-wheat-100 text-soil-700 border-wheat-500/50",
  estimated: "bg-[#eaf1fa] text-[#1f4f86] border-[#2f6db3]/30",
  neutral: "bg-[#f1f2ee] text-ink-muted border-line",
};

/** Small label that tells the farmer where a number comes from (live / demo / estimated). */
export function Badge({ kind = "neutral", children, title }) {
  return (
    <span title={title} className={`inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold ${BADGE_STYLES[kind]}`}>
      {children}
    </span>
  );
}

export function Loading({ label }) {
  const { t } = useApp();
  return (
    <div role="status" className="flex items-center gap-2 py-6 text-ink-muted">
      <Loader2 className="animate-spin" size={20} aria-hidden /> {label || t("loading")}
    </div>
  );
}

export function ErrorBox({ error, onRetry }) {
  const { t } = useApp();
  if (!error) return null;
  return (
    <div role="alert" className="flex flex-col gap-3 rounded-2xl border border-[#e8b4a6] bg-[#fdf1ee] p-4 text-[#7a2b17] sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-2">
        <AlertTriangle size={20} className="mt-0.5 shrink-0" aria-hidden />
        <div>
          <p className="font-semibold">{error.message}</p>
          {error.details?.reason && <p className="text-sm opacity-80">{error.details.reason}</p>}
          {error.details?.fields && (
            <ul className="mt-1 list-disc pl-5 text-sm">
              {error.details.fields.map((f) => <li key={f.field}>{f.field}: {f.message}</li>)}
            </ul>
          )}
        </div>
      </div>
      {onRetry && (
        <button className="btn btn-secondary shrink-0" onClick={onRetry}>
          <RefreshCw size={16} aria-hidden /> {t("retry")}
        </button>
      )}
    </div>
  );
}

export function Notice({ kind = "info", children }) {
  const styles = {
    info: "border-[#c5d7ee] bg-[#f2f7fd] text-[#1f4f86]",
    warn: "border-wheat-500/50 bg-wheat-100 text-soil-700",
    success: "border-leaf-500/40 bg-leaf-50 text-forest-700",
  };
  const Icon = kind === "warn" ? AlertTriangle : kind === "success" ? CheckCircle2 : Info;
  return (
    <div className={`flex items-start gap-2 rounded-xl border p-3 text-sm ${styles[kind]}`}>
      <Icon size={18} className="mt-0.5 shrink-0" aria-hidden />
      <div>{children}</div>
    </div>
  );
}

export function Empty({ icon: Icon = Info, children }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-line px-4 py-8 text-center text-ink-muted">
      <Icon size={28} aria-hidden className="text-leaf-500" />
      <div>{children}</div>
    </div>
  );
}

export function ConfidenceBar({ value, label }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-leaf-600" : pct >= 60 ? "bg-wheat-500" : "bg-[#b4532a]";
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-ink-muted">{label}</span>
        <span className="font-semibold">{pct}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-[#e7eae3]" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function Field({ label, htmlFor, hint, error, children }) {
  return (
    <div>
      <label className="label" htmlFor={htmlFor}>{label}</label>
      {children}
      {hint && !error && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
      {error && <p className="mt-1 text-sm font-medium text-[#a1361b]">{error}</p>}
    </div>
  );
}

export function formatDate(value, lang = "en") {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function titleCase(s) {
  return (s || "").replace(/\b\w/g, (c) => c.toUpperCase());
}
