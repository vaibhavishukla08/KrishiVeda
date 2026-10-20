import { Link } from "react-router-dom";
import { BarChart3 } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Card, Empty, ErrorBox, Loading, PageHeader, titleCase } from "../components/ui";
import { HorizontalBarChart, SimpleBarChart } from "../components/charts";

export default function Analytics() {
  const { t, farmerId } = useApp();
  const res = useAsync(() => (farmerId ? api.stats(farmerId, 30) : Promise.resolve(null)), [farmerId]);
  const s = res.data;

  return (
    <>
      <PageHeader title={t("analytics_title")} subtitle={t("analytics_subtitle")} icon={BarChart3} />
      {!farmerId && <Empty><Link to="/profile" className="font-semibold text-forest-700 underline">{t("need_profile")}</Link></Empty>}
      {res.loading && <Loading />}
      <ErrorBox error={res.error} onRetry={res.run} />
      {s && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card><p className="text-ink-muted">{t("total_checks")}</p><p className="font-display text-4xl font-bold text-forest-800">{s.disease_checks}</p></Card>
            <Card><p className="text-ink-muted">{t("total_recs")}</p><p className="font-display text-4xl font-bold text-forest-800">{s.recommendations}</p></Card>
          </div>
          {s.disease_checks === 0 ? <Empty>{t("no_history")}</Empty> : (
            <div className="grid gap-6 lg:grid-cols-2">
              <Card title={t("checks_per_day")}>
                <SimpleBarChart data={s.checks_per_day.map((d) => ({ label: d.date.slice(5), count: d.count }))} dataKey="count" valueLabel={t("total_checks")} />
              </Card>
              <Card title={t("results_by_status")}>
                <HorizontalBarChart data={Object.entries(s.by_status).map(([k, v]) => ({ label: t(`status_${k}`), v }))} dataKey="v" valueLabel={t("total_checks")} />
              </Card>
              {s.top_diseases.length > 0 && (
                <Card title={t("top_diseases")} className="lg:col-span-2">
                  <HorizontalBarChart data={s.top_diseases.map(([name, v]) => ({ label: name, v }))} dataKey="v" valueLabel={t("total_checks")} />
                </Card>
              )}
            </div>
          )}
          {Object.keys(s.recommended_crops).length > 0 && (
            <Card title={t("total_recs")}>
              <HorizontalBarChart data={Object.entries(s.recommended_crops).map(([k, v]) => ({ label: titleCase(k), v }))} dataKey="v" valueLabel={t("total_recs")} />
            </Card>
          )}
        </div>
      )}
    </>
  );
}
