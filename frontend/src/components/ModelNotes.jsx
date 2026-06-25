import React from "react";

import { dataSources } from "../data/modelMetrics";

function ModelNotes() {
  return (
    <section className="info-page" id="model">
      <div className="section-heading">
        <p>Modelo y datos</p>
        <h2>Que esta conectado y que es referencia visual</h2>
      </div>

      <div className="source-grid">
        {dataSources.map((source) => (
          <article className="panel source-card" key={source.label}>
            <span>{source.label}</span>
            <strong>{source.value}</strong>
            <p>{source.note}</p>
          </article>
        ))}
      </div>

      <article className="panel limitation-card">
        <h3>Lectura responsable</h3>
        <p>
          El Oraculo identifica senales, no certezas. Las metricas visibles explican
          el rendimiento de referencia del proyecto y la prediccion operativa se obtiene
          del backend. El modelo activo es un Gradient Boosting entrenado sobre funding,
          edad de la empresa, industria, pais y continente; el feedback se guarda para
          monitorizar futuras mejoras y reentrenamientos.
        </p>
      </article>
    </section>
  );
}

export default ModelNotes;
