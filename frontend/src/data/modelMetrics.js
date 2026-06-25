import { BASE_URL } from "../api";

export const initialForm = {
  year_founded: 2015,
  funding_usd: 50_000_000,
  company_age: 9,
  industry: "Fintech",
  country: "United States",
  continent: "North America",
};

export const countries = [
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

export const industries = [
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

export const continents = [
  { value: "North America", label: "América del Norte" },
  { value: "Asia", label: "Asia" },
  { value: "Europe", label: "Europa" },
  { value: "South America", label: "América del Sur" },
  { value: "Africa", label: "África" },
  { value: "Oceania", label: "Oceanía" },
];

export async function fetchMetrics() {
  const res = await fetch(`${BASE_URL}/metrics`);
  if (!res.ok) throw new Error("No se pudieron obtener las métricas");
  return res.json();
}

function formatNumber(value, digits = 4) {
  return typeof value === "number" ? value.toFixed(digits) : "No disponible";
}

function formatInteger(value) {
  return typeof value === "number" ? value.toLocaleString("es-ES") : "No disponible";
}

function formatUsdBillions(value) {
  return typeof value === "number"
    ? `$${(value / 1_000_000_000).toFixed(2)}B`
    : "No disponible";
}

function formatModelName(value) {
  return typeof value === "string" ? value.replaceAll("_", " ") : "No disponible";
}

function formatOverfitting(value) {
  if (value === true) return "Controlado";
  if (value === false) return "Revisar";
  return "No disponible";
}

function getR2Tone(value) {
  if (typeof value !== "number") return "neutral";
  if (value >= 0.5) return "signal";
  if (value >= 0) return "neutral";
  return "risk";
}

function getOverfittingTone(value) {
  if (value === true) return "signal";
  if (value === false) return "risk";
  return "neutral";
}

export function buildMetricCards(metrics) {
  const validation = metrics?.validation ?? {};
  const crossValidation = metrics?.cross_validation ?? {};

  return [
    {
      label: "Muestras",
      value: formatInteger(metrics?.n_samples),
      detail: "Registros usados durante el entrenamiento",
    },
    {
      label: "R² de validación",
      value: formatNumber(validation.r2),
      detail: "Capacidad explicativa sobre datos no vistos",
    },
    {
      label: "MAE de validación",
      value: formatUsdBillions(validation.mae),
      detail: "Error medio absoluto del modelo",
    },
    {
      label: "R² medio en validación cruzada",
      value: formatNumber(crossValidation.cv_r2_mean),
      detail: "Promedio de validación cruzada",
    },
  ];
}

export function buildMarketSignals(metrics) {
  const validation = metrics?.validation ?? {};
  const overfitting = metrics?.overfitting ?? {};

  return [
    { label: "Modelo", value: formatModelName(metrics?.model_type), tone: "signal" },
    { label: "R² de validación", value: formatNumber(validation.r2), tone: getR2Tone(validation.r2) },
    {
      label: "Sobreajuste",
      value: formatOverfitting(overfitting.within_limit),
      tone: getOverfittingTone(overfitting.within_limit),
    },
    { label: "RMSE de validación", value: formatUsdBillions(validation.rmse), tone: "neutral" },
  ];
}

export const pipelineSteps = [
  "Datos crudos",
  "Ingeniería de variables",
  "Preprocesamiento",
  "LinearRegression / RidgeCV",
  "Valor predictivo",
];

export const sectorMix = [
  { label: "Fintech", value: 42 },
  { label: "SaaS", value: 28 },
  { label: "Healthtech", value: 17 },
  { label: "E-commerce", value: 13 },
];

export const valueProps = [
  {
    title: "Evaluación objetiva",
    copy: "Analiza señales históricas y reduce el peso de la intuición aislada.",
  },
  {
    title: "Deal flow escalable",
    copy: "Prioriza grandes volúmenes de startups antes de una evaluación profunda.",
  },
  {
    title: "Baseline predictivo",
    copy: "Genera una estimación inicial basada en patrones del mercado unicornio.",
  },
];

export const dataSources = [
  {
    label: "Dataset",
    value: "Kaggle: ramjasmaurya/unicorn-startups",
    note: "La muestra contiene startups unicornio hasta septiembre de 2022.",
  },
  {
    label: "Métricas visibles",
    value: "Backend FastAPI /metrics",
    note: "El frontend solicita las métricas al backend para evitar valores duplicados.",
  },
  {
    label: "Predicción",
    value: "Backend FastAPI /predict",
    note: "Usa el modelo versionado en models/best_model.joblib cuando está disponible.",
  },
  {
    label: "Retroalimentación",
    value: "Backend FastAPI /feedback",
    note: "Cuando la API está activa, se guarda en PostgreSQL vía DATABASE_URL.",
  },
];
