# App usage

Este modulo corresponde a la rama `feature/member-4-app-feedback`.

## Arquitectura

- Frontend: React con Vite y Bootstrap.
- Backend: FastAPI.
- Persistencia inicial: SQLite en `data/feedback/predictions.sqlite3`.
- Modelo: `models/current_model.pkl` cuando exista; mientras tanto se usa `mock_model`.

## Contrato de prediccion

Endpoint:

```http
POST /predict
```

Payload:

```json
{
  "country": "United States",
  "city": "San Francisco",
  "industry": "Fintech",
  "join_year": 2021,
  "join_month": 7,
  "investor_count": 3
}
```

Respuesta:

```json
{
  "request_id": "uuid",
  "prediction_billion_usd": 3.25,
  "unit": "billion_usd",
  "model_used": "mock_model",
  "message": "Prediction generated successfully."
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
  "request_id": "uuid",
  "feedback_score": 4,
  "actual_valuation_b": 3.5,
  "comments": "Close estimate"
}
```

## Backend

Instalar dependencias Python si aun no estan disponibles:

```bash
python -m pip install fastapi "uvicorn[standard]" pydantic pandas numpy scikit-learn joblib python-dotenv pytest httpx
```

Ejecutar API:

```bash
uvicorn app.main:app --reload
```

Comprobar salud:

```bash
curl http://127.0.0.1:8000/health
```

## Frontend

Desde `frontend/`:

```bash
npm install
npm run dev
```

Por defecto el frontend espera la API en:

```text
http://127.0.0.1:8000
```

Para cambiarlo, crear `frontend/.env` usando `frontend/.env.example`.

## Tests

Desde la raiz del repo:

```bash
pytest
```
