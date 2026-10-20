import { useEffect, useState } from "react";
import { Inbox, KeyRound, LogOut, PhoneCall, Send } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, Empty, ErrorBox, Field, Loading, Notice, PageHeader, formatDate, titleCase } from "../components/ui";

// The code is kept only for this browser tab (sessionStorage) and cleared on sign-out.
const session = {
  get: (k) => { try { return sessionStorage.getItem(k) || ""; } catch { return ""; } },
  set: (k, v) => { try { v ? sessionStorage.setItem(k, v) : sessionStorage.removeItem(k); } catch { /* ignore */ } },
};

function CodeGate({ onOk }) {
  const { t } = useApp();
  const [code, setCode] = useState("");
  const check = useAsync((c) => api.expertVerify(c), [], { immediate: false });

  async function submit(e) {
    e.preventDefault();
    if (await check.run(code.trim())) onOk(code.trim());
  }

  return (
    <Card className="mx-auto max-w-md">
      <form onSubmit={submit} className="space-y-4">
        <Field label={t("expert_code")} htmlFor="code" hint={t("expert_code_hint")}>
          <input id="code" className="input" type="password" autoComplete="off" value={code} onChange={(e) => setCode(e.target.value)} />
        </Field>
        <ErrorBox error={check.error} />
        <button className="btn btn-primary w-full" disabled={check.loading || !code.trim()}>
          <KeyRound size={18} aria-hidden /> {t("expert_open_panel")}
        </button>
      </form>
    </Card>
  );
}

function QuestionCard({ q, code, expertName, setExpertName, onAnswered }) {
  const { t, lang } = useApp();
  const [answer, setAnswer] = useState("");
  const send = useAsync((body) => api.expertAnswer(code, q.id, body), [code, q.id], { immediate: false });

  async function submit(e) {
    e.preventDefault();
    if (await send.run({ expert_name: expertName.trim(), answer: answer.trim() })) onAnswered(q.id);
  }

  return (
    <Card>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
        <Badge>{t(`cat_${q.category}`)}</Badge>
        {q.crop && <Badge>{titleCase(q.crop)}</Badge>}
        <Badge>{q.language === "hi" ? "हिंदी" : "English"}</Badge>
        <span className="text-ink-muted">#{q.id} · {formatDate(q.created_at, lang)}</span>
      </div>
      <p className="text-sm text-ink-muted">
        {q.farmer_name}
        {q.phone && <> · <a className="inline-flex items-center gap-1 font-semibold text-forest-700" href={`tel:${q.phone}`}><PhoneCall size={14} aria-hidden />{q.phone}</a></>}
      </p>
      <p className="mt-2 whitespace-pre-line text-lg">{q.question}</p>

      {q.status === "answered" ? (
        <div className="mt-3 rounded-xl bg-leaf-50 p-3">
          <p className="whitespace-pre-line">{q.answer}</p>
          <p className="mt-1 text-sm text-ink-muted">— {q.expert_name}, {formatDate(q.answered_at, lang)}</p>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-4 space-y-3">
          <Field label={t("expert_your_answer")} htmlFor={`a-${q.id}`}>
            <textarea id={`a-${q.id}`} className="input min-h-[110px]" value={answer} maxLength={4000} onChange={(e) => setAnswer(e.target.value)} />
          </Field>
          <Field label={t("expert_name_label")} htmlFor={`n-${q.id}`}>
            <input id={`n-${q.id}`} className="input" value={expertName} maxLength={100} placeholder="e.g. Dr. Sharma, KVK Ludhiana"
              onChange={(e) => setExpertName(e.target.value)} />
          </Field>
          <ErrorBox error={send.error} />
          <button className="btn btn-primary" disabled={send.loading || answer.trim().length < 5 || expertName.trim().length < 2}>
            <Send size={18} aria-hidden /> {send.loading ? t("saving") : t("expert_send_answer")}
          </button>
        </form>
      )}
    </Card>
  );
}

export default function ExpertPanel() {
  const { t } = useApp();
  const [code, setCodeState] = useState(() => session.get("kv_expert_code"));
  const [expertName, setExpertNameState] = useState(() => session.get("kv_expert_name"));
  const [tab, setTab] = useState("open");
  const inbox = useAsync(() => (code ? api.expertInbox(code, tab) : Promise.resolve(null)), [code, tab]);

  const setCode = (c) => { setCodeState(c); session.set("kv_expert_code", c); };
  const setExpertName = (n) => { setExpertNameState(n); session.set("kv_expert_name", n); };

  // A wrong/changed code on the server signs the expert out
  useEffect(() => {
    if (inbox.error?.code === "INVALID_EXPERT_CODE") { setCodeState(""); session.set("kv_expert_code", ""); }
  }, [inbox.error]);

  return (
    <>
      <PageHeader title={t("expert_panel_title")} subtitle={t("expert_panel_subtitle")} icon={Inbox}>
        {code && <button className="btn btn-secondary" onClick={() => setCode("")}><LogOut size={16} aria-hidden /> {t("expert_sign_out")}</button>}
      </PageHeader>

      {!code ? <CodeGate onOk={setCode} /> : (
        <>
          <div className="mb-4 flex gap-2" role="tablist">
            {["open", "answered"].map((s) => (
              <button key={s} role="tab" aria-selected={tab === s} onClick={() => setTab(s)}
                className={`rounded-full px-4 py-2 font-semibold ${tab === s ? "bg-forest-700 text-white" : "border border-line bg-white text-forest-700"}`}>
                {t(`expert_tab_${s}`)}
              </button>
            ))}
          </div>
          {inbox.loading && <Loading />}
          <ErrorBox error={inbox.error} onRetry={inbox.run} />
          {inbox.data?.length === 0 && <Empty icon={Inbox}>{t(tab === "open" ? "expert_inbox_empty" : "no_history")}</Empty>}
          <div className="space-y-4">
            {inbox.data?.map((q) => (
              <QuestionCard key={q.id} q={q} code={code} expertName={expertName} setExpertName={setExpertName}
                onAnswered={(id) => inbox.setData(inbox.data.filter((x) => x.id !== id))} />
            ))}
          </div>
          <div className="mt-6"><Notice kind="info">{t("expert_panel_note")}</Notice></div>
        </>
      )}
    </>
  );
}
