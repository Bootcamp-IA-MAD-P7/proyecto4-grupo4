import { Database, ShieldCheck } from "lucide-react";

import SignalBadge from "./SignalBadge";

function getSignal(prediction) {
  if (!prediction) return { signal: "Pendiente", risk: "Sin lectura", tone: "neutral" };
  const value = prediction.prediction_billion_usd;
  if (value >= 5) return { signal: "Alta señal", risk: "Riesgo alto", tone: "risk" };
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
  const canSendFeedback = Boolean(prediction?.request_id);

  return (
    <aside className="result-stack">
      <section className="panel result-panel">
        <div className="result-header">
          <div>
            <p>Valoracion predictiva estimada</p>
            <h2>{prediction ? `$${prediction.prediction_billion_usd.toFixed(2)}B` : "$--"}</h2>
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
          Esta estimación representa un baseline analítico basado en datos históricos.
          Debe utilizarse como apoyo a la decisión, no como valoración definitiva.
        </p>

        <dl className="model-meta">
          <div>
            <dt>Modelo</dt>
            <dd>{prediction?.model_used ?? "mock_model"}</dd>
          </div>
          <div>
            <dt>Unidad</dt>
            <dd>USD Billions</dd>
          </div>
        </dl>
      </section>

      <form className="panel feedback-panel" onSubmit={onFeedbackSubmit}>
        <div className="section-heading compact">
          <p>Feedback</p>
          <h2>Registro para mejora continua</h2>
        </div>

        <div className="feedback-grid">
          <label>
            Score
            <input
              disabled={!canSendFeedback}
              max="5"
              min="1"
              name="feedback_score"
              onChange={onFeedbackChange}
              type="number"
              value={feedback.feedback_score}
            />
          </label>

          <label>
            Valor real
            <input
              disabled={!canSendFeedback}
              min="0"
              name="actual_valuation_b"
              onChange={onFeedbackChange}
              step="0.01"
              type="number"
              value={feedback.actual_valuation_b}
            />
          </label>
        </div>

        <label>
          Comentarios
          <textarea
            disabled={!canSendFeedback}
            maxLength="500"
            name="comments"
            onChange={onFeedbackChange}
            rows="3"
            value={feedback.comments}
          />
        </label>

        <button className="secondary-action" disabled={!canSendFeedback || loading} type="submit">
          <Database size={18} aria-hidden="true" />
          Guardar feedback
        </button>

        {error ? <p className="form-message error">{error}</p> : null}
        {feedbackMessage ? <p className="form-message success">{feedbackMessage}</p> : null}
      </form>
    </aside>
  );
}

export default PredictionResult;
