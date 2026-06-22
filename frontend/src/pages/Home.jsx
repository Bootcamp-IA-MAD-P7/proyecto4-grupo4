import { useEffect, useState } from "react";

import { createPrediction, getHealth, saveFeedback } from "../api";
import Dashboard from "../components/Dashboard";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import OraclePrism from "../components/OraclePrism";
import PipelineSteps from "../components/PipelineSteps";
import PredictionForm from "../components/PredictionForm";
import PredictionResult from "../components/PredictionResult";
import { countries, industries, initialForm } from "../data/modelMetrics";

function Home() {
  const [form, setForm] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [feedback, setFeedback] = useState({
    feedback_score: "",
    actual_valuation_b: "",
    comments: "",
  });
  const [apiStatus, setApiStatus] = useState("API offline");
  const [error, setError] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getHealth()
      .then((body) => setApiStatus(`API ${body.status} · ${body.model_mode}`))
      .catch(() => setApiStatus("API offline"));
  }, []);

  function updateField(event) {
    const { name, value } = event.target;
    const numericFields = ["join_year", "join_month", "investor_count"];
    setForm((current) => ({
      ...current,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }));
  }

  function updateFeedback(event) {
    const { name, value } = event.target;
    setFeedback((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handlePredict(event) {
    event.preventDefault();
    setError("");
    setFeedbackMessage("");
    setLoading(true);

    const { startup_name: _startupName, ...payload } = form;

    try {
      const body = await createPrediction(payload);
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
    <main className="app-shell" id="top">
      <Navbar apiStatus={apiStatus} />

      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Motor predictivo de venture intelligence</p>
          <h1>El Oráculo de Venture Capital</h1>
          <p>
            Predicción basada en datos para detectar señales tempranas de
            valoración en startups unicornio.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="#predict">
              Consultar el Oráculo
            </a>
            <a className="ghost-action" href="#methodology">
              Ver metodología
            </a>
          </div>
          <div className="hero-prism-wrap">
            <OraclePrism />
          </div>
        </div>

        <PredictionForm
          countries={countries}
          form={form}
          industries={industries}
          loading={loading}
          onChange={updateField}
          onSubmit={handlePredict}
        />
      </section>

      <section className="result-dock">
        <PredictionResult
          error={error}
          feedback={feedback}
          feedbackMessage={feedbackMessage}
          loading={loading}
          onFeedbackChange={updateFeedback}
          onFeedbackSubmit={handleFeedback}
          prediction={prediction}
        />
      </section>

      <Dashboard />
      <PipelineSteps />
      <Footer />
    </main>
  );
}

export default Home;
