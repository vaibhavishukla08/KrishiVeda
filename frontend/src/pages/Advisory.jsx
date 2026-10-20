import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bot, Loader2, MessageCircle, Send, User } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, ErrorBox, Notice, PageHeader } from "../components/ui";

export default function Advisory() {
  const { t, lang, farmerId } = useApp();
  const status = useAsync(() => api.advisoryStatus(), []);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, busy]);

  async function ask(question) {
    const q = question.trim();
    if (q.length < 3 || busy) return;
    setText("");
    setError(null);
    // Only previous AI question/answer pairs are useful context for the AI model
    const history = [];
    messages.forEach((m, i) => {
      if (m.role === "assistant" && m.provider !== "knowledge_base" && messages[i - 1]?.role === "user") {
        history.push({ role: "user", content: messages[i - 1].content }, { role: "assistant", content: m.content });
      }
    });
    setMessages((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const res = await api.ask({ question: q, language: lang, farmer_id: farmerId || undefined, history: history.slice(-6) });
      setMessages((m) => [...m, { role: "assistant", content: res.answer, provider: res.provider, notice: res.notice }]);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  const ai = status.data?.ai_configured;

  return (
    <>
      <PageHeader title={t("advisory_title")} subtitle={t("advisory_subtitle")} icon={MessageCircle}>
        {status.data && <Badge kind={ai ? "live" : "demo"}>{ai ? `${t("ai_answer")} · ${status.data.provider === "gemini" ? "Gemini" : "Claude"}` : t("offline_answer")}</Badge>}
      </PageHeader>

      {status.data && !ai && (
        <div className="mb-4">
          <Notice kind="warn">{t("ai_not_configured")}</Notice>
        </div>
      )}
      <div className="mb-4">
        <Notice kind="info">
          {t("advisory_expert_hint")} <Link to="/expert" className="font-semibold underline">{t("nav_expert")} →</Link>
        </Notice>
      </div>

      <div className="card flex min-h-[420px] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-5" aria-live="polite">
          {messages.length === 0 && (
            <div>
              <p className="mb-3 font-semibold text-forest-800">{t("suggested")}</p>
              <div className="flex flex-wrap gap-2">
                {["sq_1", "sq_2", "sq_3", "sq_4"].map((k) => (
                  <button key={k} className="rounded-full border border-leaf-500/40 bg-leaf-50 px-4 py-2 text-left text-sm font-medium text-forest-700 hover:bg-leaf-100" onClick={() => ask(t(k))}>
                    {t(k)}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${m.role === "user" ? "bg-wheat-100 text-soil-700" : "bg-leaf-100 text-forest-700"}`}>
                {m.role === "user" ? <User size={18} aria-hidden /> : <Bot size={18} aria-hidden />}
              </span>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${m.role === "user" ? "bg-forest-700 text-white" : "border border-line bg-leaf-50/60"}`}>
                <p className="whitespace-pre-line">{m.content}</p>
                {m.role === "assistant" && (
                  <p className="mt-2 text-xs text-ink-muted">
                    {m.provider !== "knowledge_base" ? t("ai_answer") : t("offline_answer")}{m.notice ? ` · ${m.notice}` : ""}
                  </p>
                )}
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex items-center gap-2 text-ink-muted" role="status">
              <Loader2 className="animate-spin" size={18} aria-hidden /> {t("thinking")}
            </div>
          )}
          <div ref={endRef} />
        </div>
        <div className="border-t border-line p-3 sm:p-4">
          <ErrorBox error={error} />
          <form className="mt-1 flex gap-2" onSubmit={(e) => { e.preventDefault(); ask(text); }}>
            <label htmlFor="q" className="sr-only">{t("ask_placeholder")}</label>
            <input id="q" className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("ask_placeholder")} maxLength={1000} />
            <button className="btn btn-primary shrink-0" disabled={busy || text.trim().length < 3} aria-label={t("ask")}>
              <Send size={18} aria-hidden /> <span className="hidden sm:inline">{t("ask")}</span>
            </button>
          </form>
          <p className="mt-2 text-xs text-ink-muted">{t("advisory_disclaimer")}</p>
        </div>
      </div>
    </>
  );
}
