import React from "react";

import { dataSources } from "../data/modelMetrics";

function ModelNotes() {
  return (
    <section className="info-page" id="model">
      <div className="section-heading">
        <p>Modelo y datos</p>
        <h2>Qué está conectado y qué es referencia visual</h2>
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
          El Oráculo identifica señales, no certezas. Las métricas visibles explican
          el rendimiento de referencia del proyecto y la predicción operativa se obtiene
          del backend. Hasta que el modelo real esté disponible, la API informa el estado
          del servicio y permite validar la interfaz de predicción.
        </p>
      </article>
    </section>
  );
}

export default ModelNotes;
