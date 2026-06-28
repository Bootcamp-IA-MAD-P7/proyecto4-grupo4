import React, { useEffect, useState } from "react";

import { getMetrics, getPredictions, postRetrain } from "../api";

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

function RetrainSection({ onRetrained }) {
  const [status, setStatus] = useState("idle");
  const [toast, setToast] = useState(null);

  async function handleRetrain() {
    setStatus("loading");
    setToast(null);
    try {
      const res = await postRetrain();
      setStatus("idle");
      setToast({ message: `✓ ${res.message ?? "Reentrenamiento iniciado en segundo plano."}`, type: "success" });
      if (onRetrained) onRetrained();
      setTimeout(() => setToast(null), 6000);
    } catch (err) {
      setStatus("idle");
      setToast({ message: `✗ ${err.message}`, type: "error" });
      setTimeout(() => setToast(null), 6000);
    }
  }

  return (
    <div className="mlops-card">
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Control de Reentrenamiento</h3>
      </div>
      <p className="mlops-hint" style={{ marginBottom: "1rem" }}>
        Lanza un reentrenamiento completo con K-Fold + Optuna en segundo plano sin interrumpir el servicio.
      </p>
      <button
        className="mlops-btn mlops-btn-primary"
        disabled={status === "loading"}
        onClick={handleRetrain}
      >
        {status === "loading" ? "Iniciando reentrenamiento…" : "⟳ Reentrenar Modelo (Optuna + K-Fold)"}
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
          <span className="mlops-metric-value">
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

  async function loadPredictions() {
    try {
      const data = await getPredictions(200, 0);
      setPredictions(data);
    } catch {
      setPredictions([]);
    }
  }

  useEffect(() => {
    loadPredictions();

    getMetrics()
      .then((data) => {
        setMetricsData(data);
        setMetricsStatus("ready");
      })
      .catch(() => {
        setMetricsStatus("error");
      });
  }, []);

  return (
    <div className="mlops-panels-grid">
      <RetrainSection onRetrained={loadPredictions} />
      <ModelVersionSection predictions={predictions} metricsData={metricsData} />
      <ABMetricsSection predictions={predictions} />
      <ModelMetricsSection metricsData={metricsData} metricsStatus={metricsStatus} />
    </div>
  );
}

export default MLOpsPanel;
