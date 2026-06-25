# App usage

## Arquitectura

- Frontend: React con Vite.
- Backend: FastAPI.
- Persistencia de feedback: SQLite en `backend/data/feedback/predictions.sqlite3`.
- Modelo: `backend/models/best_model.joblib`.
- Metricas: `backend/models/metrics.json`.

## Entrenamiento

Desde la carpeta `backend/`:

```bash
python scripts/train.py --report
```

El entrenamiento:

- genera `data/processed/dataset.pkl`;
- compara Ridge, Random Forest y Gradient Boosting;
- aplica validacion cruzada K-Fold;
- controla overfitting con el limite de `config.yaml`;
- guarda el mejor modelo en `models/best_model.joblib`;
- genera graficos de distribucion, residuos, prediccion vs real y feature importance.

## Contrato de prediccion

Endpoint:

```http
POST /predict
```

Payload:

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

## Contrato de feedback

Endpoint:

```http
POST /feedback
```

Payload:

```json
{
  "year_founded": 2015,
  "funding_usd": 50000000,
  "company_age": 11,
  "industry": "Fintech",
  "country": "United States",
  "continent": "North America",
  "predicted_valuation_usd": 1331072782.758,
  "actual_valuation_usd": 1100000000,
  "comment": "Close estimate"
}
```

Respuesta:

```json
{
  "id": 1,
  "status": "recorded",
  "message": "Feedback recorded successfully.",
  "timestamp": "2026-06-24T20:37:40.709902+00:00"
}
```

## Ejecucion local

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Por defecto el frontend espera la API en `http://127.0.0.1:8000`.

## Tests

```bash
python -m pytest backend/tests -q
```
