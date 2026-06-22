import { useEffect, useMemo, useState } from "react";
import { Database, RefreshCw, Send, Sparkles } from "lucide-react";

import { createPrediction, getHealth, saveFeedback } from "./api";

const initialForm = {
  country: "United States",
  city: "San Francisco",
  industry: "Fintech",
  join_year: 2021,
  join_month: 7,
  investor_count: 3,
};

const countries = [
  "United States",
  "China",
  "India",
  "United Kingdom",
  "Germany",
  "France",
  "Israel",
  "Canada",
  "Brazil",
  "Singapore",
];

const industries = [
  "Fintech",
  "Internet software & services",
  "E-commerce & direct-to-consumer",
  "Health",
  "Artificial intelligence",
  "Supply chain, logistics, & delivery",
  "Cybersecurity",
  "Data management & analytics",
  "Auto & transportation",
  "Other",
];

function App() {
  const [form, setForm] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [feedback, setFeedback] = useState({
    feedback_score: "",
    actual_valuation_b: "",
    comments: "",
  });
  const [status, setStatus] = useState("Checking API");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState("");

  useEffect(() => {
    getHealth()
      .then((body) => setStatus(`API ${body.status} · ${body.model_mode}`))
      .catch(() => setStatus("API offline"));
  }, []);

  const canSendFeedback = useMemo(() => Boolean(prediction?.request_id), [prediction]);

  function updateField(event) {
    const { name, value } = event.target;
    const numericFields = ["join_year", "join_month", "investor_count"];
    setForm((current) => ({
      ...current,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }));
  }

  async function handlePredict(event) {
    event.preventDefault();
    setError("");
    setFeedbackMessage("");
    setLoading(true);

    try {
      const body = await createPrediction(form);
      setPrediction(body);
    } catch (requestError) {
      setPrediction(null);
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(event) {
    event.preventDefault();
    if (!prediction?.request_id) return;

    setError("");
    setFeedbackMessage("");
    setLoading(true);

    const payload = {
      request_id: prediction.request_id,
      feedback_score: feedback.feedback_score ? Number(feedback.feedback_score) : null,
      actual_valuation_b: feedback.actual_valuation_b
        ? Number(feedback.actual_valuation_b)
        : null,
      comments: feedback.comments || null,
    };

    try {
      const body = await saveFeedback(payload);
      setFeedbackMessage(body.message);
      setFeedback({ feedback_score: "", actual_valuation_b: "", comments: "" });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Grupo 4 · Regresion supervisada</p>
          <h1>Unicorn Valuation Estimator</h1>
        </div>
        <span className="api-status">
          <Database size={16} aria-hidden="true" />
          {status}
        </span>
      </section>

      <section className="workspace-grid">
        <form className="tool-panel" onSubmit={handlePredict}>
          <div className="panel-heading">
            <Sparkles size={18} aria-hidden="true" />
            <h2>Startup Inputs</h2>
          </div>

          <div className="row g-3">
            <div className="col-md-6">
              <label className="form-label" htmlFor="country">
                Country
              </label>
              <select
                className="form-select"
                id="country"
                name="country"
                value={form.country}
                onChange={updateField}
                required
              >
                {countries.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-md-6">
              <label className="form-label" htmlFor="city">
                City
              </label>
              <input
                className="form-control"
                id="city"
                name="city"
                value={form.city}
                onChange={updateField}
                required
              />
            </div>

            <div className="col-12">
              <label className="form-label" htmlFor="industry">
                Industry
              </label>
              <select
                className="form-select"
                id="industry"
                name="industry"
                value={form.industry}
                onChange={updateField}
                required
              >
                {industries.map((industry) => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="join_year">
                Join year
              </label>
              <input
                className="form-control"
                id="join_year"
                max="2026"
                min="2007"
                name="join_year"
                onChange={updateField}
                type="number"
                value={form.join_year}
                required
              />
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="join_month">
                Join month
              </label>
              <input
                className="form-control"
                id="join_month"
                max="12"
                min="1"
                name="join_month"
                onChange={updateField}
                type="number"
                value={form.join_month}
                required
              />
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="investor_count">
                Investors
              </label>
              <input
                className="form-control"
                id="investor_count"
                max="20"
                min="0"
                name="investor_count"
                onChange={updateField}
                type="number"
                value={form.investor_count}
                required
              />
            </div>
          </div>

          <button className="btn btn-primary action-button" disabled={loading} type="submit">
            {loading ? <RefreshCw size={18} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
            Predict
          </button>
        </form>

        <section className="result-column">
          <div className="tool-panel result-panel">
            <h2>Prediction</h2>
            {prediction ? (
              <>
                <p className="prediction-value">
                  ${prediction.prediction_billion_usd.toFixed(2)}B
                </p>
                <p className="prediction-meta">{prediction.model_used}</p>
              </>
            ) : (
              <p className="muted">No prediction yet</p>
            )}
          </div>

          <form className="tool-panel" onSubmit={handleFeedback}>
            <h2>Feedback</h2>
            <div className="row g-3">
              <div className="col-sm-6">
                <label className="form-label" htmlFor="feedback_score">
                  Score
                </label>
                <input
                  className="form-control"
                  disabled={!canSendFeedback}
                  id="feedback_score"
                  max="5"
                  min="1"
                  name="feedback_score"
                  onChange={(event) =>
                    setFeedback((current) => ({
                      ...current,
                      feedback_score: event.target.value,
                    }))
                  }
                  type="number"
                  value={feedback.feedback_score}
                />
              </div>

              <div className="col-sm-6">
                <label className="form-label" htmlFor="actual_valuation_b">
                  Actual valuation
                </label>
                <input
                  className="form-control"
                  disabled={!canSendFeedback}
                  id="actual_valuation_b"
                  min="0"
                  name="actual_valuation_b"
                  onChange={(event) =>
                    setFeedback((current) => ({
                      ...current,
                      actual_valuation_b: event.target.value,
                    }))
                  }
                  step="0.01"
                  type="number"
                  value={feedback.actual_valuation_b}
                />
              </div>

              <div className="col-12">
                <label className="form-label" htmlFor="comments">
                  Comments
                </label>
                <textarea
                  className="form-control"
                  disabled={!canSendFeedback}
                  id="comments"
                  maxLength="500"
                  name="comments"
                  onChange={(event) =>
                    setFeedback((current) => ({
                      ...current,
                      comments: event.target.value,
                    }))
                  }
                  rows="3"
                  value={feedback.comments}
                />
              </div>
            </div>

            <button className="btn btn-outline-primary action-button" disabled={!canSendFeedback || loading} type="submit">
              <Database size={18} aria-hidden="true" />
              Save
            </button>
          </form>
        </section>
      </section>

      {error ? <div className="alert alert-danger app-alert">{error}</div> : null}
      {feedbackMessage ? <div className="alert alert-success app-alert">{feedbackMessage}</div> : null}
    </main>
  );
}

export default App;
