import React, { useEffect, useState } from "react";

import { createPrediction, getHealth, saveFeedback } from "../api";
import Dashboard from "../components/Dashboard";
import Footer from "../components/Footer";
import ModelNotes from "../components/ModelNotes";
import Navbar from "../components/Navbar";
import OraclePrism from "../components/OraclePrism";
import PipelineSteps from "../components/PipelineSteps";
import PredictionForm from "../components/PredictionForm";
import PredictionResult from "../components/PredictionResult";
import { continents, countries, industries, initialForm, valueProps } from "../data/modelMetrics";

const routeTitles = {
  "/": "Inicio",
  "/dashboard": "Dashboard",
  "/predict": "Prediccion",
  "/methodology": "Metodologia",
  "/model": "Modelo",
};

function getInitialPath() {
  const path = window.location.pathname;
  return routeTitles[path] ? path : "/";
}

function Home() {
  const [form, setForm] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [feedback, setFeedback] = useState({
    actual_valuation_usd: "",
    comment: "",
  });
  const [apiStatus, setApiStatus] = useState("API offline");
  const [error, setError] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState(getInitialPath);

  useEffect(() => {
    getHealth()
      .then((body) => setApiStatus(`API ${body.status} | ${body.model_mode}`))
      .catch(() => setApiStatus("API offline"));
  }, []);

  useEffect(() => {
    function handlePopState() {
      setCurrentPath(getInitialPath());
      window.scrollTo({ top: 0, behavior: "instant" });
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(event, path) {
    event.preventDefault();
    if (path !== currentPath) {
      window.history.pushState({}, "", path);
      setCurrentPath(path);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function updateField(event) {
    const { name, value } = event.target;
    const numericFields = ["year_founded", "funding_usd", "company_age"];
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
    if (!prediction?.valuation_usd) return;

    setError("");
    setFeedbackMessage("");
    setLoading(true);

    const payload = {
      ...form,
      predicted_valuation_usd: prediction.valuation_usd,
      actual_valuation_usd: feedback.actual_valuation_usd
        ? Number(feedback.actual_valuation_usd)
        : null,
      comment: feedback.comment || null,
    };
    delete payload.startup_name;

    try {
      const body = await saveFeedback(payload);
      setFeedbackMessage(body.message);
      setFeedback({ actual_valuation_usd: "", comment: "" });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell" id="top">
      <Navbar apiStatus={apiStatus} currentPath={currentPath} onNavigate={navigate} />

      {currentPath === "/" ? (
        <section className="hero-grid hero-home">
          <div className="hero-copy">
            <div className="hero-title-lockup">
              <OraclePrism className="hero-prism-bg" />
              <p className="eyebrow">Motor predictivo de venture intelligence</p>
              <h1>El Oraculo de Venture Capital</h1>
            </div>

            <p>
              Prediccion basada en datos para detectar senales tempranas de
              valoracion en startups unicornio.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="/predict" onClick={(event) => navigate(event, "/predict")}>
                Consultar el Oraculo
              </a>
              <a className="ghost-action" href="/methodology" onClick={(event) => navigate(event, "/methodology")}>
                Ver metodologia
              </a>
            </div>
          </div>

          <section className="value-grid" aria-label="Bloques de valor">
            {valueProps.map((item) => (
              <article className="panel value-card" key={item.title}>
                <h2>{item.title}</h2>
                <p>{item.copy}</p>
              </article>
            ))}
          </section>
        </section>
      ) : null}

      {currentPath === "/dashboard" ? <Dashboard /> : null}

      {currentPath === "/predict" ? (
        <section className="route-page predict-page">
          <div className="route-heading">
            <p className="eyebrow">Consulta predictiva</p>
            <h1>Convierte datos de deal flow en una lectura inicial de valoracion.</h1>
          </div>

          <div className="predict-grid">
            <PredictionForm
              continents={continents}
              countries={countries}
              form={form}
              industries={industries}
              loading={loading}
              onChange={updateField}
              onSubmit={handlePredict}
            />

            <PredictionResult
              error={error}
              feedback={feedback}
              feedbackMessage={feedbackMessage}
              loading={loading}
              onFeedbackChange={updateFeedback}
              onFeedbackSubmit={handleFeedback}
              prediction={prediction}
            />
          </div>
        </section>
      ) : null}

      {currentPath === "/methodology" ? <PipelineSteps /> : null}
      {currentPath === "/model" ? <ModelNotes /> : null}

      <Footer onNavigate={navigate} />
    </main>
  );
}

export default Home;
