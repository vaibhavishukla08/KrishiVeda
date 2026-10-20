import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Clock, ExternalLink, Headset, PhoneCall, RefreshCw, Send } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { validatePhone } from "../utils/validation";
import { Badge, Card, Empty, ErrorBox, Field, Loading, Notice, PageHeader, formatDate, titleCase } from "../components/ui";

export const EXPERT_CATEGORIES = ["disease", "pest", "irrigation", "soil", "weather", "market", "other"];

function MyQuestions({ farmerId, refreshKey }) {
  const { t, lang } = useApp();
  const res = useAsync(() => api.myExpertQuestions(farmerId), [farmerId, refreshKey]);
  return (
    <Card
      title={t("expert_my_questions")}
      action={<button className="btn btn-secondary !min-h-0 !py-1.5" onClick={res.run} aria-label={t("refresh")} title={t("refresh")}><RefreshCw size={16} aria-hidden /></button>}
    >
      {res.loading && <Loading />}
      <ErrorBox error={res.error} onRetry={res.run} />
      {res.data?.length === 0 && <Empty>{t("expert_no_questions")}</Empty>}
      <ul className="space-y-3">
        {res.data?.map((q) => (
          <li key={q.id} className="rounded-2xl border border-line p-4">
            <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
              {q.status === "answered"
                ? <Badge kind="live"><CheckCircle2 size={13} aria-hidden /> {t("expert_answered")}</Badge>
                : <Badge kind="demo"><Clock size={13} aria-hidden /> {t("expert_waiting")}</Badge>}
              <Badge>{t(`cat_${q.category}`)}</Badge>
              {q.crop && <Badge>{titleCase(q.crop)}</Badge>}
              <span className="text-ink-muted">{formatDate(q.created_at, lang)}</span>
            </div>
            <p className="font-medium">{q.question}</p>
            {q.answer && (
              <div className="mt-3 rounded-xl bg-leaf-50 p-3">
                <p className="whitespace-pre-line">{q.answer}</p>
                <p className="mt-1 text-sm text-ink-muted">— {q.expert_name}, {formatDate(q.answered_at, lang)}</p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export default function AskExpert() {
  const { t, lang, farmer, farmerId, farm } = useApp();
  const contacts = useAsync(() => api.expertContacts(), []);
  const send = useAsync((body) => api.askExpert(body), [], { immediate: false });
  const [form, setForm] = useState({ farmer_name: "", phone: "", crop: "", category: "disease", question: "" });
  const [errors, setErrors] = useState({});
  const [sentCount, setSentCount] = useState(0);

  // Pre-fill from the farm profile
  useEffect(() => {
    if (!farmer) return;
    setForm((f) => ({
      ...f,
      farmer_name: f.farmer_name || farmer.name,
      phone: f.phone || farmer.phone || "",
      crop: f.crop || farm?.crops?.[0]?.crop_name || "",
    }));
  }, [farmer, farm]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    const errs = {};
    if (form.farmer_name.trim().length < 2) errs.farmer_name = t("err_required");
    if (!validatePhone(form.phone.trim())) errs.phone = t("err_phone");
    if (form.question.trim().length < 10) errs.question = t("expert_err_question");
    setErrors(errs);
    if (Object.keys(errs).length) return;
    const saved = await send.run({
      farmer_id: farmerId || null,
      farmer_name: form.farmer_name.trim(),
      phone: form.phone.trim() || null,
      crop: form.crop.trim() || null,
      category: form.category,
      question: form.question.trim(),
      language: lang,
    });
    if (saved) {
      setForm((f) => ({ ...f, question: "" }));
      setSentCount((n) => n + 1);
    }
  }

  const c = contacts.data;
  return (
    <>
      <PageHeader title={t("expert_title")} subtitle={t("expert_subtitle")} icon={Headset} />

      {/* Talk to an expert right now */}
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Card className="border-leaf-500/40 bg-leaf-50/60">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-forest-800"><PhoneCall size={20} className="text-leaf-600" aria-hidden />{t("expert_call_title")}</h2>
          <p className="mt-1 text-ink-muted">{t("expert_call_text")}</p>
          <a href="tel:18001801551" className="btn btn-primary mt-3 w-full sm:w-auto">
            <PhoneCall size={18} aria-hidden /> {c?.helpline.phone || "1800-180-1551"}
          </a>
          {c && <p className="mt-2 text-sm text-ink-muted">{c.helpline.hours} · {c.helpline.note}</p>}
        </Card>
        <Card>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-forest-800"><ExternalLink size={20} className="text-leaf-600" aria-hidden />{t("expert_kvk_title")}</h2>
          <p className="mt-1 text-ink-muted">{t("expert_kvk_text")}</p>
          <a href={c?.kvk_portal.url || "https://kvk.icar.gov.in"} target="_blank" rel="noreferrer" className="btn btn-secondary mt-3 w-full sm:w-auto">
            {t("expert_kvk_btn")} <ExternalLink size={16} aria-hidden />
          </a>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Send a question */}
        <Card title={t("expert_form_title")} icon={Send}>
          <p className="mb-4 text-sm text-ink-muted">{t("expert_form_text")}</p>
          <form onSubmit={submit} noValidate className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("your_name")} htmlFor="ex-name" error={errors.farmer_name}>
                <input id="ex-name" className="input" value={form.farmer_name} onChange={(e) => set("farmer_name", e.target.value)} maxLength={100} />
              </Field>
              <Field label={t("expert_phone")} htmlFor="ex-phone" error={errors.phone} hint={t("expert_phone_hint")}>
                <input id="ex-phone" className="input" inputMode="numeric" value={form.phone} maxLength={10}
                  onChange={(e) => set("phone", e.target.value.replace(/\D/g, ""))} />
              </Field>
              <Field label={t("crop")} htmlFor="ex-crop">
                <input id="ex-crop" className="input" value={form.crop} onChange={(e) => set("crop", e.target.value)} maxLength={40} placeholder="e.g. wheat" />
              </Field>
              <Field label={t("expert_category")} htmlFor="ex-cat">
                <select id="ex-cat" className="input" value={form.category} onChange={(e) => set("category", e.target.value)}>
                  {EXPERT_CATEGORIES.map((cat) => <option key={cat} value={cat}>{t(`cat_${cat}`)}</option>)}
                </select>
              </Field>
            </div>
            <Field label={t("expert_question")} htmlFor="ex-q" error={errors.question}>
              <textarea id="ex-q" className="input min-h-[120px]" value={form.question} maxLength={2000}
                onChange={(e) => set("question", e.target.value)} placeholder={t("expert_question_ph")} />
            </Field>
            <ErrorBox error={send.error} />
            {sentCount > 0 && !send.loading && !send.error && <Notice kind="success">{t("expert_sent")}</Notice>}
            <button className="btn btn-primary w-full sm:w-auto" disabled={send.loading}>
              <Send size={18} aria-hidden /> {send.loading ? t("saving") : t("expert_send")}
            </button>
          </form>
        </Card>

        {/* Replies */}
        <div className="space-y-4">
          {farmerId ? <MyQuestions farmerId={farmerId} refreshKey={sentCount} /> : (
            <Notice kind="info">
              {t("expert_need_profile")} <Link to="/profile" className="font-semibold underline">{t("dash_setup_btn")}</Link>
            </Notice>
          )}
          <Notice kind="info">
            {t("expert_ai_hint")} <Link to="/advisory" className="font-semibold underline">{t("nav_advisory")}</Link>
          </Notice>
          <p className="text-sm text-ink-muted">
            {t("expert_are_you")} <Link to="/expert/panel" className="font-semibold text-forest-700 underline">{t("expert_panel_link")}</Link>
          </p>
        </div>
      </div>
    </>
  );
}
