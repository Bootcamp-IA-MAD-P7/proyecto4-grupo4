import { BASE_URL } from "../api";

const currentYear = new Date().getFullYear();

export const initialForm = {
  year_founded: 2015,
  funding_usd: 50_000_000,
  company_age: currentYear - 2015,
  industry: "Fintech",
  country: "United States",
  continent: "North America",
};

export const countries = [
  { value: "Germany", label: "Alemania", continent: "Europe" },
  { value: "Argentina", label: "Argentina", continent: "South America" },
  { value: "Australia", label: "Australia", continent: "Oceania" },
  { value: "Austria", label: "Austria", continent: "Europe" },
  { value: "Bahamas", label: "Bahamas", continent: "North America" },
  { value: "Belgium", label: "Bélgica", continent: "Europe" },
  { value: "Bermuda", label: "Bermudas", continent: "North America" },
  { value: "Brazil", label: "Brasil", continent: "South America" },
  { value: "Canada", label: "Canadá", continent: "North America" },
  { value: "Chile", label: "Chile", continent: "South America" },
  { value: "China", label: "China", continent: "Asia" },
  { value: "Colombia", label: "Colombia", continent: "South America" },
  { value: "South Korea", label: "Corea del Sur", continent: "Asia" },
  { value: "Croatia", label: "Croacia", continent: "Europe" },
  { value: "Denmark", label: "Dinamarca", continent: "Europe" },
  { value: "United Arab Emirates", label: "Emiratos Árabes Unidos", continent: "Asia" },
  { value: "Spain", label: "España", continent: "Europe" },
  { value: "United States", label: "Estados Unidos", continent: "North America" },
  { value: "Estonia", label: "Estonia", continent: "Europe" },
  { value: "Philippines", label: "Filipinas", continent: "Asia" },
  { value: "Finland", label: "Finlandia", continent: "Europe" },
  { value: "France", label: "Francia", continent: "Europe" },
  { value: "Hong Kong", label: "Hong Kong", continent: "Asia" },
  { value: "India", label: "India", continent: "Asia" },
  { value: "Indonesia", label: "Indonesia", continent: "Asia" },
  { value: "Ireland", label: "Irlanda", continent: "Europe" },
  { value: "Israel", label: "Israel", continent: "Asia" },
  { value: "Italy", label: "Italia", continent: "Europe" },
  { value: "Japan", label: "Japón", continent: "Asia" },
  { value: "Lithuania", label: "Lituania", continent: "Europe" },
  { value: "Luxembourg", label: "Luxemburgo", continent: "Europe" },
  { value: "Malaysia", label: "Malasia", continent: "Asia" },
  { value: "Mexico", label: "México", continent: "North America" },
  { value: "Nigeria", label: "Nigeria", continent: "Africa" },
  { value: "Norway", label: "Noruega", continent: "Europe" },
  { value: "Netherlands", label: "Países Bajos", continent: "Europe" },
  { value: "United Kingdom", label: "Reino Unido", continent: "Europe" },
  { value: "Czech Republic", label: "República Checa", continent: "Europe" },
  { value: "Senegal", label: "Senegal", continent: "Africa" },
  { value: "Singapore", label: "Singapur", continent: "Asia" },
  { value: "South Africa", label: "Sudáfrica", continent: "Africa" },
  { value: "Sweden", label: "Suecia", continent: "Europe" },
  { value: "Switzerland", label: "Suiza", continent: "Europe" },
  { value: "Thailand", label: "Tailandia", continent: "Asia" },
  { value: "Turkey", label: "Turquía", continent: "Europe" },
  { value: "Vietnam", label: "Vietnam", continent: "Asia" },
];

export const industries = [
  { value: "Fintech", label: "Fintech" },
  { value: "Internet software & services", label: "Software y servicios de internet" },
  { value: "E-commerce & direct-to-consumer", label: "Comercio electrónico y venta directa" },
  { value: "Health", label: "Salud" },
  { value: "Artificial intelligence", label: "Inteligencia artificial" },
  { value: "Supply chain, logistics, & delivery", label: "Cadena de suministro, logística y entregas" },
  { value: "Cybersecurity", label: "Ciberseguridad" },
  { value: "Data management & analytics", label: "Gestión y análisis de datos" },
  { value: "Auto & transportation", label: "Automoción y transporte" },
  { value: "Other", label: "Otro" },
];

export const continents = [
  { value: "North America", label: "América del Norte" },
  { value: "Asia", label: "Asia" },
  { value: "Europe", label: "Europa" },
  { value: "South America", label: "América del Sur" },
  { value: "Africa", label: "África" },
  { value: "Oceania", label: "Oceanía" },
];

