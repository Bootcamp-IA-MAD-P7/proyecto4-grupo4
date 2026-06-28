import React from "react";

import MLOpsPanel from "../components/MLOpsPanel";
import PredictionsTable from "../components/PredictionsTable";

function MLOpsDashboard() {
  return (
    <section className="route-page mlops-page">
      <div className="route-heading">
        <p className="eyebrow">Operaciones de Machine Learning</p>
        <h1>Panel MLOps</h1>
        <p className="mlops-subtitle">
          Monitorización, reentrenamiento y análisis A/B del modelo en producción.
        </p>
      </div>

      <MLOpsPanel />

      <div className="mlops-page-spacer">
        <PredictionsTable />
      </div>
    </section>
  );
}

export default MLOpsDashboard;
