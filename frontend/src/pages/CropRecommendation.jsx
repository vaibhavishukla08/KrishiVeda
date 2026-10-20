import { useState } from "react";
import { CheckCircle2, CircleAlert, CloudSun, FlaskConical, Sprout } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { CROP_FIELDS, validateCropInputs } from "../utils/validation";
import { Badge, Card, ConfidenceBar, ErrorBox, Field, Loading, Notice, PageHeader, titleCase } from "../components/ui";
import { HorizontalBarChart } from "../components/charts";

const EMPTY = Object.fromEntries(CROP_FIELDS.map((f) => [f.key, ""]));

export default function CropRecommendation() {
  const { t, lang, farmerId, farm } = useApp();
  const [values, setValues] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const model = useAsync(() => api.cropModel(), []);
  const rec = useAsync((body) => api.recommendCrop(body), [], { immediate: false });
  const weather = useAsync((q) => api.weather(q), [], { immediate: false });

  const set = (k, v) => setValues((s) => ({ ...s, [k]: v }));

  async function fillFromWeather() {
    if (!farm?.location_name) return;
    const w = await weather.run({ city: farm.location_name });
    if (w) setValues((s) => ({ ...s, temperature: String(w.current.temperature_c), humidity: String(w.current.humidity_pct) }));
  }

  function submit(e) {
    e.preventDefault();
    const errs = validateCropInputs(values);
    setErrors(errs);
    if (Object.keys(errs).length) return;
    const body = Object.fromEntries(CROP_FIELDS.map((f) => [f.key, Number(values[f.key])]));
    rec.run({ ...body, farmer_id: farmerId || undefined });
  }

  const r = rec.data;
  const cropLabel = (c) => (lang === "hi" && c.crop_hi ? `${c.crop_hi} (${titleCase(c.crop)})` : titleCase(c.crop));

  return (
    <>
      <PageHeader title={t("crops_title")} subtitle={t("crops_subtitle")} icon={Sprout} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,420px)_1fr]">
        <Card>
          <form onSubmit={submit} noValidate className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {CROP_FIELDS.map((f) => (
                <Field
                  key={f.key}
                  label={`${t(`field_${f.key}`)}${f.unit ? ` (${f.unit})` : ""}`}
                  htmlFor={`f-${f.key}`}
                  hint={`${t("range")} ${f.min}–${f.max}`}
                  error={errors[f.key] && t(errors[f.key])}
                >
                  <input
                    id={`f-${f.key}`}
                    className="input"
                    type="number"
                    inputMode="decimal"
                    min={f.min}
                    max={f.max}
                    step={f.step}
                    value={values[f.key]}
                    aria-invalid={Boolean(errors[f.key])}
                    onChange={(e) => set(f.key, e.target.value)}
                  />
                </Field>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn btn-secondary" onClick={() => { setValues(Object.fromEntries(CROP_FIELDS.map((f) => [f.key, String(f.example)]))); setErrors({}); }}>
                <FlaskConical size={16} aria-hidden /> {t("fill_example")}
              </button>
              {farm?.location_name && (
                <button type="button" className="btn btn-secondary" onClick={fillFromWeather} disabled={weather.loading}>
                  <CloudSun size={16} aria-hidden /> {t("fill_weather")}
                </button>
              )}
            </div>
            <ErrorBox error={weather.error} />
            <button className="btn btn-primary w-full" disabled={rec.loading || model.data?.available === false}>
              <Sprout size={18} aria-hidden /> {rec.loading ? t("recommending") : t("recommend")}
            </button>
          </form>
          {model.data && (
            <p className="mt-4 text-xs text-ink-muted">
              {model.data.available
                ? `${model.data.algorithm} · ${model.data.dataset.name} (${model.data.dataset.license}) · hold-out accuracy ${(model.data.metrics.test_accuracy * 100).toFixed(1)}% on ${model.data.metrics.test_rows} rows`
                : "Model not trained yet — run python ml/training/train_crop_model.py"}
            </p>
          )}
        </Card>

        <div className="space-y-4">
          {rec.loading && <Loading label={t("recommending")} />}
          <ErrorBox error={rec.error} />
          {!r && !rec.loading && (
            <Notice kind="info">
              N, P, K values are usually given in kg/ha on the Soil Health Card. Rainfall here means the typical rainfall (mm) for the growing season, as in the training dataset.
            </Notice>
          )}
          {r && !rec.loading && (
            <>
              <Card>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-ink-muted">{t("recommended_crop")}</p>
                    <p className="font-display text-3xl font-bold text-forest-800">{cropLabel(r.candidates[0])}</p>
                  </div>
                  <Badge kind="estimated">ML model</Badge>
                </div>
                <div className="mt-4"><ConfidenceBar value={r.confidence} label={t("probability")} /></div>
                <p className="mt-4">{r.explanation}</p>
                {r.warnings.map((w) => <div className="mt-3" key={w}><Notice kind="warn">{w}</Notice></div>)}
              </Card>

              <Card title={t("why")}>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[420px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-line text-ink-muted">
                        <th className="py-2 font-medium"></th><th className="font-medium">{t("your_value")}</th>
                        <th className="font-medium">{t("typical_range")}</th><th className="sr-only">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.candidates[0].comparison.map((row) => (
                        <tr key={row.feature} className="border-b border-line/60">
                          <td className="py-2 font-medium">{t(`field_${row.feature}`)}</td>
                          <td className="tabular-nums">{row.value}</td>
                          <td className="tabular-nums">{row.typical_low} – {row.typical_high}</td>
                          <td>
                            {row.within_typical
                              ? <span className="inline-flex items-center gap-1 text-forest-700"><CheckCircle2 size={16} aria-hidden /> OK</span>
                              : <span className="inline-flex items-center gap-1 text-soil-700"><CircleAlert size={16} aria-hidden /> Differs</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-2 text-xs text-ink-muted">Typical range = 10th–90th percentile of this crop in the training data.</p>
              </Card>

              <Card title={t("alternatives")}>
                <HorizontalBarChart
                  data={r.candidates.map((c) => ({ label: cropLabel(c), p: Math.round(c.probability * 1000) / 10 }))}
                  dataKey="p"
                  format={(v) => `${v}%`}
                  valueLabel={t("probability")}
                />
              </Card>
              <Notice kind="warn">{r.disclaimer}</Notice>
            </>
          )}
        </div>
      </div>
    </>
  );
}
