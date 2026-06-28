# Unicorn Valuation Estimator

> **Herramienta de inteligencia predictiva para el análisis de startups unicornio.**
> Estima la valoración de una empresa en el momento de su inclusión al club unicornio a partir de sus características fundacionales: sector, país, edad, financiación y geografía.

**Demo en producción → [http://34.235.130.33:3005/](http://34.235.130.33:3005/)**

---

## Evaluación y Rúbrica

Este proyecto cumple los **cuatro niveles** de la rúbrica académica (Esencial → Medio → Avanzado → **Experto**). La trazabilidad completa de cada requisito frente a la implementación está documentada en:

**→ [backend/docs/EVALUATION_RUBRIC.md](backend/docs/EVALUATION_RUBRIC.md)**

Resumen por nivel:

| Nivel | Cumplimiento | Destacado |
|-------|-------------|-----------|
| **Esencial** | ✅ | Regresión sobre múltiplo de valoración, EDA en notebooks, control de overfitting, FastAPI + React, R² = 0.42 (techo empírico documentado) |
| **Medio** | ✅ | Gradient Boosting, K-Fold (K=5), Optuna (50 trials), feedback real vía `PUT /predictions/{id}` |
| **Avanzado** | ✅ | Docker Compose multi-stage, PostgreSQL, AWS EC2, **28 tests Pytest** en verde |
| **Experto** | ✅ | A/B Testing, Data Drift (KS), reentrenamiento en background, **Dashboard MLOps interactivo** |

El **Panel MLOps** (`/mlops`) permite al tribunal evaluar directamente las capacidades de nivel experto: historial editable de predicciones, botón de reentrenamiento con Optuna + K-Fold, indicadores A/B por versión de modelo y métricas de rendimiento en tiempo real.

---

## ¿Qué problema resuelve?

El ecosistema de capital riesgo carece de herramientas accesibles para estimar rápidamente el potencial de valoración de una startup. Los analistas dependen de comparables manuales o modelos de hoja de cálculo que no escalan ni aprenden de datos históricos.

**Unicorn Valuation Estimator** convierte un conjunto reducido de datos objetivos en una predicción cuantificable, permitiendo:

- **Inversores y fondos de VC** → Pre-filtrar oportunidades de inversión antes del due diligence.
- **Founders y equipos de startups** → Calibrar expectativas de valoración en rondas de financiación.
- **Analistas e investigadores** → Explorar patrones de valoración por sector, geografía y antigüedad.
- **Equipos académicos** → Demostrar un pipeline MLOps completo end-to-end sobre datos reales.

---

## Cómo funciona

```
Usuario introduce datos                API FastAPI                   Modelo ML
─────────────────────    ──────────────────────────────    ─────────────────────────
sector, país, año        POST /predict                     GradientBoostingRegressor
fundación, funding   →   valida schema Pydantic        →   entrenado sobre ~1 062
edad de empresa          devuelve valuation_usd            startups unicornio reales
                         y valuation_b (miles de M)        (Kaggle, hasta sept 2022)
```

El modelo predice `valuation_usd` a partir de seis features:

| Feature | Descripción |
|---------|-------------|
| `year_founded` | Año de fundación de la empresa |
| `funding_usd` | Total de financiación recibida (en dólares) |
| `company_age` | Antigüedad de la empresa en años |
| `industry` | Sector industrial (fintech, healthtech, e-commerce…) |
| `country` | País de origen |
| `continent` | Región geográfica derivada del país |

---

## Arquitectura

```
proyecto4-grupo4/
│
├── frontend/                    # SPA React + Vite + Bootstrap
│   ├── src/
│   │   ├── pages/               # Predicción, Panel, Metodología, Panel MLOps
│   │   ├── components/          # Formulario, PredictionsTable, MLOpsPanel…
│   │   └── api.js               # Cliente HTTP hacia la API (VITE_API_URL)
│   ├── Dockerfile               # Multi-stage: builder Node 20 → runner Nginx
│   └── nginx.conf
│
├── backend/                     # API FastAPI + Pipeline ML
│   ├── app/                     # Endpoints, schemas Pydantic, servicios
│   ├── src/                     # Pipeline ML (datos, modelos, preprocesamiento)
│   ├── scripts/train.py         # Entrenamiento K-Fold + Optuna con quality gate
│   ├── tests/                   # Suite pytest (28 tests)
│   ├── models/                  # best_model.joblib — generado en build, no versionado
│   ├── data/raw/                # unicorn_companies.csv (dataset Kaggle)
│   ├── Dockerfile               # Entrena el modelo en build y sirve con uvicorn
│   └── requirements.txt
│
├── docker-compose.yml           # Stack local de desarrollo
├── docker-compose.prod.yml      # Stack de producción EC2 (puertos 8004 / 3005)
└── .github/workflows/
    └── deployment.yml           # CI/CD: test → build → push → deploy en EC2
```

### Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend | React 18, Vite, Bootstrap 5 |
| Backend / API | FastAPI, Uvicorn, Pydantic v2 |
| Machine Learning | scikit-learn (GradientBoostingRegressor), pandas, numpy |
| Base de datos | PostgreSQL 15 (feedback de usuarios) |
| Contenedores | Docker, Docker Compose |
| CI/CD | GitHub Actions (test → build → deploy) |
| Infraestructura | AWS EC2, Docker Hub |

---

## Arranque rápido (primera vez)

### Prerrequisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose)
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/<org>/proyecto4-grupo4.git
cd proyecto4-grupo4
```

### 2. Levantar el stack completo

```bash
docker compose up --build
```

Esto lanza tres servicios de forma automática:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:5173 | Interfaz React |
| API | http://localhost:8000 | FastAPI + modelo ML |
| PostgreSQL | localhost:5434 | Base de datos de feedback |

> El primer arranque tarda 2–4 minutos porque entrena el modelo ML dentro del contenedor de la API.

### 3. Comprobar que todo funciona

```bash
# Salud de la API
curl http://localhost:8000/health
# → {"status":"ok","model_loaded":true,"model_r2":0.22}

# Predicción de ejemplo
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,
       "industry":"fintech","country":"United States","continent":"North America"}' \
  | python3 -m json.tool
