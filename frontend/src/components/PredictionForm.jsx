import React from "react";
import { RefreshCw, Send } from "lucide-react";

function PredictionForm({ continents, countries, form, industries, loading, onChange, onSubmit }) {
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
            max="2030"
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
            min="0"
            name="funding_usd"
            onChange={onChange}
            step="1000000"
            type="number"
            value={form.funding_usd}
            required
          />
        </label>

        <label>
          Edad de la compañía
          <input
            min="0"
            name="company_age"
            onChange={onChange}
            type="number"
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
          <select name="continent" onChange={onChange} value={form.continent} required>
            {continents.map((continent) => (
              <option key={continent.value} value={continent.value}>
                {continent.label}
              </option>
            ))}
          </select>
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
