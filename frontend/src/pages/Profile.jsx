import { useEffect, useState } from "react";
import { Leaf, MessageCircle, Plus, Sprout, User, X } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { validatePhone } from "../utils/validation";
import { Card, Empty, ErrorBox, Field, Loading, Notice, PageHeader, formatDate, titleCase } from "../components/ui";

const SOILS = ["alluvial", "black", "red", "laterite", "sandy", "clay", "loamy"];
const IRRIGATION = ["canal", "tubewell", "drip", "sprinkler", "rainfed"];
const CROP_SUGGESTIONS = ["wheat", "rice", "maize", "cotton", "sugarcane", "potato", "tomato", "soybean", "chickpea", "mustard", "onion"];

const blank = {
  name: "", phone: "", preferred_language: "en", state: "", district: "", village: "",
  farm: { name: "My Farm", location_name: "", area_acres: "", soil_type: "", irrigation_type: "", crops: [] },
};

function toForm(farmer) {
  if (!farmer) return blank;
  const f = farmer.farms?.[0];
  return {
    name: farmer.name, phone: farmer.phone || "", preferred_language: farmer.preferred_language,
    state: farmer.state || "", district: farmer.district || "", village: farmer.village || "",
    farm: f ? {
      name: f.name, location_name: f.location_name || "", area_acres: f.area_acres ?? "",
      soil_type: f.soil_type || "", irrigation_type: f.irrigation_type || "",
      crops: f.crops.map((c) => ({ crop_name: c.crop_name, season: c.season })),
    } : blank.farm,
  };
}

function toPayload(form) {
  const nul = (v) => (v === "" ? null : v);
  return {
    name: form.name.trim(), phone: nul(form.phone.trim()), preferred_language: form.preferred_language,
    state: nul(form.state), district: nul(form.district), village: nul(form.village),
    farm: {
      name: form.farm.name || "My Farm", location_name: nul(form.farm.location_name),
      area_acres: form.farm.area_acres === "" ? null : Number(form.farm.area_acres),
      soil_type: nul(form.farm.soil_type), irrigation_type: nul(form.farm.irrigation_type),
      crops: form.farm.crops,
    },
  };
}

