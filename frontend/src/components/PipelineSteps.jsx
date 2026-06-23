import React from "react";

import { pipelineSteps } from "../data/modelMetrics";

function PipelineSteps() {
  return (
    <section className="method-section" id="methodology">
      <div className="section-heading">
        <p>Metodología</p>
        <h2>Pipeline de valoración predictiva</h2>
      </div>

      <div className="pipeline">
        {pipelineSteps.map((step, index) => (
          <article key={step}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{step}</strong>
          </article>
        ))}
      </div>

      <p className="method-copy" id="model">
        El modelo transforma variables disponibles en etapas tempranas en señales
        numéricas y categóricas. A partir de ellas estima una valoración esperada
        y compara su desempeño contra un baseline simple.
      </p>
    </section>
  );
}

export default PipelineSteps;
