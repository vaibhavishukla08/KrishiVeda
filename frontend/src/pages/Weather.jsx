import { useEffect, useState } from "react";
import { AlertTriangle, CloudRain, CloudSun, Droplets, MapPin, Search, Thermometer, Wind } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, Empty, ErrorBox, Field, Loading, Notice, PageHeader, formatDate, titleCase } from "../components/ui";
import { CHART, SimpleBarChart, TempChart } from "../components/charts";

export const IRRIGATION_CROPS = ["wheat", "rice", "maize", "cotton", "sugarcane", "potato", "tomato", "soybean", "chickpea", "lentil", "groundnut", "mustard", "onion", "pepper", "banana"];

const ACTION_STYLE = {
  irrigate: "bg-[#eaf1fa] text-[#1f4f86] border-[#2f6db3]/30",
  delay: "bg-wheat-100 text-soil-700 border-wheat-500/50",
  monitor: "bg-leaf-50 text-forest-700 border-leaf-500/30",
};

export function Stat({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl bg-leaf-50 p-3">
      <div className="flex items-center gap-1.5 text-sm text-ink-muted"><Icon size={16} aria-hidden />{label}</div>
      <div className="mt-0.5 text-xl font-bold tabular-nums text-forest-800">{value}</div>
    </div>
  );
}

