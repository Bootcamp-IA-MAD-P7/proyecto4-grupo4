from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_config, resolve_path
from src.data.load import build_features, load_raw_dataset
from src.models.train import load_pipeline
from src.storage.db import init_db, save_new_observation, save_prediction_feedback

st.set_page_config(page_title="Unicorn Valuation Predictor", layout="wide")


@st.cache_data
def get_reference_options() -> dict[str, list[str]]:
    raw = load_raw_dataset()
    featured = build_features(raw)
    return {
        "industries": sorted(featured["industry"].unique().tolist()),
        "countries": sorted(featured["country"].unique().tolist()),
        "continents": sorted(featured["continent"].unique().tolist()),
    }


@st.cache_resource
def get_model():
    return load_pipeline()


def load_metrics() -> dict:
    metrics_path = resolve_path(load_config()["paths"]["metrics_file"])
    if not metrics_path.exists():
        return {}
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def format_billions(value: float) -> str:
    return f"${value / 1e9:,.2f}B"


def main() -> None:
    init_db()
    options = get_reference_options()
    metrics = load_metrics()

    st.title("Unicorn Valuation Predictor")
    st.caption("MVP Esencial · Base escalable hacia MLOps")

    tab_predict, tab_metrics, tab_feedback, tab_ingest = st.tabs(
        ["Predicción", "Rendimiento", "Feedback", "Nuevos datos"]
    )

    with tab_predict:
        col1, col2 = st.columns(2)
        with col1:
            industry = st.selectbox("Industria", options["industries"])
            country = st.selectbox("País", options["countries"])
            continent = st.selectbox("Continente", options["continents"])
        with col2:
            year_founded = st.number_input("Año de fundación", min_value=1980, max_value=2026, value=2015)
            funding_usd = st.number_input("Funding (USD)", min_value=0.0, value=500_000_000.0, step=10_000_000.0)

        company_age = datetime.now().year - int(year_founded)
        input_df = pd.DataFrame(
            [
                {
                    "year_founded": year_founded,
                    "funding_usd": funding_usd,
                    "company_age": company_age,
                    "industry": industry,
                    "country": country,
                    "continent": continent,
                }
            ]
        )

        if st.button("Predecir valoración", type="primary"):
            model = get_model()
            prediction = float(model.predict(input_df)[0])
            st.success(f"Valoración estimada: **{format_billions(prediction)}**")
            st.session_state["last_prediction"] = {
                "input": input_df.iloc[0].to_dict(),
                "prediction": prediction,
            }

    with tab_metrics:
        if not metrics:
            st.warning("Entrena el modelo primero: `python scripts/train.py --report`")
        else:
            val = metrics["validation"]
            overfit = metrics["overfitting"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RMSE (val)", f"{val['rmse']:,.0f}")
            c2.metric("MAE (val)", f"{val['mae']:,.0f}")
            c3.metric("R² (val)", f"{val['r2']:.3f}")
            c4.metric("Gap overfitting", f"{overfit['max_gap_pct']:.2f}%")

            reports_dir = resolve_path("reports")
            for image_name in [
                "target_distribution.png",
                "pred_vs_actual.png",
                "residuals.png",
                "feature_importance.png",
            ]:
                image_path = reports_dir / image_name
                if image_path.exists():
                    st.image(str(image_path), caption=image_name.replace("_", " ").replace(".png", ""))

    with tab_feedback:
        st.subheader("Feedback de predicciones")
        if "last_prediction" not in st.session_state:
            st.info("Genera una predicción en la pestaña anterior para registrar feedback.")
        else:
            actual = st.number_input("Valoración real (USD, opcional)", min_value=0.0, value=0.0)
            rating = st.slider("Calidad percibida de la predicción (1-5)", 1, 5, 3)
            notes = st.text_area("Notas")
            if st.button("Guardar feedback"):
                payload = st.session_state["last_prediction"]["input"]
                save_prediction_feedback(
                    {
                        **payload,
                        "predicted_valuation": st.session_state["last_prediction"]["prediction"],
                        "actual_valuation": actual if actual > 0 else None,
                        "user_rating": rating,
                        "notes": notes or None,
                    }
                )
                st.success("Feedback guardado en SQLite.")

    with tab_ingest:
        st.subheader("Ingesta de nuevas observaciones")
        st.write("Base para reentrenamiento futuro (Nivel Medio/Avanzado).")
        new_industry = st.text_input("Industria")
        new_country = st.text_input("País")
        new_continent = st.text_input("Continente")
        new_year = st.number_input("Año fundación", min_value=1980, max_value=2026, value=2020, key="ingest_year")
        new_funding = st.number_input("Funding USD", min_value=0.0, value=100_000_000.0, key="ingest_funding")
        new_valuation = st.number_input("Valoración real USD", min_value=0.0, value=1_000_000_000.0)

        if st.button("Registrar observación"):
            payload = {
                "industry": new_industry,
                "country": new_country,
                "continent": new_continent,
                "year_founded": new_year,
                "funding_usd": new_funding,
                "company_age": datetime.now().year - int(new_year),
                "valuation_usd": new_valuation,
            }
            save_new_observation(payload)
            st.success("Observación almacenada para futuros reentrenamientos.")


if __name__ == "__main__":
    main()
