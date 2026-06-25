import React, { useEffect, useState } from "react";

import { getHealth, predict, submitFeedback } from "../api";
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
  "/dashboard": "Panel",
  "/predict": "Predicción",
  "/methodology": "Metodología",
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
  const [apiStatus, setApiStatus] = useState("API sin conexión");
  const [error, setError] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState(getInitialPath);

  useEffect(() => {
    getHealth()
      .then((body) => {
        const modelState = body.model_loaded ? "modelo cargado" : "modelo no cargado";
        setApiStatus(`API ${body.status} | ${modelState}`);
      })
      .catch(() => setApiStatus("API sin conexión"));
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
      [name]: numericFields.includes(name) && value !== "" ? Number(value) : value,
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

    try {
      const body = await predict(form);
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
    if (!prediction) return;

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

    try {
      const body = await submitFeedback(payload);
      setFeedbackMessage(`Retroalimentación registrada con ID ${body.id}.`);
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
              <p className="eyebrow">Motor predictivo de inteligencia de inversión</p>
              <h1>El Oráculo de Capital Riesgo</h1>
            </div>

            <p>
              Predicción basada en datos para detectar señales tempranas de
              valoración en startups unicornio.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="/predict" onClick={(event) => navigate(event, "/predict")}>
                Consultar el Oráculo
              </a>
              <a className="ghost-action" href="/methodology" onClick={(event) => navigate(event, "/methodology")}>
                Ver metodología
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
            <h1>Convierte datos de oportunidades de inversión en una lectura inicial de valoración.</h1>
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