export function getContinentForCountry(countryValue) {
  return countries.find((country) => country.value === countryValue)?.continent ?? initialForm.continent;
}

export function getContinentLabel(continentValue) {
  return continents.find((continent) => continent.value === continentValue)?.label ?? continentValue;
}

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

/** Unifica métricas legacy (Fase 3) y Fase 7 (target múltiplo + Optuna). */
function normalizeMetrics(metrics) {
  if (!metrics) return null;

  const validation = metrics.validation ?? {};
  const crossValidation = metrics.cross_validation ?? {};
  const overfitting = metrics.overfitting ?? {};

  const r2 =
    validation.r2 ??
    validation.r2_mean ??
    validation.r2_val_split ??
    null;

  const cvR2Mean =
    crossValidation.cv_r2_mean ??
    validation.r2_mean ??
    null;

  let withinLimit = overfitting.within_limit;
  if (withinLimit == null && typeof metrics.overfitting_gap === "number") {
    withinLimit = metrics.overfitting_gap < 0.05;
  }

  const modelType =
    metrics.model_type ??
    (metrics.target === "multiple" ? "gradient boosting" : null);

  return {
    n_samples: metrics.n_samples ?? null,
    model_type: modelType,
    optuna_trials: metrics.optuna_trials ?? null,
    cv_folds: metrics.cv_folds ?? null,
    validation: {
      r2,
      mae: validation.mae ?? null,
      rmse: validation.rmse ?? null,
    },
    cross_validation: { cv_r2_mean: cvR2Mean },
    overfitting: { within_limit: withinLimit },
  };
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
  const m = normalizeMetrics(metrics);
  if (!m) {
    return [
      { label: "Muestras", value: "No disponible", detail: "Registros usados durante el entrenamiento" },
      { label: "R² de validación", value: "No disponible", detail: "Capacidad explicativa sobre datos no vistos" },
      { label: "MAE de validación", value: "No disponible", detail: "Error medio absoluto del modelo" },
      { label: "R² medio en validación cruzada", value: "No disponible", detail: "Promedio de validación cruzada" },
    ];
  }

  const samplesValue =
    m.n_samples != null
      ? formatInteger(m.n_samples)
      : m.optuna_trials != null
        ? `${m.optuna_trials} trials`
        : "No disponible";

  const samplesDetail =
    m.n_samples != null
      ? "Registros usados durante el entrenamiento"
      : m.optuna_trials != null
        ? `Optuna K-Fold (${m.cv_folds ?? 5} folds)`
        : "Registros usados durante el entrenamiento";

  return [
    {
      label: "Muestras",
      value: samplesValue,
      detail: samplesDetail,
    },
    {
      label: "R² de validación",
      value: formatNumber(m.validation.r2),
      detail: "Capacidad explicativa sobre datos no vistos",
    },
    {
      label: "MAE de validación",
      value: m.validation.mae != null ? formatUsdBillions(m.validation.mae) : "N/D",
      detail: m.validation.mae != null ? "Error medio absoluto del modelo" : "No aplica al target múltiplo (Fase 7)",
    },
    {
      label: "R² medio en validación cruzada",
      value: formatNumber(m.cross_validation.cv_r2_mean),
      detail: "Promedio de validación cruzada",
    },
  ];
}

export function buildMarketSignals(metrics) {
  const m = normalizeMetrics(metrics);
  if (!m) {
    return [
      { label: "Modelo", value: "No disponible", tone: "neutral" },
      { label: "R² de validación", value: "No disponible", tone: "neutral" },
      { label: "Sobreajuste", value: "No disponible", tone: "neutral" },
      { label: "RMSE de validación", value: "No disponible", tone: "info" },
    ];
  }

  return [
    { label: "Modelo", value: formatModelName(m.model_type), tone: "signal" },
    { label: "R² de validación", value: formatNumber(m.validation.r2), tone: getR2Tone(m.validation.r2) },
    {
      label: "Sobreajuste",
      value: formatOverfitting(m.overfitting.within_limit),
      tone: getOverfittingTone(m.overfitting.within_limit),
    },
    {
      label: "RMSE de validación",
      value: m.validation.rmse != null ? formatUsdBillions(m.validation.rmse) : "N/D",
      tone: "info",
    },
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
  { label: "Comercio electrónico", value: 13 },
];

export const valueProps = [
  {
    title: "Evaluación objetiva",
    copy: "Analiza señales históricas y reduce el peso de la intuición aislada.",
  },
  {
    title: "Flujo de oportunidades escalable",
    copy: "Prioriza grandes volúmenes de startups antes de una evaluación profunda.",
  },
  {
    title: "Referencia predictiva",
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
