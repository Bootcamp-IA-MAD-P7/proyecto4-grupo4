import React, { useCallback, useEffect, useState } from "react";

import { getMetrics, getPredictions, getRetrainStatus, postRetrain } from "../api";

function fmt(value, decimals = 4) {
  if (value == null) return "—";
  return Number(value).toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function computeABMetrics(predictions) {
  const groups = {};
  for (const p of predictions) {
    const version = p.model_version ?? "prod";
    if (!groups[version]) groups[version] = { sumAE: 0, count: 0 };
    if (p.actual_multiple != null && p.predicted_multiple != null) {
      groups[version].sumAE += Math.abs(p.actual_multiple - p.predicted_multiple);
      groups[version].count += 1;
    }
  }
  return Object.entries(groups).map(([version, g]) => ({
    version,
    mae: g.count > 0 ? g.sumAE / g.count : null,
    n: predictions.filter((p) => (p.model_version ?? "prod") === version).length,
  }));
}

function Toast({ message, type }) {
  if (!message) return null;
  return (
    <div className={`mlops-toast mlops-toast-${type}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}

const DECISION_LABELS = {
  promoted: "Promovido a producción",
  candidate: "Candidato A/B",
  discarded: "Descartado",
  skipped: "Completado",
};

function RetrainStatusBanner({ status, onDismiss }) {
  if (!status || status.status === "idle") return null;

  const tone =
    status.status === "failed"
      ? "error"
      : status.status === "running"
        ? "running"
        : status.decision === "promoted"
          ? "success"
          : status.decision === "candidate"
            ? "warn"
            : status.decision === "discarded"
              ? "neutral"
              : "success";

  const title =
    status.status === "running"
      ? "Reentrenamiento en curso"
      : status.status === "failed"
        ? "Reentrenamiento fallido"
        : DECISION_LABELS[status.decision] ?? "Reentrenamiento finalizado";

  return (
    <div className={`mlops-retrain-banner mlops-retrain-banner-${tone}`} role="status" aria-live="polite">
      <div className="mlops-retrain-banner-copy">
        <strong>{title}</strong>
        <p>{status.message}</p>
        {status.status === "running" ? (
          <p className="mlops-retrain-banner-hint">
            Puedes seguir usando la app. La API recargará el modelo al terminar — no hace falta reiniciar contenedores.
          </p>
        ) : null}
        {status.status === "completed" && status.details?.model_reloaded === false ? (
          <p className="mlops-retrain-banner-hint mlops-retrain-banner-hint-warn">
            No se pudo recargar el modelo en memoria. Reinicia el contenedor API para aplicar cambios.
          </p>
        ) : null}
      </div>
      {status.status !== "running" && onDismiss ? (
        <button className="mlops-retrain-banner-dismiss" onClick={onDismiss} type="button">
          Cerrar
        </button>
      ) : null}
    </div>
  );
}

function RetrainConfirmModal({ open, loading, onCancel, onConfirm }) {
  useEffect(() => {
    if (!open) return undefined;
    function onKeyDown(event) {
      if (event.key === "Escape" && !loading) onCancel();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, loading, onCancel]);

  if (!open) return null;

  return (
    <div className="mlops-modal-backdrop" role="presentation" onClick={onCancel}>
      <div
        className="mlops-modal"
        role="dialog"
        aria-labelledby="retrain-modal-title"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mlops-modal-title" id="retrain-modal-title">
          ¿Iniciar reentrenamiento?
        </h3>
        <div className="mlops-modal-body">
          <p>El proceso corre en <strong>segundo plano</strong> (2–5 min) y no interrumpe las predicciones.</p>
          <ul>
            <li>Verás un <strong>banner de progreso</strong> arriba del panel con el resultado final.</li>
            <li>Se ejecutará Optuna + K-Fold (con feedback real si hay ≥5 filas confirmadas).</li>
            <li>Según el quality gate: promoción a producción, candidato A/B o descarte.</li>
            <li>La API recarga el modelo al terminar — <strong>no hace falta reiniciar contenedores</strong> en condiciones normales.</li>
          </ul>
        </div>
        <div className="mlops-modal-actions">
          <button className="mlops-btn" disabled={loading} onClick={onCancel} type="button">
            Cancelar
          </button>
          <button className="mlops-btn mlops-btn-primary" disabled={loading} onClick={onConfirm} type="button">
            {loading ? "Iniciando…" : "Confirmar reentrenamiento"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RetrainSection({ onRetrained, onRetrainStarted, retrainRunning }) {
  const [status, setStatus] = useState("idle");
  const [toast, setToast] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  async function handleRetrain() {
    setStatus("loading");
    setToast(null);
    try {
      const res = await postRetrain();
      setStatus("idle");
      setModalOpen(false);
      setToast({
        message: `✓ ${res.message ?? "Reentrenamiento iniciado."} Ver progreso arriba.`,
        type: "success",
      });
      if (onRetrainStarted) onRetrainStarted();
      if (onRetrained) onRetrained();
      setTimeout(() => setToast(null), 8000);
    } catch (err) {
      setStatus("idle");
      setToast({ message: `✗ ${err.message}`, type: "error" });
      setTimeout(() => setToast(null), 6000);
    }
  }

  return (
    <div className="mlops-card">
      <RetrainConfirmModal
        loading={status === "loading"}
        open={modalOpen}
        onCancel={() => status !== "loading" && setModalOpen(false)}
        onConfirm={handleRetrain}
      />
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Control de Reentrenamiento</h3>
      </div>
      <p className="mlops-hint mlops-hint-block">
        Lanza un reentrenamiento completo con K-Fold + Optuna en segundo plano. El banner superior
        mostrará el progreso y el resultado (promovido, candidato A/B o descartado).
      </p>
      <button
        className="mlops-btn mlops-btn-primary"
        disabled={status === "loading" || retrainRunning}
        onClick={() => setModalOpen(true)}
        type="button"
      >
        {retrainRunning
          ? "Reentrenamiento en curso…"
          : status === "loading"
            ? "Iniciando reentrenamiento…"
            : "⟳ Reentrenar Modelo (Optuna + K-Fold)"}
      </button>
      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
}

function ModelVersionSection({ predictions, metricsData }) {
  const versions = [...new Set(predictions.map((p) => p.model_version ?? "prod"))];
  const activeVersion = versions.length > 0 ? versions[0] : "prod";

  return (
    <div className="mlops-card">
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Versión del Modelo (A/B Testing)</h3>
      </div>
      <div className="mlops-ab-grid">
        {versions.map((v) => (
          <div key={v} className={`mlops-ab-chip mlops-badge-${v}`}>
            <span className="mlops-ab-label">Modelo activo</span>
            <span className="mlops-ab-version">{v}</span>
            <span className="mlops-ab-count">
              {predictions.filter((p) => (p.model_version ?? "prod") === v).length} predicciones
            </span>
          </div>
        ))}
        {versions.length === 0 && (
          <p className="mlops-hint">Sin predicciones registradas aún.</p>
        )}
      </div>
      {metricsData && (
        <div className="mlops-meta">
          <span className="mlops-meta-item">
            Versión métricas: <strong>{metricsData.model_version ?? activeVersion}</strong>
          </span>
        </div>
      )}
    </div>
  );
}

function ABMetricsSection({ predictions }) {
  const abData = computeABMetrics(predictions);
  const hasFeedback = abData.some((g) => g.mae != null);

  return (
    <div className="mlops-card">
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Métricas A/B por Versión</h3>
        <span className="mlops-hint">MAE medio del múltiplo calculado desde el feedback recibido.</span>
      </div>
      {!hasFeedback ? (
        <p className="mlops-status">Sin feedback real registrado. Introduce valores reales en la tabla para activar las métricas A/B.</p>
      ) : (
        <table className="mlops-table mlops-table-compact">
          <thead>
            <tr>
              <th className="mlops-th">Versión</th>
              <th className="mlops-th">Predicciones</th>
              <th className="mlops-th">MAE múltiplo</th>
            </tr>
          </thead>
          <tbody>
            {abData.map((g) => (
              <tr key={g.version} className="mlops-tr">
                <td className="mlops-td">
                  <span className={`mlops-badge mlops-badge-${g.version}`}>{g.version}</span>
                </td>
                <td className="mlops-td mlops-td-num">{g.n}</td>
                <td className="mlops-td mlops-td-num">{g.mae != null ? fmt(g.mae, 4) : "Sin feedback"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function ModelMetricsSection({ metricsData, metricsStatus }) {
  if (metricsStatus === "loading") {
    return (
      <div className="mlops-card">
        <h3 className="mlops-card-title">Métricas del Modelo</h3>
        <p className="mlops-status">Cargando métricas…</p>
      </div>
    );
  }

  if (metricsStatus === "error" || !metricsData) {
    return (
      <div className="mlops-card">
        <h3 className="mlops-card-title">Métricas del Modelo</h3>
        <p className="mlops-status mlops-status-error">Métricas no disponibles. Ejecuta el reentrenamiento primero.</p>
      </div>
    );
  }

  const val = metricsData.validation ?? {};
  const r2Mean = val.r2_mean;
  const r2Std = val.r2_std;
  const gap = metricsData.overfitting_gap;
  const bestParams = metricsData.best_params ?? {};

  return (
    <div className="mlops-card">
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Métricas del Modelo</h3>
      </div>
      <div className="mlops-metrics-grid">
        <div className="mlops-metric-item">
          <span className="mlops-metric-label">R² medio (CV)</span>
          <span className="mlops-metric-value mlops-metric-default">
            {r2Mean != null ? fmt(r2Mean, 4) : "—"}
            {r2Std != null ? <small> ± {fmt(r2Std, 4)}</small> : null}
          </span>
        </div>
        <div className="mlops-metric-item">
          <span className="mlops-metric-label">Overfitting gap</span>
          <span className={`mlops-metric-value ${gap != null && gap < 0.05 ? "mlops-good" : "mlops-warn"}`}>
            {gap != null ? fmt(gap, 4) : "—"}
            {gap != null && <small> {gap < 0.05 ? "✓ OK" : "⚠ A/B candidato"}</small>}
          </span>
        </div>
        {r2Mean != null && (
          <div className="mlops-metric-item">
            <span className="mlops-metric-label">Umbral mínimo R²</span>
            <span className={`mlops-metric-value ${r2Mean >= 0.5 ? "mlops-good" : "mlops-warn"}`}>
              0.50 {r2Mean >= 0.5 ? "✓" : "✗"}
            </span>
          </div>
        )}
      </div>
      {Object.keys(bestParams).length > 0 && (
        <div className="mlops-params">
          <p className="mlops-params-title">Mejores hiperparámetros (Optuna):</p>
          <pre className="mlops-params-pre">{JSON.stringify(bestParams, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function MLOpsPanel() {
  const [predictions, setPredictions] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [metricsStatus, setMetricsStatus] = useState("loading");
  const [retrainStatus, setRetrainStatus] = useState(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  async function loadPredictions() {
    try {
      const data = await getPredictions(200, 0);
      setPredictions(data);
    } catch {
      setPredictions([]);
    }
  }

  async function loadMetrics() {
    try {
      const data = await getMetrics();
      setMetricsData(data);
      setMetricsStatus("ready");
    } catch {
      setMetricsStatus("error");
    }
  }

  const refreshRetrainStatus = useCallback(async () => {
    try {
      const data = await getRetrainStatus();
      setRetrainStatus(data);
      if (data.status === "running") {
        setBannerDismissed(false);
      }
      if (data.status === "completed") {
        await loadMetrics();
        await loadPredictions();
      }
    } catch {
      /* ignore polling errors */
    }
  }, []);

  useEffect(() => {
    loadPredictions();
    loadMetrics();
    refreshRetrainStatus();
  }, [refreshRetrainStatus]);

  useEffect(() => {
    const isRunning = retrainStatus?.status === "running";
    if (!isRunning) return undefined;

    const timer = window.setInterval(refreshRetrainStatus, 4000);
    return () => window.clearInterval(timer);
  }, [retrainStatus?.status, refreshRetrainStatus]);

  const showBanner = retrainStatus && retrainStatus.status !== "idle" && !bannerDismissed;

  return (
    <div className="mlops-shell">
      {showBanner ? (
        <RetrainStatusBanner
          status={retrainStatus}
          onDismiss={() => setBannerDismissed(true)}
        />
      ) : null}

      <div className="mlops-panels-grid">
        <div className="mlops-panels-row">
          <RetrainSection
            onRetrainStarted={refreshRetrainStatus}
            onRetrained={loadPredictions}
            retrainRunning={retrainStatus?.status === "running"}
          />
          <ModelVersionSection predictions={predictions} metricsData={metricsData} />
        </div>
        <div className="mlops-panels-row">
          <ModelMetricsSection metricsData={metricsData} metricsStatus={metricsStatus} />
          <ABMetricsSection predictions={predictions} />
        </div>
      </div>
    </div>
  );
}

export default MLOpsPanel;