function History({ farmerId }) {
  const { t, lang } = useApp();
  const h = useAsync(() => api.history(farmerId, 10), [farmerId]);
  if (h.loading) return <Loading />;
  if (h.error) return <ErrorBox error={h.error} onRetry={h.run} />;
  const d = h.data;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card title={t("recent_checks")} icon={Leaf}>
        {d.disease_analyses.length === 0 ? <Empty>{t("no_history")}</Empty> : (
          <ul className="divide-y divide-line">
            {d.disease_analyses.map((a) => (
              <li key={a.id} className="flex justify-between gap-2 py-2 text-sm">
                <span><strong>{a.crop || "—"}</strong> · {a.disease || t(`status_${a.status}`)}</span>
                <span className="shrink-0 text-ink-muted">{Math.round(a.confidence * 100)}% · {formatDate(a.created_at, lang)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title={t("total_recs")} icon={Sprout}>
        {d.crop_recommendations.length === 0 ? <Empty>{t("no_history")}</Empty> : (
          <ul className="divide-y divide-line">
            {d.crop_recommendations.map((r) => (
              <li key={r.id} className="flex justify-between gap-2 py-2 text-sm">
                <span><strong>{titleCase(r.recommended_crop)}</strong> · pH {r.inputs.ph}, N {r.inputs.N}</span>
                <span className="shrink-0 text-ink-muted">{formatDate(r.created_at, lang)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title={t("recent_advice")} icon={MessageCircle} className="md:col-span-2">
        {d.advisory.length === 0 ? <Empty>{t("no_history")}</Empty> : (
          <ul className="divide-y divide-line">
            {d.advisory.map((m) => (
              <li key={m.id} className="py-2 text-sm">
                <p className="font-medium">{m.question}</p>
                <p className="line-clamp-2 text-ink-muted">{m.answer}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export default function Profile() {
  const { t, farmer, farmerId, setFarmerId, setFarmer, farmerLoading, setLang } = useApp();
  const [form, setForm] = useState(blank);
  const [cropInput, setCropInput] = useState("");
  const [errors, setErrors] = useState({});
  const save = useAsync(
    (payload) => (farmerId ? api.updateFarmer(farmerId, payload) : api.createFarmer(payload)),
    [farmerId],
    { immediate: false }
  );
  const [savedAt, setSavedAt] = useState(null);

  useEffect(() => { setForm(toForm(farmer)); }, [farmer]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setFarm = (k, v) => setForm((f) => ({ ...f, farm: { ...f.farm, [k]: v } }));

  function addCrop(name) {
    const c = name.trim().toLowerCase();
    if (c.length < 2 || form.farm.crops.some((x) => x.crop_name === c)) return;
    setFarm("crops", [...form.farm.crops, { crop_name: c, season: null }]);
    setCropInput("");
  }

  async function submit(e) {
    e.preventDefault();
    const errs = {};
    if (form.name.trim().length < 2) errs.name = t("err_required");
    if (!validatePhone(form.phone.trim())) errs.phone = t("err_phone");
    if (form.farm.area_acres !== "" && !(Number(form.farm.area_acres) > 0)) errs.area = t("err_range");
    setErrors(errs);
    if (Object.keys(errs).length) return;
    const saved = await save.run(toPayload(form));
    if (saved) {
      setFarmer(saved);
      setFarmerId(saved.id);
      setLang(saved.preferred_language);
      setSavedAt(Date.now());
    }
  }

  if (farmerLoading) return <Loading />;

  return (
    <>
      <PageHeader title={t("profile_title")} subtitle={t("profile_subtitle")} icon={User} />
      <form onSubmit={submit} noValidate className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title={t("your_name")}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("your_name")} htmlFor="name" error={errors.name}>
                <input id="name" className="input" value={form.name} onChange={(e) => set("name", e.target.value)} maxLength={100} required />
              </Field>
              <Field label={t("phone")} htmlFor="phone" error={errors.phone}>
                <input id="phone" className="input" inputMode="numeric" value={form.phone} onChange={(e) => set("phone", e.target.value.replace(/\D/g, ""))} maxLength={10} />
              </Field>
              <Field label={t("language")} htmlFor="lang">
                <select id="lang" className="input" value={form.preferred_language} onChange={(e) => set("preferred_language", e.target.value)}>
                  <option value="en">English</option>
                  <option value="hi">हिंदी</option>
                </select>
              </Field>
              <Field label={t("state")} htmlFor="state">
                <input id="state" className="input" value={form.state} onChange={(e) => set("state", e.target.value)} maxLength={60} />
              </Field>
              <Field label={t("district")} htmlFor="district">
                <input id="district" className="input" value={form.district} onChange={(e) => set("district", e.target.value)} maxLength={60} />
              </Field>
              <Field label={t("village")} htmlFor="village">
                <input id="village" className="input" value={form.village} onChange={(e) => set("village", e.target.value)} maxLength={100} />
              </Field>
            </div>
          </Card>

          <Card title={t("my_farm")}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("farm_name")} htmlFor="farm-name">
                <input id="farm-name" className="input" value={form.farm.name} onChange={(e) => setFarm("name", e.target.value)} maxLength={100} />
              </Field>
              <Field label={t("farm_location")} htmlFor="farm-loc" hint="e.g. Ludhiana">
                <input id="farm-loc" className="input" value={form.farm.location_name} onChange={(e) => setFarm("location_name", e.target.value)} maxLength={120} />
              </Field>
              <Field label={t("farm_area")} htmlFor="farm-area" error={errors.area}>
                <input id="farm-area" className="input" type="number" min="0.01" step="0.01" value={form.farm.area_acres} onChange={(e) => setFarm("area_acres", e.target.value)} />
              </Field>
              <Field label={t("soil_type")} htmlFor="soil">
                <select id="soil" className="input" value={form.farm.soil_type} onChange={(e) => setFarm("soil_type", e.target.value)}>
                  <option value="">—</option>
                  {SOILS.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
                </select>
              </Field>
              <Field label={t("irrigation_type")} htmlFor="irr">
                <select id="irr" className="input" value={form.farm.irrigation_type} onChange={(e) => setFarm("irrigation_type", e.target.value)}>
                  <option value="">—</option>
                  {IRRIGATION.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
                </select>
              </Field>
            </div>
            <div className="mt-4">
              <label className="label" htmlFor="crop-in">{t("your_crops")}</label>
              <div className="mb-2 flex flex-wrap gap-2">
                {form.farm.crops.map((c) => (
                  <span key={c.crop_name} className="inline-flex items-center gap-1 rounded-full bg-leaf-100 py-1 pl-3 pr-1 text-sm font-medium text-forest-700">
                    {titleCase(c.crop_name)}
                    <button type="button" className="rounded-full p-1 hover:bg-white/60" aria-label={`Remove ${c.crop_name}`}
                      onClick={() => setFarm("crops", form.farm.crops.filter((x) => x.crop_name !== c.crop_name))}>
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input id="crop-in" className="input" list="crop-list" value={cropInput} onChange={(e) => setCropInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addCrop(cropInput); } }} maxLength={40} />
                <datalist id="crop-list">{CROP_SUGGESTIONS.map((c) => <option key={c} value={c} />)}</datalist>
                <button type="button" className="btn btn-secondary shrink-0" onClick={() => addCrop(cropInput)}>
                  <Plus size={16} aria-hidden /> {t("add_crop")}
                </button>
              </div>
            </div>
          </Card>
        </div>

        <ErrorBox error={save.error} />
        {savedAt && !save.loading && !save.error && <Notice kind="success">{t("profile_saved")}</Notice>}
        <button className="btn btn-primary w-full sm:w-auto" disabled={save.loading}>
          {save.loading ? t("saving") : t("save")}
        </button>
      </form>

      {farmerId && (
        <section className="mt-10">
          <h2 className="mb-4 text-xl font-bold text-forest-800">{t("history")}</h2>
          <History farmerId={farmerId} key={savedAt} />
        </section>
      )}
    </>
  );
}
