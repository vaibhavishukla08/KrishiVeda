import { useState } from "react";
import { IndianRupee } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Badge, Card, Empty, ErrorBox, Field, Loading, Notice, PageHeader, formatDate } from "../components/ui";
import { HorizontalBarChart } from "../components/charts";

const STATES = ["Punjab", "Haryana", "Uttar Pradesh", "Madhya Pradesh", "Maharashtra", "Rajasthan"];
const inr = (v) => (v == null ? "–" : `₹${Number(v).toLocaleString("en-IN")}`);

export default function MarketPrices() {
  const { t, lang } = useApp();
  const [commodity, setCommodity] = useState("");
  const [state, setState] = useState("");
  const commodities = useAsync(() => api.commodities(), []);
  const prices = useAsync(() => api.marketPrices({ commodity, state, limit: 100 }), [commodity, state]);
  const d = prices.data;

  return (
    <>
      <PageHeader title={t("market_title")} subtitle={t("market_subtitle")} icon={IndianRupee}>
        {d && <Badge kind={d.mode === "live" ? "live" : "demo"}>{d.mode === "live" ? t("live_data") : t("demo_data")}</Badge>}
      </PageHeader>

      <Card className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("commodity")} htmlFor="commodity">
            <select id="commodity" className="input" value={commodity} onChange={(e) => setCommodity(e.target.value)}>
              <option value="">{t("all")}</option>
              {(commodities.data?.commodities || []).map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label={t("state")} htmlFor="state">
            <select id="state" className="input" value={state} onChange={(e) => setState(e.target.value)}>
              <option value="">{t("all")}</option>
              {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
        </div>
      </Card>

      {d?.notice && <div className="mb-4"><Notice kind={d.mode === "live" ? "info" : "warn"}>{d.notice}</Notice></div>}
      {prices.loading && <Loading />}
      <ErrorBox error={prices.error} onRetry={prices.run} />

      {d && !prices.loading && (d.records.length === 0 ? (
        <Empty icon={IndianRupee}>{t("no_prices")}</Empty>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <Card className="lg:col-span-3" title={t("price_unit")}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-muted">
                    <th className="py-2 font-medium">{t("commodity")}</th><th className="font-medium">{t("market")}</th>
                    <th className="text-right font-medium">{t("min_price")}</th><th className="text-right font-medium">{t("modal_price")}</th>
                    <th className="text-right font-medium">{t("max_price")}</th><th className="pl-3 font-medium">{t("date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {d.records.map((r, i) => (
                    <tr key={i} className="border-b border-line/60">
                      <td className="py-2 font-medium">{r.commodity}</td>
                      <td>{r.market}<span className="block text-xs text-ink-muted">{r.district}, {r.state}</span></td>
                      <td className="text-right tabular-nums">{inr(r.min_price)}</td>
                      <td className="text-right font-semibold tabular-nums">{inr(r.modal_price)}</td>
                      <td className="text-right tabular-nums">{inr(r.max_price)}</td>
                      <td className="pl-3">{formatDate(r.price_date, lang)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-ink-muted">{t("source")}: {d.records[0].source} · {d.records[0].unit}</p>
          </Card>
          {commodity && (
            <Card className="lg:col-span-2" title={t("modal_chart")}>
              <HorizontalBarChart
                data={d.records.map((r) => ({ label: r.market, v: r.modal_price }))}
                dataKey="v"
                format={inr}
                valueLabel={t("modal_price")}
              />
            </Card>
          )}
        </div>
      ))}
    </>
  );
}
