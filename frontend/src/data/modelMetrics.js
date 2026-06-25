export const initialForm = {
  startup_name: "Nova Signal",
  country: "United States",
  continent: "North America",
  industry: "Fintech",
  year_founded: 2015,
  funding_usd: 50000000,
  company_age: 11,
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
  "North America",
  "Asia",
  "Europe",
  "South America",
  "Oceania",
  "Africa",
];

export const metricCards = [
  {
    label: "Startups analizadas",
    value: "1.186",
    detail: "Dataset Kaggle hasta septiembre de 2022",
  },
  {
    label: "Concentracion USA",
    value: "53.6%",
    detail: "Dominancia geográfica en la muestra",
  },
  {
    label: "Features operativas",
    value: "6",
    detail: "Fundacion, funding, edad, industria, pais y continente",
  },
  {
    label: "R2 validacion",
    value: "0.2207",
    detail: "Gradient Boosting ganador sin sobreajuste",
  },
];

export const marketSignals = [
  { label: "Sector dominante", value: "Fintech", tone: "signal" },
  { label: "MAE validacion", value: "$1.68B", tone: "neutral" },
  { label: "CV R2 medio", value: "0.2757", tone: "signal" },
  { label: "Riesgo estructural", value: "Outliers", tone: "risk" },
];

export const pipelineSteps = [
  "Datos crudos",
  "Feature Engineering",
  "Preprocesamiento",
  "Ridge / Random Forest / Gradient Boosting",
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
    title: "Evaluacion objetiva",
    copy: "Analiza senales historicas y reduce el peso de la intuicion aislada.",
  },
  {
    title: "Deal flow escalable",
    copy: "Prioriza grandes volumenes de startups antes de una due diligence profunda.",
  },
  {
    title: "Baseline predictivo",
    copy: "Genera una estimacion inicial basada en patrones del mercado unicornio.",
  },
];

export const dataSources = [
  {
    label: "Dataset",
    value: "Kaggle: ramjasmaurya/unicorn-startups",
    note: "La muestra contiene 1.186 startups hasta septiembre de 2022.",
  },
  {
    label: "Metricas visibles",
    value: "Backend models/metrics.json",
    note: "El entrenamiento genera RMSE, MAE, R2, validacion cruzada y control de overfitting.",
  },
  {
    label: "Prediccion",
    value: "Backend FastAPI /predict",
    note: "Requiere models/best_model.joblib y usa las features actuales del pipeline.",
  },
  {
    label: "Feedback",
    value: "Backend FastAPI /feedback",
    note: "Cuando la API esta activa, se guarda en SQLite dentro de data/feedback.",
  },
];