export function AlertList({ alerts }) {
  const { t } = useApp();
  if (!alerts?.length) return <p className="text-sm text-ink-muted">{t("no_alerts")}</p>;
  return (
    <ul className="space-y-2">
      {alerts.map((a, i) => (
        <li key={i} className={`flex gap-2 rounded-xl border p-3 text-sm ${a.severity === "high" ? "border-[#e0a48f] bg-[#fdf1ee] text-[#8a2f16]" : "border-wheat-500/50 bg-wheat-100 text-soil-700"}`}>
          <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden />
          <span>{a.date && <strong>{a.date}: </strong>}{a.message}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Weather() {
  const { t, lang, farm } = useApp();
  const [city, setCity] = useState("");
  const [crop, setCrop] = useState("wheat");
  const [stage, setStage] = useState("mid");
  const [area, setArea] = useState("");
  const [query, setQuery] = useState(null);
  const res = useAsync((q) => api.irrigation(q), [], { immediate: false });

  // Pre-fill from the farmer profile
  useEffect(() => {
    if (!farm) return;
    if (farm.location_name) setCity((c) => c || farm.location_name);
    if (farm.area_acres) setArea((a) => a || String(farm.area_acres));
    const known = farm.crops?.map((c) => c.crop_name).find((c) => IRRIGATION_CROPS.includes(c));
    if (known) setCrop(known);
  }, [farm]);

  function submit(e, overrides = {}) {
    e?.preventDefault();
    const q = { crop, stage, area_acres: area || undefined, city: city.trim() || undefined, ...overrides };
    if (!q.city && q.lat == null) return;
    setQuery(q);
    res.run(q);
  }

  const w = res.data?.weather;
  const adv = res.data?.advice;
  const days = (w?.daily || []).map((d) => ({
    label: new Date(d.date).toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { weekday: "short", day: "numeric" }),
    max: d.temp_max_c, min: d.temp_min_c, rain: d.rain_mm,
  }));

  return (
    <>
      <PageHeader title={t("weather_title")} subtitle={t("weather_subtitle")} icon={CloudSun} />

      <Card className="mb-6">
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-[2fr_1fr_1fr_1fr_auto] md:items-end">
          <Field label={t("city_placeholder")} htmlFor="city">
            <input id="city" className="input" value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Ludhiana" minLength={2} maxLength={80} />
          </Field>
          <Field label={t("crop")} htmlFor="crop">
            <select id="crop" className="input" value={crop} onChange={(e) => setCrop(e.target.value)}>
              {IRRIGATION_CROPS.map((c) => <option key={c} value={c}>{titleCase(c)}</option>)}
            </select>
          </Field>
          <Field label={t("growth_stage")} htmlFor="stage">
            <select id="stage" className="input" value={stage} onChange={(e) => setStage(e.target.value)}>
              {["initial", "mid", "late"].map((s) => <option key={s} value={s}>{t(`stage_${s}`)}</option>)}
            </select>
          </Field>
          <Field label={t("farm_area")} htmlFor="area">
            <input id="area" className="input" type="number" min="0.01" step="0.01" value={area} onChange={(e) => setArea(e.target.value)} />
          </Field>
          <button className="btn btn-primary" disabled={res.loading || city.trim().length < 2}>
            <Search size={18} aria-hidden /> {t("search")}
          </button>
        </form>
        {farm?.latitude != null && (
          <button className="btn btn-secondary mt-3" onClick={() => submit(null, { city: undefined, lat: farm.latitude, lon: farm.longitude })}>
            <MapPin size={16} aria-hidden /> {t("use_farm_location")}
          </button>
        )}
      </Card>

      {res.loading && <Loading />}
      <ErrorBox error={res.error} onRetry={query ? () => res.run(query) : undefined} />
      {!res.data && !res.loading && !res.error && <Empty icon={CloudSun}>{t("weather_empty")}</Empty>}

      {w && adv && !res.loading && (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-3">
            <Card
              title={w.location.name}
              icon={MapPin}
              action={<Badge kind="live" title={w.source.name}>{t("measured")} · {w.source.provider}</Badge>}
            >
              <p className="mb-3 text-ink-muted">{w.current.condition} · {t("updated")} {w.current.observed_at.replace("T", " ").slice(0, 16)}</p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4">
                <Stat icon={Thermometer} label={t("temperature")} value={`${Math.round(w.current.temperature_c)}°C`} />
                <Stat icon={Droplets} label={t("humidity")} value={`${w.current.humidity_pct}%`} />
                <Stat icon={CloudRain} label={t("rain")} value={`${w.current.precipitation_mm} mm`} />
                <Stat icon={Wind} label={t("wind")} value={`${Math.round(w.current.wind_speed_kmh)} km/h`} />
              </div>
            </Card>

            <Card title={t("forecast")}>
              <h3 className="text-sm font-semibold text-ink-muted">{t("temp_chart")}</h3>
              <TempChart data={days} maxLabel={t("max")} minLabel={t("min")} />
              <h3 className="mt-4 text-sm font-semibold text-ink-muted">{t("rain_chart")}</h3>
              <SimpleBarChart data={days} dataKey="rain" color={CHART.sky} unit=" mm" height={170} valueLabel={t("rain")} />
              <details className="mt-3 text-sm">
                <summary className="cursor-pointer font-medium text-forest-700">Table view</summary>
                <div className="mt-2 overflow-x-auto">
                  <table className="w-full text-left">
                    <thead><tr className="border-b border-line text-ink-muted"><th className="py-1">{t("date")}</th><th>{t("max")}</th><th>{t("min")}</th><th>{t("rain")}</th><th>ET0</th></tr></thead>
                    <tbody>
                      {w.daily.map((d) => (
                        <tr key={d.date} className="border-b border-line/60">
                          <td className="py-1">{formatDate(d.date, lang)}</td><td>{d.temp_max_c}°</td><td>{d.temp_min_c}°</td>
                          <td>{d.rain_mm} mm ({d.rain_probability_pct ?? "–"}%)</td><td>{d.et0_mm ?? "–"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              <p className="mt-2 text-xs text-ink-muted">{t("source")}: <a className="underline" href={w.source.url} target="_blank" rel="noreferrer">{w.source.name}</a></p>
            </Card>
          </div>

          <div className="space-y-6 lg:col-span-2">
            <Card title={t("irrigation_advice")} icon={Droplets} action={<Badge kind="estimated">{t("estimated")}</Badge>}>
              <div className={`mb-3 rounded-2xl border p-4 ${ACTION_STYLE[adv.action]}`}>
                <p className="text-sm font-semibold uppercase tracking-wide">{t(`action_${adv.action}`)}</p>
                <p className="text-lg font-bold">{adv.headline}</p>
              </div>
              <ul className="list-disc space-y-1.5 pl-5 text-sm">{adv.reasons.map((r) => <li key={r}>{r}</li>)}</ul>

              {adv.estimate && (
                <div className="mt-4 rounded-2xl border border-line p-4">
                  <h3 className="mb-2 font-semibold">{t("water_estimate")}</h3>
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between"><dt>{t("crop_water_use")}</dt><dd className="font-medium tabular-nums">{adv.estimate.etc_mm} mm</dd></div>
                    <div className="flex justify-between"><dt>{t("useful_rain")}</dt><dd className="font-medium tabular-nums">− {adv.estimate.effective_rain_mm} mm</dd></div>
                    <div className="flex justify-between border-t border-line pt-1"><dt className="font-semibold">{t("net_need")}</dt><dd className="font-bold tabular-nums">{adv.estimate.net_requirement_mm} mm</dd></div>
                    <div className="flex justify-between"><dt>{t("litres_acre")}</dt><dd className="tabular-nums">≈ {adv.estimate.litres_per_acre.toLocaleString("en-IN")}</dd></div>
                    {adv.estimate.litres_for_farm != null && (
                      <div className="flex justify-between"><dt>{t("litres_farm")}</dt><dd className="tabular-nums">≈ {adv.estimate.litres_for_farm.toLocaleString("en-IN")}</dd></div>
                    )}
                  </dl>
                  <p className="mt-2 text-xs text-ink-muted">{adv.estimate.method} (Kc = {adv.estimate.kc}, ET0 = {adv.estimate.et0_mm} mm)</p>
                  <details className="mt-2 text-xs text-ink-muted">
                    <summary className="cursor-pointer font-medium">{t("assumptions")}</summary>
                    <ul className="mt-1 list-disc pl-4">{adv.estimate.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
                  </details>
                </div>
              )}
              <div className="mt-4"><Notice kind="info">{adv.disclaimer}</Notice></div>
            </Card>
            <Card title={t("alerts")} icon={AlertTriangle}><AlertList alerts={adv.alerts} /></Card>
          </div>
        </div>
      )}
    </>
  );
}
