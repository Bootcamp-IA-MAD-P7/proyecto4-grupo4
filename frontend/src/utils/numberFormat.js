export function formatIntegerInput(value) {
  if (value === "" || value === null || value === undefined) return "";
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 0,
  }).format(value);
}

export function parseIntegerInput(value) {
  const digits = String(value).replace(/\D/g, "");
  return digits ? Number(digits) : "";
}

export function isGreaterThanOne(value) {
  return typeof value === "number" && value > 1;
}
