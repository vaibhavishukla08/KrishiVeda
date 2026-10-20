import { ExternalLink, Landmark, Phone } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, ErrorBox, Loading, Notice, PageHeader } from "../components/ui";

export default function Schemes() {
  const { t, lang } = useApp();
  const res = useAsync(() => api.schemes(), []);
  const hi = lang === "hi";
  return (
    <>
      <PageHeader title={t("schemes_title")} subtitle={t("schemes_subtitle")} icon={Landmark} />
      {res.loading && <Loading />}
      <ErrorBox error={res.error} onRetry={res.run} />
      {res.data && (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-2">
            {res.data.schemes.map((s) => (
              <Card key={s.id}>
                <Badge>{s.category}</Badge>
                <h2 className="mt-2 text-lg font-semibold text-forest-800">{hi ? s.name_hi : s.name}</h2>
                <p className="mt-1 text-ink-muted">{hi ? s.summary_hi : s.summary}</p>
                <a href={s.url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 font-semibold text-forest-700 hover:underline">
                  {t("visit_site")} <ExternalLink size={15} aria-hidden />
                </a>
              </Card>
            ))}
          </div>
          {res.data.helplines.map((h) => (
            <Card key={h.phone} title={t("helpline")} icon={Phone}>
              <p className="text-lg"><strong>{hi ? h.name_hi : h.name}</strong>: <a className="font-bold text-forest-700" href={`tel:${h.phone}`}>{h.phone}</a> <span className="text-ink-muted">({h.note})</span></p>
            </Card>
          ))}
          <div className="mt-4"><Notice kind="info">{res.data.note}</Notice></div>
        </>
      )}
    </>
  );
}
