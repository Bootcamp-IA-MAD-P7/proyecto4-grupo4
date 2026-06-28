export const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const PREDICT_FIELDS = [
  "year_founded",
  "funding_usd",
  "company_age",
  "industry",
  "country",
  "continent",
];

function pickFields(payload, fields) {
  return fields.reduce((body, field) => {
    body[field] = payload[field];
    return body;
  }, {});
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ?? "La petición falló");
  }
  return body;
}

export function predict(payload) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(pickFields(payload, PREDICT_FIELDS)),
  });
}

export function submitFeedback(payload) {
  return request("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getHealth() {
  return request("/health");
}

export const createPrediction = predict;
export const saveFeedback = submitFeedback;

export function getPredictions(limit = 50, offset = 0) {
  return request(`/predictions?limit=${limit}&offset=${offset}`);
}

export function updatePrediction(id, payload) {
  return request(`/predictions/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function postRetrain() {
  return request("/retrain", { method: "POST" });
}

export function getMetrics() {
  return request("/metrics");
}
