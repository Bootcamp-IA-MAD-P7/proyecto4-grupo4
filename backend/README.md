# Proyecto 4 - Grupo 4: Unicorn Valuation

Prediccion de la valoracion de startups unicornio como problema de regresion.

## Estado actual

- Dataset local: `data/raw/unicorn_companies.csv`.
- Dataset procesado: `data/processed/dataset.pkl`.
- Modelo entrenado: `models/best_model.joblib`.
- Metricas: `models/metrics.json`.
- API: FastAPI con endpoints `/health`, `/predict` y `/feedback`.
- Frontend: React/Vite conectado al contrato actual de la API.
- Persistencia de feedback: SQLite.
- Tests backend: `20 passed`.

## Modelo

El entrenamiento compara:

- Ridge
- Random Forest
- Gradient Boosting

El modelo ganador actual es `gradient_boosting`.

Metricas de validacion actuales:

| Metrica | Valor |
|---|---:|
| RMSE | 6.40B USD |
| MAE | 1.68B USD |
| R2 | 0.2207 |
| Overfitting max gap | 0.0% |
| CV R2 medio | 0.2757 |

## Features

Features numericas:

- `year_founded`
- `log_funding_usd`
- `funding_velocity`
- `funding_vs_industry`
- `company_age`

Features categoricas:

- `industry`
- `country`
- `continent`

El target es `valuation_usd`.

## Entrenamiento

```bash
cd backend
python -m pip install -r requirements.txt
python scripts/train.py --report
```

Esto genera:

- `data/processed/dataset.pkl`
- `models/best_model.joblib`
- `models/metrics.json`
- `reports/target_distribution.png`
- `reports/pred_vs_actual.png`
- `reports/residuals.png`
- `reports/feature_importance.png`

## API

```bash
cd backend
uvicorn app.main:app --reload
```

Ejemplo de prediccion:

```json
{
  "year_founded": 2015,
  "funding_usd": 50000000,
  "company_age": 11,
  "industry": "Fintech",
  "country": "United States",
  "continent": "North America"
}
```

Respuesta:

```json
{
  "valuation_usd": 1331072782.758,
  "valuation_b": 1.3311,
  "model_version": "best_model.joblib",
  "model_used": "trained_model",
  "message": "Prediction generated successfully.",
  "timestamp": "2026-06-24T20:37:40.574476+00:00"
}
```

## Frontend

```bash
cd frontend
npm ci
npm run dev
```

El frontend usa `VITE_API_URL`; por defecto apunta a `http://127.0.0.1:8000`.

## Tests

```bash
python -m pytest backend/tests -q
```

## Docker

```bash
docker compose up --build
```

La imagen espera que exista `models/best_model.joblib`. Para regenerarlo, ejecutar primero el entrenamiento.

## Notas de rendimiento

El dataset tiene outliers severos y una cola alta dificil de aprender con las variables disponibles. Por eso el objetivo principal es mantener un modelo funcional, validado, sin overfitting superior al 5%, con metricas transparentes y una aplicacion capaz de recoger feedback para futuras mejoras.
