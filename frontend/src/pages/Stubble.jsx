import { Flame, Recycle, Tractor } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, ErrorBox, Loading, Notice, PageHeader } from "../components/ui";

export default function Stubble() {
  const { t, lang } = useApp();
  const res = useAsync(() => api.stubble(), []);
  const hi = lang === "hi";
  const d = res.data;
  return (
    <>
      <PageHeader title={t("stubble_title")} subtitle={t("stubble_subtitle")} icon={Flame} />
      {res.loading && <Loading />}
      <ErrorBox error={res.error} onRetry={res.run} />
      {d && (
        <div className="space-y-6">
          <Card title={t("why_not_burn")} icon={Flame} className="border-[#e0a48f] bg-[#fdf6f3]">
            <ul className="list-disc space-y-1.5 pl-5">{(hi ? d.why_not_burn_hi : d.why_not_burn).map((x) => <li key={x}>{x}</li>)}</ul>
          </Card>
          <div>
            <h2 className="mb-3 text-xl font-bold text-forest-800">{t("alternatives_title")}</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {d.options.map((o) => (
                <Card key={o.id}>
                  <div className="flex items-center gap-2">
                    {o.type === "In-situ" ? <Tractor size={20} className="text-leaf-600" aria-hidden /> : <Recycle size={20} className="text-leaf-600" aria-hidden />}
                    <Badge kind={o.type === "In-situ" ? "live" : "estimated"}>{o.type}</Badge>
                  </div>
                  <h3 className="mt-2 text-lg font-semibold text-forest-800">{hi ? o.name_hi : o.name}</h3>
                  <p className="mt-1 text-ink-muted">{hi ? o.description_hi : o.description}</p>
                </Card>
              ))}
            </div>
          </div>
          <Notice kind="success"><strong>{t("support_title")}:</strong> {hi ? d.support_hi : d.support}</Notice>
        </div>
      )}
    </>
  );
}
