export const initialForm = {
  startup_name: "Nova Signal",
  country: "United States",
  city: "San Francisco",
  industry: "Fintech",
  join_year: 2021,
  join_month: 7,
  investor_count: 3,
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
    label: "MAE modelo lineal",
    value: "$1.52B",
    detail: "Error medio absoluto de referencia",
  },
  {
    label: "R2 test",
    value: "0.0286",
    detail: "Señal positiva, con limitaciones",
  },
];

export const marketSignals = [
  { label: "Sector dominante", value: "Fintech", tone: "signal" },
  { label: "RMSE lineal", value: "$2.92B", tone: "neutral" },
  { label: "Mejora vs baseline", value: "4.4%", tone: "signal" },
  { label: "Riesgo estructural", value: "Outliers", tone: "risk" },
];

export const pipelineSteps = [
  "Datos crudos",
  "Feature Engineering",
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
