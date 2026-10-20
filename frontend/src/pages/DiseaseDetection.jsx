import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, HelpCircle, ImageOff, Leaf, RotateCcw, ScanSearch, ShieldCheck, Upload } from "lucide-react";
import { useApp } from "../hooks/AppContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { validateImageFile, ALLOWED_IMAGE_TYPES } from "../utils/validation";
import { Badge, Card, ConfidenceBar, ErrorBox, Loading, Notice, PageHeader } from "../components/ui";

const STATUS = {
  healthy: { icon: CheckCircle2, key: "status_healthy", style: "border-leaf-500/40 bg-leaf-50 text-forest-700" },
  diseased: { icon: AlertTriangle, key: "status_diseased", style: "border-[#e0a48f] bg-[#fdf1ee] text-[#8a2f16]" },
  uncertain: { icon: HelpCircle, key: "status_uncertain", style: "border-wheat-500/60 bg-wheat-100 text-soil-700" },
  no_leaf: { icon: ImageOff, key: "status_no_leaf", style: "border-line bg-[#f4f5f1] text-ink-muted" },
};

function labelFor(p, lang) {
  if (p.no_leaf) return lang === "hi" ? "पत्ती नहीं" : "No leaf";
  const crop = lang === "hi" ? p.crop_hi || p.crop : p.crop;
  if (p.healthy) return `${crop} — ${lang === "hi" ? "स्वस्थ" : "Healthy"}`;
  return `${crop} — ${lang === "hi" ? p.disease_hi || p.disease : p.disease}`;
}

function ModelPanel({ info }) {
  const { t, lang } = useApp();
  if (!info) return null;
  return (
    <Card title={t("model_info")} icon={ShieldCheck}>
      {info.available ? (
        <dl className="space-y-1.5 text-sm">
          <div className="flex justify-between gap-2"><dt className="text-ink-muted">CNN</dt><dd className="font-medium">MobileNetV3-Large</dd></div>
          <div className="flex justify-between gap-2"><dt className="text-ink-muted">Version</dt><dd className="font-mono text-xs">{info.version}</dd></div>
          {info.metrics?.test_accuracy != null && (
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{t("test_accuracy")}</dt>
              <dd className="font-medium">{(info.metrics.test_accuracy * 100).toFixed(1)}% <span className="text-ink-muted">({info.metrics.test_images} imgs)</span></dd>
            </div>
          )}
          {info.metrics?.field_test_accuracy != null && (
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{t("field_accuracy")}</dt>
              <dd className="font-medium">{(info.metrics.field_test_accuracy * 100).toFixed(1)}%</dd>
            </div>
          )}
          <div className="flex justify-between gap-2">
            <dt className="text-ink-muted">Dataset</dt>
            <dd className="text-right">{info.metrics?.field_test_accuracy != null ? "PlantVillage + PlantDoc" : "PlantVillage (CC0)"}</dd>
          </div>
        </dl>
      ) : (
        <Notice kind="warn"><strong>{t("model_unavailable_title")}.</strong> {info.reason}</Notice>
      )}
      <h3 className="mb-2 mt-4 text-sm font-semibold">{t("supported_crops")}</h3>
      <div className="flex flex-wrap gap-1.5">
        {[...new Map(info.supported_classes.map((c) => [c.crop, c])).values()].map((c) => (
          <Badge key={c.crop}>{lang === "hi" ? c.crop_hi || c.crop : c.crop}</Badge>
        ))}
      </div>
      {info.available && (
        <p className="mt-3 text-xs text-ink-muted">
          Trained on lab and real-field leaf photos. Field photos are harder, so results below {Math.round(info.confidence_threshold * 100)}% confidence are marked "not sure".
        </p>
      )}
    </Card>
  );
}

