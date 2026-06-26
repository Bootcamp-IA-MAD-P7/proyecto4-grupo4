import React from "react";
import { RefreshCw, Send } from "lucide-react";

import { formatIntegerInput } from "../utils/numberFormat";

function PredictionForm({
  continentLabel,
  countries,
  form,
  industries,
  loading,
  maxFoundedYear,
  onChange,
  onSubmit,
}) {
  return (
    <form className="panel prediction-form" id="predict" onSubmit={onSubmit}>
      <div className="section-heading">
        <p>Consulta predictiva</p>
        <h2>Lectura inicial de potencial unicornio</h2>
      </div>

      <div className="form-grid">
        <label>
          Año de fundación
          <input
            max={maxFoundedYear}
            min="1800"
            name="year_founded"
            onChange={onChange}
            type="number"
            value={form.year_founded}
            required
          />
        </label>

        <label>
          Financiación total (USD)
          <input
            className="numeric-input"
            inputMode="numeric"
            name="funding_usd"
            onChange={onChange}
            pattern="[0-9.]*"
            type="text"
            value={formatIntegerInput(form.funding_usd)}
            required
          />
        </label>

        <label>
          Edad de la compañía
          <input
            min="0"
            name="company_age"
            readOnly
            type="text"
            value={form.company_age}
            required
          />
        </label>

        <label>
          Industria
          <select name="industry" onChange={onChange} value={form.industry} required>
            {industries.map((industry) => (
              <option key={industry.value} value={industry.value}>
                {industry.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          País
          <select name="country" onChange={onChange} value={form.country} required>
            {countries.map((country) => (
              <option key={country.value} value={country.value}>
                {country.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Región geográfica
          <input name="continent" readOnly type="text" value={continentLabel} />
        </label>
      </div>

      <button className="primary-action" disabled={loading} type="submit">
        {loading ? <RefreshCw size={18} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
        Consultar el Oráculo
      </button>
    </form>
  );
}

export default PredictionForm;
