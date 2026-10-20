import { Link } from "react-router-dom";
import {
  AlertTriangle, ArrowRight, CloudSun, Droplets, IndianRupee, Leaf, MapPin, MessageCircle, ScanSearch, Sprout, Thermometer,
} from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, Empty, ErrorBox, Loading, formatDate, titleCase } from "../components/ui";
import { AlertList, IRRIGATION_CROPS } from "./Weather";

function QuickAction({ to, icon: Icon, label }) {
  return (
    <Link to={to} className="card group flex items-center gap-3 p-4 transition-colors hover:border-leaf-500 hover:bg-leaf-50">
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-leaf-100 text-forest-700"><Icon size={22} aria-hidden /></span>
      <span className="font-semibold text-forest-800">{label}</span>
      <ArrowRight size={18} className="ml-auto text-ink-muted transition-transform group-hover:translate-x-0.5" aria-hidden />
    </Link>
  );
}

function OverviewCard({ title, icon: Icon, badge, children }) {
  return (
    <Card className="flex flex-col">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold text-ink-muted"><Icon size={18} className="text-leaf-600" aria-hidden />{title}</h2>
        {badge}
      </div>
      <div className="flex-1">{children}</div>
    </Card>
  );
}

export default function Dashboard() {
  const { t, lang, farmer, farm, farmerId, farmerLoading } = useApp();
  const location = farm?.location_name;
  const mainCrop = farm?.crops?.map((c) => c.crop_name).find((c) => IRRIGATION_CROPS.includes(c)) || "wheat";

  const irr = useAsync(
    () => (location ? api.irrigation({ city: location, crop: mainCrop, area_acres: farm?.area_acres || undefined }) : Promise.resolve(null)),
    [location, mainCrop]
  );
  const history = useAsync(() => (farmerId ? api.history(farmerId, 5) : Promise.resolve(null)), [farmerId]);
  const prices = useAsync(() => api.marketPrices({ limit: 200 }), []);

  const w = irr.data?.weather;
  const adv = irr.data?.advice;
  const lastCheck = history.data?.disease_analyses?.[0];
  const farmCrops = farm?.crops?.map((c) => c.crop_name) || [];
  const priceRows = (prices.data?.records || [])
    .filter((r) => !farmCrops.length || farmCrops.some((c) => r.commodity.toLowerCase().includes(c === "rice" ? "paddy" : c)))
    .slice(0, 3);

  if (farmerLoading) return <Loading />;

  return (
    <>
      <section className="relative mb-6 overflow-hidden rounded-3xl bg-forest-700 px-6 py-7 text-white sm:px-8">
        <svg aria-hidden className="absolute -right-10 -top-6 h-48 w-48 opacity-15" viewBox="0 0 64 64"><path d="M32 52V26" stroke="#fff" strokeWidth="3" /><path d="M32 34c-9 0-15-6-15-15 9 0 15 6 15 15Z" fill="#fff" /><path d="M32 40c9 0 15-6 15-15-9 0-15 6-15 15Z" fill="#fff" /></svg>
        <p className="text-leaf-100/90">{t("tagline")}</p>
        <h1 className="mt-1 text-3xl font-bold sm:text-4xl">{farmer ? `${t("greeting")}, ${farmer.name}` : t("greeting_guest")}</h1>
        <p className="mt-2 max-w-xl text-leaf-100/90">{t("dash_intro")}</p>
        {farm && (
          <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-leaf-100">
            {location && <span className="inline-flex items-center gap-1"><MapPin size={15} aria-hidden />{location}</span>}
            {farm.area_acres && <span>{farm.area_acres} {t("acres")}</span>}
            {farmCrops.length > 0 && <span>{t("crops_label")}: {farmCrops.map(titleCase).join(", ")}</span>}
          </p>
        )}
      </section>

      {!farmer && (
        <Card className="mb-6 border-wheat-500/60 bg-wheat-100/50">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-forest-800">{t("dash_setup_title")}</h2>
              <p className="text-ink-muted">{t("dash_setup_text")}</p>
            </div>
            <Link to="/profile" className="btn btn-primary shrink-0">{t("dash_setup_btn")}</Link>
          </div>
        </Card>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewCard title={t("card_weather")} icon={CloudSun} badge={w && <Badge kind="live">{t("measured")}</Badge>}>
          {!location ? <p className="text-sm text-ink-muted">{t("no_location")}</p>
            : irr.loading ? <Loading />
            : irr.error ? <p className="text-sm text-[#a1361b]">{irr.error.message}</p>
            : w && (
              <>
                <p className="flex items-baseline gap-2 text-3xl font-bold tabular-nums text-forest-800"><Thermometer size={22} className="self-center text-sun-chart" aria-hidden />{Math.round(w.current.temperature_c)}°C</p>
                <p className="text-sm text-ink-muted">{w.current.condition} · {t("humidity")} {w.current.humidity_pct}%</p>
              </>
            )}
        </OverviewCard>

        <OverviewCard title={t("card_crop_health")} icon={Leaf}>
          {history.loading ? <Loading /> : lastCheck ? (
            <>
              <p className="text-xl font-bold text-forest-800">{lastCheck.disease || t(`status_${lastCheck.status}`)}</p>
              <p className="text-sm text-ink-muted">{lastCheck.crop} · {t("last_check")} {formatDate(lastCheck.created_at, lang)}</p>
            </>
          ) : (
            <>
              <p className="text-sm text-ink-muted">{t("no_checks_yet")}</p>
              <Link to="/disease" className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-forest-700 hover:underline">{t("check_now")} <ArrowRight size={14} /></Link>
            </>
          )}
        </OverviewCard>

        <OverviewCard title={t("card_irrigation")} icon={Droplets} badge={adv && <Badge kind="estimated">{t("estimated")}</Badge>}>
          {!location ? <p className="text-sm text-ink-muted">{t("no_location")}</p>
            : irr.loading ? <Loading />
            : adv && (
              <>
                <p className="text-xl font-bold text-forest-800">{t(`action_${adv.action}`)}</p>
                <p className="text-sm text-ink-muted">{titleCase(mainCrop)} · {adv.headline}</p>
              </>
            )}
        </OverviewCard>

        <OverviewCard title={t("card_market")} icon={IndianRupee} badge={prices.data && <Badge kind={prices.data.mode === "live" ? "live" : "demo"}>{prices.data.mode === "live" ? t("live_data") : t("demo_data")}</Badge>}>
          {prices.loading ? <Loading /> : priceRows.length ? (
            <ul className="space-y-1 text-sm">
              {priceRows.map((r, i) => (
                <li key={i} className="flex justify-between gap-2"><span className="truncate">{r.commodity} · {r.market}</span><span className="font-semibold tabular-nums">₹{r.modal_price?.toLocaleString("en-IN")}</span></li>
              ))}
            </ul>
          ) : <p className="text-sm text-ink-muted">{t("no_prices")}</p>}
        </OverviewCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title={t("alerts")} icon={AlertTriangle}>
            {!location ? <p className="text-sm text-ink-muted">{t("no_location")}</p>
              : irr.loading ? <Loading /> : irr.error ? <ErrorBox error={irr.error} onRetry={irr.run} /> : <AlertList alerts={adv?.alerts} />}
          </Card>
          <div className="grid gap-6 md:grid-cols-2">
            <Card title={t("recent_checks")} icon={Leaf}>
              {!farmerId ? <Empty>{t("need_profile")}</Empty> : history.data?.disease_analyses?.length ? (
                <ul className="divide-y divide-line text-sm">
                  {history.data.disease_analyses.map((a) => (
                    <li key={a.id} className="flex justify-between gap-2 py-2">
                      <span>{a.crop || "—"} · {a.disease || t(`status_${a.status}`)}</span>
                      <span className="shrink-0 text-ink-muted">{formatDate(a.created_at, lang)}</span>
                    </li>
                  ))}
                </ul>
              ) : <Empty>{t("no_checks_yet")}</Empty>}
            </Card>
            <Card title={t("recent_advice")} icon={MessageCircle}>
              {!farmerId ? <Empty>{t("need_profile")}</Empty> : history.data?.advisory?.length ? (
                <ul className="divide-y divide-line text-sm">
                  {history.data.advisory.map((m) => <li key={m.id} className="py-2"><p className="line-clamp-1 font-medium">{m.question}</p></li>)}
                </ul>
              ) : <Empty>{t("no_history")}</Empty>}
            </Card>
          </div>
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold text-forest-800">{t("quick_actions")}</h2>
          <div className="grid gap-3">
            <QuickAction to="/disease" icon={ScanSearch} label={t("qa_disease")} />
            <QuickAction to="/weather" icon={CloudSun} label={t("qa_weather")} />
            <QuickAction to="/crops" icon={Sprout} label={t("qa_crops")} />
            <QuickAction to="/advisory" icon={MessageCircle} label={t("qa_ask")} />
          </div>
        </div>
      </div>
    </>
  );
}