function ResultView({ result, preview, onReset }) {
  const { t, lang } = useApp();
  const s = STATUS[result.status];
  const Icon = s.icon;
  const p = result.prediction;
  return (
    <div className="space-y-4">
      <div className="card overflow-hidden">
        <div className="grid md:grid-cols-[minmax(0,280px)_1fr]">
          <img src={preview} alt="Uploaded leaf" className="h-64 w-full object-cover md:h-full" />
          <div className="space-y-4 p-5">
            <div className={`flex items-start gap-3 rounded-2xl border p-4 ${s.style}`}>
              <Icon size={28} className="shrink-0" aria-hidden />
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide">{t(s.key)}</p>
                <p className="text-xl font-bold">{result.status === "no_leaf" ? t("status_no_leaf") : labelFor(p, lang)}</p>
                <p className="mt-1 text-sm">{result.message}</p>
              </div>
            </div>
            <ConfidenceBar value={p.probability} label={t("confidence")} />
            <div>
              <h3 className="mb-2 text-sm font-semibold text-ink-muted">{t("other_possibilities")}</h3>
              <ul className="space-y-1.5">
                {result.top_predictions.slice(1).map((alt) => (
                  <li key={alt.class} className="flex justify-between gap-3 text-sm">
                    <span>{labelFor(alt, lang)}</span>
                    <span className="font-medium tabular-nums">{(alt.probability * 100).toFixed(1)}%</span>
                  </li>
                ))}
              </ul>
            </div>
            <button className="btn btn-primary w-full sm:w-auto" onClick={onReset}>
              <RotateCcw size={18} aria-hidden /> {t("analyze_another")}
            </button>
          </div>
        </div>
      </div>

      {result.advisory && (
        <div className="grid gap-4 md:grid-cols-2">
          {result.advisory.cause && (
            <Card title={t("cause")}><p>{result.advisory.cause}</p></Card>
          )}
          {result.advisory.symptoms && (
            <Card title={t("symptoms")}><p>{result.advisory.symptoms}</p></Card>
          )}
          <Card title={t("what_to_do")}>
            <ol className="list-decimal space-y-1.5 pl-5">{result.advisory.management.map((m) => <li key={m}>{m}</li>)}</ol>
          </Card>
          <Card title={t("prevention")}>
            <ul className="list-disc space-y-1.5 pl-5">{result.advisory.prevention.map((m) => <li key={m}>{m}</li>)}</ul>
          </Card>
        </div>
      )}
      <Notice kind="warn">{result.disclaimer}</Notice>
      <p className="text-xs text-ink-muted">Model {result.model_version}</p>
    </div>
  );
}

export default function DiseaseDetection() {
  const { t, farmerId } = useApp();
  const model = useAsync(() => api.diseaseModel(), []);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const predict = useAsync((f) => api.predictDisease(f, farmerId), [farmerId], { immediate: false });

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  function choose(f) {
    const err = validateImageFile(f);
    setFileError(err);
    predict.setData(null);
    if (err) { setFile(null); setPreview(null); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function reset() {
    setFile(null);
    setPreview(null);
    setFileError(null);
    predict.setData(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  const result = predict.data;
  const unavailable = model.data && !model.data.available;

  return (
    <>
      <PageHeader title={t("disease_title")} subtitle={t("disease_subtitle")} icon={Leaf} />
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          {result ? (
            <ResultView result={result} preview={preview} onReset={reset} />
          ) : (
            <Card>
              {!preview ? (
                <label
                  htmlFor="leaf-file"
                  onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(e) => { e.preventDefault(); setDragging(false); choose(e.dataTransfer.files?.[0]); }}
                  className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-4 py-14 text-center transition-colors ${
                    dragging ? "border-leaf-600 bg-leaf-50" : "border-[#c9d0c4] hover:border-leaf-500 hover:bg-leaf-50/60"
                  }`}
                >
                  <span className="flex h-16 w-16 items-center justify-center rounded-full bg-leaf-100 text-forest-700">
                    <Upload size={30} aria-hidden />
                  </span>
                  <span className="text-lg font-semibold text-forest-800">{t("upload_prompt")}</span>
                  <span className="text-sm text-ink-muted">{t("upload_hint")}</span>
                </label>
              ) : (
                <div className="space-y-4">
                  <img src={preview} alt="Selected leaf preview" className="mx-auto max-h-80 rounded-2xl object-contain" />
                  <p className="text-center text-sm text-ink-muted">{file?.name} · {(file?.size / 1024).toFixed(0)} KB</p>
                  <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
                    <button className="btn btn-primary" onClick={() => predict.run(file)} disabled={predict.loading || unavailable}>
                      <ScanSearch size={18} aria-hidden /> {predict.loading ? t("analyzing") : t("analyze")}
                    </button>
                    <button className="btn btn-secondary" onClick={reset} disabled={predict.loading}>{t("change_photo")}</button>
                  </div>
                  {predict.loading && <Loading label={t("analyzing")} />}
                </div>
              )}
              <input
                ref={inputRef}
                id="leaf-file"
                type="file"
                accept={ALLOWED_IMAGE_TYPES.join(",")}
                className="sr-only"
                onChange={(e) => choose(e.target.files?.[0])}
              />
              {fileError && <p role="alert" className="mt-3 text-center font-medium text-[#a1361b]">{t(fileError)}</p>}
            </Card>
          )}
          <ErrorBox error={predict.error} onRetry={file ? () => predict.run(file) : undefined} />
          {unavailable && <Notice kind="warn"><strong>{t("model_unavailable_title")}.</strong> {model.data.reason}</Notice>}
        </div>

        <aside className="space-y-4">
          <Card title={t("tips_title")}>
            <ul className="space-y-2 text-sm">
              {["tip_1", "tip_2", "tip_3"].map((k) => (
                <li key={k} className="flex gap-2"><CheckCircle2 size={18} className="mt-0.5 shrink-0 text-leaf-600" aria-hidden />{t(k)}</li>
              ))}
            </ul>
          </Card>
          {model.loading ? <Loading /> : <ModelPanel info={model.data} />}
          <ErrorBox error={model.error} onRetry={model.run} />
        </aside>
      </div>
    </>
  );
}