```

### Detener el stack

```bash
docker compose down          # Para los contenedores (conserva datos)
docker compose down -v       # Para y elimina el volumen de PostgreSQL
```

---

## Desarrollo local (sin Docker)

Para trabajar en el código con recarga en caliente:

```bash
# Terminal 1 — Backend (requiere PostgreSQL local o contenedor db activo)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/train.py --report --allow-low-r2-artifact
export DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5434/unicorns
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

## Tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/ -v --tb=short
```

**28 tests en verde.** La suite cubre endpoints API, pipeline ML, integridad de datos y el módulo MLOps completo (`test_mlops.py`: predicciones, retrain, drift, A/B Testing, concurrencia).

---

## Despliegue en producción

La aplicación está desplegada en AWS EC2 y accesible en:

**[http://34.235.130.33:3005/](http://34.235.130.33:3005/)**

| Servicio | Puerto externo | Puerto interno |
|----------|---------------|----------------|
| API FastAPI | **8004** | 8000 |
| Frontend Nginx | **3005** | 80 |
| PostgreSQL | 5434 (debug) | 5432 |

El pipeline CI/CD en `.github/workflows/deployment.yml` realiza automáticamente en cada push a `main`:

1. **Test** — Ejecuta la suite pytest en GitHub Actions
2. **Build** — Construye imágenes Docker e inyecta `VITE_API_URL` en el bundle de Vite
3. **Push** — Sube imágenes a Docker Hub
4. **Deploy** — Conecta al EC2 por SSH, recrea los contenedores y ejecuta smoke tests

---

## API — Referencia rápida

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Estado del servicio y modelo |
| `GET` | `/metrics` | Métricas del modelo (R², MAE, RMSE) |
| `POST` | `/predict` | Predicción de valoración |
| `POST` | `/feedback` | Registro de feedback del usuario |
| `GET` | `/predictions` | Historial de predicciones (paginado) |
| `PUT` | `/predictions/{id}` | Actualizar valoración real observada |
| `POST` | `/retrain` | Lanzar reentrenamiento en background (202) |

Documentación interactiva Swagger: [http://34.235.130.33:8004/docs](http://34.235.130.33:8004/docs)

---

## Equipo

Proyecto académico desarrollado bajo metodología **SDD (Spec-Driven Development)** como parte del Bootcamp de IA — Factoría F5, Madrid 2026.

| Integrante | Área principal |
|------------|----------------|
| Integrante 1 | Dataset, EDA y calidad de datos |
| Integrante 2 | Pipeline ML y preprocesamiento |
| Integrante 3 | API FastAPI y base de datos |
| Integrante 4 | Frontend React y Docker |

---

## Licencia

Uso académico. Dataset original: [Kaggle — Unicorn Startups](https://www.kaggle.com/datasets/ramjasmaurya/unicorn-startups) (ramjasmaurya).
