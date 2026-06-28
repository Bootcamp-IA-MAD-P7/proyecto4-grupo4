import React from "react";
import { Database, ShieldCheck } from "lucide-react";

import SignalBadge from "./SignalBadge";
import { formatIntegerInput } from "../utils/numberFormat";

function formatUsd(value) {
  return typeof value === "number"
    ? new Intl.NumberFormat("es-ES", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }).format(value)
    : "Pendiente";
}

function formatBillions(value) {
  return typeof value === "number" ? `$${value.toFixed(2)}B` : "$--";
}

function getSignal(prediction) {
  if (!prediction) return { signal: "Pendiente", risk: "Sin lectura", tone: "neutral" };

  const value = prediction.valuation_b;
  if (value >= 5) return { signal: "Señal alta", risk: "Riesgo alto", tone: "risk" };
  if (value >= 2.5) return { signal: "Señal positiva", risk: "Moderado", tone: "signal" };
  return { signal: "Señal inicial", risk: "Controlado", tone: "neutral" };
}

function PredictionResult({
  error,
  feedback,
  feedbackMessage,
  loading,
  onFeedbackChange,
  onFeedbackSubmit,
  prediction,
}) {
  const reading = getSignal(prediction);
  const canSendFeedback = Boolean(prediction);

  return (
    <aside className="result-stack">
      <section className="panel result-panel">
        <div className="result-header">
          <div>
            <p>Valoración predictiva estimada</p>
            <h2>{formatBillions(prediction?.valuation_b)}</h2>
          </div>
          <SignalBadge tone={reading.tone}>{reading.signal}</SignalBadge>
        </div>

        <div className="risk-row">
          <span>
            <ShieldCheck size={18} aria-hidden="true" />
            Riesgo algorítmico
          </span>
          <strong>{reading.risk}</strong>
        </div>

        <p className="result-copy">
          Esta estimación representa una referencia analítica basada en datos históricos.
          Debe utilizarse como apoyo a la decisión, no como valoración definitiva.
        </p>

        <dl className="model-meta">
          <div>
            <dt>Valor completo</dt>
            <dd>{formatUsd(prediction?.valuation_usd)}</dd>
          </div>
          <div>
            <dt>Modelo</dt>
            <dd>{prediction?.model_version ?? "Pendiente"}</dd>
          </div>
        </dl>
      </section>

      <form className="panel feedback-panel" onSubmit={onFeedbackSubmit}>
        <div className="section-heading compact">
          <p>Retroalimentación</p>
          <h2>Registro para mejora continua</h2>
        </div>

        <div className="feedback-fields">
          <label>
            Valor real observado (USD)
            <input
              className="numeric-input"
              disabled={!canSendFeedback}
              inputMode="numeric"
              name="actual_valuation_usd"
              onChange={onFeedbackChange}
              pattern="[0-9.]*"
              type="text"
              value={formatIntegerInput(feedback.actual_valuation_usd)}
            />
          </label>

          <label>
            Comentario
            <textarea
              disabled={!canSendFeedback}
              maxLength="1000"
              name="comment"
              onChange={onFeedbackChange}
              rows="3"
              value={feedback.comment}
            />
          </label>
        </div>

        <button className="secondary-action" disabled={!canSendFeedback || loading} type="submit">
          <Database size={18} aria-hidden="true" />
          Guardar retroalimentación
        </button>

        {error ? <p className="form-message error">{error}</p> : null}
        {feedbackMessage ? <p className="form-message success">{feedbackMessage}</p> : null}
      </form>
    </aside>
  );
}

export default PredictionResult;
