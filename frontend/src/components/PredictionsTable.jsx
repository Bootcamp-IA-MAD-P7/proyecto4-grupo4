import React, { useCallback, useEffect, useState } from "react";

import { getPredictions, updatePrediction } from "../api";

const PAGE_SIZE = 50;

function fmt(value, decimals = 2) {
  if (value == null) return "—";
  return Number(value).toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtUSD(value) {
  if (value == null) return "—";
  const billions = Number(value) / 1e9;
  if (Math.abs(billions) >= 1) return `$${fmt(billions, 2)}B`;
  const millions = Number(value) / 1e6;
  return `$${fmt(millions, 1)}M`;
}

function RowEditor({ row, onSaved }) {
  const [actual, setActual] = useState(row.actual_valuation_usd ?? "");
  const [comment, setComment] = useState(row.comment ?? "");
  const [status, setStatus] = useState("idle");

  async function handleSave() {
    if (actual === "" || Number(actual) <= 0) return;
    setStatus("saving");
    try {
      await updatePrediction(row.id, {
        actual_valuation_usd: Number(actual),
        comment: comment || null,
      });
      setStatus("ok");
      onSaved();
      setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  }

  return (
    <tr className="mlops-tr">
      <td className="mlops-td mlops-td-mono">{row.id}</td>
      <td className="mlops-td mlops-td-hide-sm">{row.industry ?? "—"}</td>
      <td className="mlops-td mlops-td-hide-sm">{row.country ?? "—"}</td>
      <td className="mlops-td mlops-td-num">{fmtUSD(row.funding_usd)}</td>
      <td className="mlops-td mlops-td-num">{fmtUSD(row.predicted_valuation_usd)}</td>
      <td className="mlops-td mlops-td-num">{fmt(row.predicted_multiple)}×</td>
      <td className="mlops-td">
        <span className={`mlops-badge mlops-badge-${row.model_version ?? "prod"}`}>
          {row.model_version ?? "prod"}
        </span>
      </td>
      <td className="mlops-td">
        <input
          aria-label="Valoración real en USD"
          className="mlops-input"
          min="1"
          placeholder="USD"
          step="1000000"
          type="number"
          value={actual}
          onChange={(e) => setActual(e.target.value)}
        />
      </td>
      <td className="mlops-td">
        <input
          aria-label="Comentario"
          className="mlops-input mlops-input-wide"
          placeholder="Comentario opcional"
          type="text"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </td>
      <td className="mlops-td">
        <button
          className="mlops-btn mlops-btn-sm"
          disabled={status === "saving" || actual === ""}
          onClick={handleSave}
        >
          {status === "saving" ? "Guardando…" : status === "ok" ? "✓ Guardado" : status === "error" ? "✗ Error" : "Guardar"}
        </button>
      </td>
      <td className="mlops-td mlops-td-mono mlops-td-hide-sm">
        {row.created_at ? new Date(row.created_at).toLocaleDateString("es-ES") : "—"}
      </td>
    </tr>
  );
}

function PredictionsTable() {
  const [rows, setRows] = useState([]);
  const [loadStatus, setLoadStatus] = useState("loading");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const load = useCallback(
    async (pageNum) => {
      setLoadStatus("loading");
      try {
        const data = await getPredictions(PAGE_SIZE, pageNum * PAGE_SIZE);
        setRows(data);
        setHasMore(data.length === PAGE_SIZE);
        setLoadStatus("ready");
      } catch {
        setLoadStatus("error");
      }
    },
    []
  );

  useEffect(() => {
    load(page);
  }, [load, page]);

  function handleSaved() {
    load(page);
  }

  return (
    <div className="mlops-card">
      <div className="mlops-card-header">
        <h3 className="mlops-card-title">Historial de Predicciones</h3>
        <span className="mlops-hint mlops-hint-block">
          Introduce el valor real observado por fila. Puedes guardar <strong>las veces que quieras</strong> en la misma fila (actualiza el registro). Cada nueva predicción en /predict crea una fila distinta.
        </span>
      </div>

      {loadStatus === "loading" && (
        <p className="mlops-status">Cargando predicciones…</p>
      )}
      {loadStatus === "error" && (
        <p className="mlops-status mlops-status-error">No se pudieron cargar las predicciones.</p>
      )}

      {loadStatus === "ready" && rows.length === 0 && (
        <p className="mlops-status">Sin predicciones registradas todavía. Realiza tu primera predicción.</p>
      )}

      {loadStatus === "ready" && rows.length > 0 && (
        <>
          <div className="mlops-table-wrap">
            <table className="mlops-table">
              <thead>
                <tr>
                  <th className="mlops-th">ID</th>
                  <th className="mlops-th mlops-th-hide-sm">Industria</th>
                  <th className="mlops-th mlops-th-hide-sm">País</th>
                  <th className="mlops-th">Financiación</th>
                  <th className="mlops-th">Val. Predicha</th>
                  <th className="mlops-th">Múltiplo pred.</th>
                  <th className="mlops-th">Versión</th>
                  <th className="mlops-th">Val. Real (USD)</th>
                  <th className="mlops-th">Comentario</th>
                  <th className="mlops-th">Acción</th>
                  <th className="mlops-th mlops-th-hide-sm">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <RowEditor key={row.id} row={row} onSaved={handleSaved} />
                ))}
              </tbody>
            </table>
          </div>

          <div className="mlops-pagination">
            <button
              className="mlops-btn"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              ← Anterior
            </button>
            <span className="mlops-page-info">Página {page + 1}</span>
            <button
              className="mlops-btn"
              disabled={!hasMore}
              onClick={() => setPage((p) => p + 1)}
            >
              Siguiente →
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default PredictionsTable;
