# Backend — Unicorn Valuation API

API FastAPI que predice la valoracion de startups unicornio a partir de sus caracteristicas fundacionales.

## Estructura del Monorepo

```
proyecto4-grupo4/
├── backend/                         # API FastAPI, pipeline ML, tests, datos
├── frontend/                        # SPA React (Vite)
├── .specify/                        # Contrato, plan y tasks SDD
├── .github/                         # Workflows CI/CD
├── docker-compose.yml               # Stack de desarrollo local
├── docker-compose.prod.yml          # Stack de produccion EC2
└── .gitignore
```

## Estructura del Backend

```
backend/
├── app/                             # FastAPI application
│   ├── main.py                      # Entrypoint, rutas, CORS
│   ├── database.py                  # Inicializacion PostgreSQL
│   ├── input_schema.py              # Pydantic schemas (request/response)
│   ├── model_service.py             # Carga y ejecucion del modelo
│   └── feedback_service.py          # Registro de feedback en BD
├── src/                             # Pipeline ML
│   ├── data/
│   │   ├── load_data.py
│   │   └── data_validation.py
│   ├── preprocessing/
│   │   └── preprocessing_pipeline.py
│   └── models/
│       ├── train.py
│       └── evaluate.py
├── scripts/
│   ├── train.py                     # Entrenamiento con quality gate (R2>=0.50)
│   └── run_eda.py
├── tests/                           # Suite pytest
├── models/
│   ├── best_model.joblib            # (generado por scripts/train.py, no versionado)
│   └── metrics.json                 # (generado por scripts/train.py, no versionado)
├── data/
│   ├── raw/
│   │   └── unicorn_companies.csv    # Dataset crudo de Kaggle
│   └── processed/
│       └── dataset.parquet          # Dataset procesado
├── docs/
│   ├── app_usage.md
│   ├── data_notes.md
│   └── experiment_log.md
├── reports/                         # Graficas EDA (no versionadas)
├── storage/                         # .gitkeep — sin SQLite
├── config.yaml                      # Rutas y umbrales canonicos
├── requirements.txt
└── Dockerfile
```

> La persistencia de feedback usa **PostgreSQL** via `DATABASE_URL`. No existe ningun archivo SQLite local.
> El modelo `best_model.joblib` se genera en tiempo de build del Dockerfile y no se versiona en Git.

---

## Instalacion y Ejecucion

### Opcion A — Stack completo con Docker (recomendado)

Desde la raiz del repositorio:

```bash
# Desarrollo local (levanta db, api y frontend)
docker compose up --build

# Solo el backend y la BD
docker compose up --build db api
```

El API queda disponible en `http://localhost:8000`.

### Opcion B — Desarrollo local sin Docker

Requiere PostgreSQL local o contenedor DB activo.

```bash
cd backend

# Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Entrenar el modelo (genera models/best_model.joblib y models/metrics.json)
python scripts/train.py --report --allow-low-r2-artifact

# Iniciar la API (requiere DATABASE_URL en el entorno)
export DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend conecta al backend segun `VITE_API_URL` (por defecto `http://localhost:8000`).
Copiar `frontend/.env.example` a `frontend/.env` para personalizar.

---

## Endpoints

| Metodo | Ruta       | Descripcion                                |
|--------|------------|--------------------------------------------|
| GET    | `/health`  | Estado del servicio y modelo               |
| GET    | `/metrics` | Metricas del modelo entrenado              |
| POST   | `/predict` | Prediccion de valoracion unicornio         |
| POST   | `/feedback`| Registro de feedback sobre una prediccion  |

Ejemplo de prediccion:

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

---

## Tests

```bash
cd backend
pytest tests/ -v
```

> El test `test_train_meets_min_r2` falla actualmente porque R²~0.22 < 0.50. Esto es deuda tecnica documentada (ADR-001, `docs/architecture_decision_target.md`) y se resolvera en Fase 7. El resto de tests deben pasar en verde.

---

## Despliegue en Produccion (EC2)

Los puertos definitivos asignados en el Security Group de AWS:

| Servicio         | Puerto Host | Puerto Contenedor |
|------------------|-------------|-------------------|
| API FastAPI       | **8004**    | 8000              |
| Frontend Nginx    | **3005**    | 80                |
| PostgreSQL (debug)| 5434        | 5432              |

El pipeline CI/CD en `.github/workflows/deployment.yml` construye las imagenes, las sube a Docker Hub y las despliega en EC2 automaticamente en cada push a `main`.

Ver `docker-compose.prod.yml` para la configuracion completa de produccion.
