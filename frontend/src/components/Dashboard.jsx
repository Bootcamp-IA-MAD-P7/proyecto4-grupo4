import React from "react";
import { Activity, CircleDollarSign, Globe2, PieChart } from "lucide-react";

import MetricCard from "./MetricCard";
import SignalBadge from "./SignalBadge";
import { marketSignals, metricCards, sectorMix } from "../data/modelMetrics";

const icons = [Globe2, Activity, CircleDollarSign, PieChart];

function Dashboard() {
  return (
    <section className="dashboard-section" id="dashboard">
      <div className="section-heading">
        <p>Dashboard</p>
        <h2>Senales historicas del mercado unicornio</h2>
      </div>

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
          <h3>Top sectores de oportunidad</h3>
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
