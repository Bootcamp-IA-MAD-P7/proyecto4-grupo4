# App Usage — Unicorn Valuation API

Guia de uso del stack completo: backend FastAPI + frontend React + base de datos PostgreSQL.

---

## 1. Levantar el stack

### Desarrollo local (recomendado)

Desde la **raiz del repositorio**:

```bash
docker compose up --build
```

Esto levanta tres servicios:

| Servicio   | URL local                  |
|------------|----------------------------|
| API        | http://localhost:8000      |
| Frontend   | http://localhost:5173      |
| PostgreSQL | localhost:5432 (interno)   |

### Solo el backend (sin Docker)

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns
uvicorn app.main:app --reload
```

---

## 2. Endpoints

### GET `/health`

Comprueba el estado del servicio y si el modelo esta cargado.

```bash
curl http://localhost:8000/health
```

Respuesta:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_r2": 0.22
}
```

---

### GET `/metrics`

Devuelve las metricas del modelo entrenado (MAE, RMSE, R2).

```bash
curl http://localhost:8000/metrics
```

---

### POST `/predict`

Predice la valoracion de una startup unicornio.

**Payload:**

```json
{
  "year_founded": 2015,
  "funding_usd": 50000000,
  "company_age": 9,
  "industry": "fintech",
  "country": "United States",
  "continent": "North America"
}
```

**Ejemplo curl:**

```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "year_founded": 2015,
    "funding_usd": 50000000,
    "company_age": 9,
    "industry": "fintech",
    "country": "United States",
    "continent": "North America"
  }' | python -m json.tool
```

**Respuesta:**

```json
{
  "valuation_usd": 1250000000.0,
  "valuation_b": 1.25,
  "model_version": "best_model.joblib",
  "timestamp": "2026-06-28T10:00:00+00:00"
}
```

---

### POST `/feedback`

Registra feedback del usuario sobre una prediccion. Persiste en PostgreSQL.

**Payload:**

```json
{
  "predicted_valuation_usd": 1250000000.0,
  "actual_valuation_usd": 1500000000.0,
  "rating": 4,
  "comment": "Estimacion cercana"
}
```

**Ejemplo curl:**

```bash
curl -s -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "predicted_valuation_usd": 1250000000.0,
    "actual_valuation_usd": 1500000000.0,
    "rating": 4,
    "comment": "Estimacion cercana"
  }'
```

**Respuesta (HTTP 201):**

```json
{
  "id": 1,
  "status": "recorded",
  "timestamp": "2026-06-28T10:00:00+00:00"
}
```

---

## 3. Frontend

### Desarrollo local

```bash
cd frontend
npm install
npm run dev
```

Disponible en `http://localhost:5173`. Conecta al backend segun `VITE_API_URL`.

Copiar `frontend/.env.example` a `frontend/.env` para configurar la URL:

```bash
cp frontend/.env.example frontend/.env
# Editar VITE_API_URL si el backend no esta en localhost:8000
```

---

## 4. Produccion (EC2)

En produccion el stack se despliega via `docker-compose.prod.yml` con imagenes pre-construidas desde Docker Hub.

| Servicio   | URL publica                        |
|------------|------------------------------------|
| API        | http://EC2_PUBLIC_IP:**8004**      |
| Frontend   | http://EC2_PUBLIC_IP:**3005**      |

Smoke test tras despliegue:

```bash
curl http://EC2_PUBLIC_IP:8004/health
```

El despliegue automatico se activa con cada push a `main` via `.github/workflows/deployment.yml`.
