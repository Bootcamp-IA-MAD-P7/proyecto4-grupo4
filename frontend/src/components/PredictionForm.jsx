import React from "react";
import { RefreshCw, Send } from "lucide-react";

function PredictionForm({ countries, form, industries, loading, onChange, onSubmit }) {
  return (
    <form className="panel prediction-form" id="predict" onSubmit={onSubmit}>
      <div className="section-heading">
        <p>Consulta predictiva</p>
        <h2>Lectura inicial de potencial unicornio</h2>
      </div>

      <div className="form-grid">
        <label>
          Startup
          <input
            name="startup_name"
            onChange={onChange}
            type="text"
            value={form.startup_name}
          />
        </label>

        <label>
          Pais
          <select name="country" onChange={onChange} value={form.country} required>
            {countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </label>

        <label>
          Ciudad
          <input name="city" onChange={onChange} type="text" value={form.city} required />
        </label>

        <label>
          Industria
          <select name="industry" onChange={onChange} value={form.industry} required>
            {industries.map((industry) => (
              <option key={industry} value={industry}>
                {industry}
              </option>
            ))}
          </select>
        </label>

        <label>
          Año de ingreso
          <input
            max="2026"
            min="2007"
            name="join_year"
            onChange={onChange}
            type="number"
            value={form.join_year}
            required
          />
        </label>

        <label>
          Mes
          <input
            max="12"
            min="1"
            name="join_month"
            onChange={onChange}
            type="number"
            value={form.join_month}
            required
          />
        </label>

        <label>
          Inversores
          <input
            max="20"
            min="0"
            name="investor_count"
            onChange={onChange}
            type="number"
            value={form.investor_count}
            required
          />
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
