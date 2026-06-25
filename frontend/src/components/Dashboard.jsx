import React, { useEffect, useState } from "react";
import { Activity, CircleDollarSign, Globe2, PieChart } from "lucide-react";

import MetricCard from "./MetricCard";
import SignalBadge from "./SignalBadge";
import { buildMarketSignals, buildMetricCards, fetchMetrics, sectorMix } from "../data/modelMetrics";

const icons = [Globe2, Activity, CircleDollarSign, PieChart];

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [metricsStatus, setMetricsStatus] = useState("loading");

  useEffect(() => {
    let ignore = false;

    fetchMetrics()
      .then((body) => {
        if (ignore) return;
        setMetrics(body);
        setMetricsStatus("ready");
      })
      .catch(() => {
        if (ignore) return;
        setMetrics(null);
        setMetricsStatus("error");
      });

    return () => {
      ignore = true;
    };
  }, []);

  const metricCards = buildMetricCards(metrics);
  const marketSignals = buildMarketSignals(metrics);

  return (
    <section className="dashboard-section" id="dashboard">
      <div className="section-heading">
        <p>Panel</p>
        <h2>Señales históricas del mercado unicornio</h2>
      </div>

      {metricsStatus === "loading" ? (
        <p className="dashboard-status">Cargando métricas del backend...</p>
      ) : null}
      {metricsStatus === "error" ? (
        <p className="dashboard-status warning">Métricas del backend no disponibles.</p>
      ) : null}

      <div className="metrics-grid">
        {metricCards.map((metric, index) => {
          const Icon = icons[index] ?? Activity;
          return (
            <div className="metric-wrap" key={metric.label}>
              <Icon size={20} aria-hidden="true" />
              <MetricCard {...metric} />
            </div>
          );
        })}
      </div>

      <div className="analysis-grid">
        <article className="panel light-panel">
          <h3>Lectura de señal</h3>
          <div className="signal-list">
            {marketSignals.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <SignalBadge tone={item.tone}>{item.value}</SignalBadge>
              </div>
            ))}
          </div>
        </article>

        <article className="panel light-panel">
          <h3>Sectores principales de oportunidad</h3>
          <div className="sector-bars">
            {sectorMix.map((sector) => (
              <div key={sector.label}>
                <span>{sector.label}</span>
                <div className="bar-track">
                  <span style={{ width: `${sector.value}%` }} />
                </div>
                <strong>{sector.value}%</strong>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}

export default Dashboard;
