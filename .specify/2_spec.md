# Spec — Single Source of Truth

> Este documento es el contrato técnico del proyecto. Cualquier archivo de código, configuración o test que contradiga lo aquí escrito debe ser corregido.

---

## 1. Esquema de Columnas Definitivo

### Dataset Crudo de Entrada

Archivo fuente: `backend/data/raw/unicorn_companies.csv`

| Columna Original (Kaggle) | Tipo   | Descripción                          |
|---------------------------|--------|--------------------------------------|
| `Company`                 | string | Nombre de la startup                 |
| `Valuation ($B)`          | string | Valoración cruda, ej. `"$1.5"` → parsear a `float` |
| `Date Joined`             | string | Fecha de ingreso al club unicornio   |
| `Country`                 | string | País de origen                       |
| `City`                    | string | Ciudad de origen                     |
| `Industry`                | string | Industria/sector                     |
| `Select Investors`        | string | Lista de inversores separada por `,` |
| `Funding`                 | string | Funding crudo, ej. `"$500M"` → parsear a `float` |
| `Year Founded`            | int    | Año de fundación                     |

### Features de Modelado (X) — Esquema Definitivo Post-Parseo

Estos son los **únicos** nombres de columna válidos en todo el código Python, tests, y API.

| Nombre Columna   | Dtype   | Derivación                                            |
|------------------|---------|-------------------------------------------------------|
| `year_founded`   | int     | Directo de `Year Founded`                             |
| `funding_usd`    | float   | Parseo de `Funding` → dólares (M=1e6, B=1e9)         |
| `company_age`    | int     | `año_actual - year_founded`                           |
| `industry`       | string  | `Industry` normalizado (lowercase, top-N + "other")  |
| `country`        | string  | `Country` normalizado (top-N + "other")               |
| `continent`      | string  | Derivado de `country` mediante lookup                 |

### Variable Objetivo (y) — Fase 7+ (ADR-001)

| Nombre Columna | Dtype | Derivación                                                             |
|----------------|-------|------------------------------------------------------------------------|
| `multiple`     | float | `valuation_usd / funding_usd` — múltiplo de valoración (adimensional) |

> **Target de entrenamiento:** `log1p(multiple)`. El pipeline ML predice el múltiplo de valoración sobre el funding; `model_service.py` reconvierte internamente: `valuation_usd_pred = expm1(pred) × funding_usd`.
>
> **Contrato externo invariante:** `POST /predict` sigue devolviendo `valuation_usd` en dólares. El cambio es 100% interno al pipeline ML.
>
> **Prohibido:** usar `Valuation`, `Funding`, `Valuation ($B)`, `Investors`, `investor_count`, `join_year`, `join_month` como features del modelo en producción. Pueden existir sólo en notebooks históricos.

---

## 2. Estructura de Directorios del Monorepo

Tras la **Fase 0.5 (Reestructuración de Carpetas)**, la raíz del repositorio contiene **únicamente**:

```
proyecto4-grupo4/
├── backend/          # API FastAPI, ML pipeline, tests, datos
├── frontend/         # SPA React (Vite)
├── .specify/         # Contrato, plan y tasks del agente
├── .github/          # Workflows de CI/CD
├── docker-compose.yml
└── .gitignore
```

Todo el código Python, configuración ML, datos y tests viven bajo `backend/`:

```
backend/
├── app/              # FastAPI (main, schemas, services, database)
├── src/              # Pipeline ML (data, models, mlops, preprocessing)
├── scripts/          # train.py, run_eda.py
├── tests/            # pytest suite
├── models/           # best_model.joblib, metrics.json (no versionados)
├── storage/          # .gitkeep (sin SQLite)
├── data/             # raw/, processed/, feedback/
├── notebooks/        # EDA y experimentos
├── docs/             # app_usage.md, data_notes.md
├── config.yaml       # Rutas y umbrales canónicos
├── requirements.txt
├── Dockerfile
└── README.md         # Documentación del backend
```

> **Regla:** Ningún módulo Python, script ni archivo de configuración ML debe permanecer en la raíz del repositorio. Las rutas canónicas de la sección 2.1 son relativas a `backend/` (working directory del servicio `api`).

---

## 2.1 Rutas Canónicas de Artefactos

Toda referencia a archivos en `backend/config.yaml`, `backend/app/`, `backend/src/`, `backend/scripts/` y `backend/tests/` debe apuntar a estas rutas. Sin excepciones.

| Artefacto                | Ruta Canónica (desde raíz del repo)       | Notas                                                  |
|--------------------------|-------------------------------------------|--------------------------------------------------------|
| Dataset crudo            | `backend/data/raw/unicorn_companies.csv`  | Nunca en `notebooks/data/`                             |
| Dataset procesado        | `backend/data/processed/dataset.parquet`  | Formato parquet (eficiente, tipado)                    |
| Modelo serializado       | `backend/models/best_model.joblib`        | Única ruta válida; `unicorn_valuation_pipeline.joblib` y `current_model.pkl` quedan eliminados |
| Métricas del modelo      | `backend/models/metrics.json`             | Generado por `backend/scripts/train.py`                |
| Base de datos            | Servicio PostgreSQL (`db`)                | Sin archivo local. Conexión vía `DATABASE_URL`. Ambas SQLite (`storage/app.db`, `data/feedback/predictions.sqlite3`) eliminadas. |
| Reportes EDA             | `backend/reports/`                        | Generados, nunca versionados en Git                    |

> **Dentro de `backend/`:** las rutas en `config.yaml` y el código Python usan paths relativos al directorio `backend/` (ej. `models/best_model.joblib`, `data/raw/unicorn_companies.csv`). No incluir el prefijo `backend/` en imports ni en claves de `config.yaml`.

---

## 3. Umbral de Calidad del Modelo

```yaml
# backend/config.yaml — sección training
training:
  min_r2: 0.50
```

### Regla de CI

- El script `backend/scripts/train.py` finaliza con `sys.exit(1)` si `validation.r2 < 0.50`.
- El test `backend/tests/test_pipeline.py` afirma `r2 >= 0.50` (no `>= 0.15`).
- Ningún PR a `main` puede fusionarse si CI falla por este motivo.

> **Estado actual del modelo (post Fase 4 → Fase 7):** El modelo T1-T3 con target `valuation_usd` alcanza R²≈0.18–0.22. **Fase 7 implementa el target `multiple = valuation_usd / funding_usd` con K-Fold + Optuna** para superar el gate R² ≥ 0.50.
>
> **Requerimientos de entrenamiento (Nivel Experto — Fase 7):**
> - **Validación Cruzada:** `KFold(n_splits=5, shuffle=True, random_state=42)` implementado explícitamente en `backend/src/mlops/tuning.py`. Las métricas de validación se reportan como `r2_mean ± r2_std` sobre los 5 folds.
> - **Optimización de Hiperparámetros:** Optuna (`n_trials=50`, sampler TPE) optimiza los hiperparámetros del estimador. La función objetivo de cada trial es la media del R² K-Fold sobre `log1p(multiple)`. El trial con mayor R² medio determina los hiperparámetros del modelo de producción.
> - **Gate compuesto de calidad:** `enforce_quality_gate()` verifica simultáneamente `val_r2_mean >= 0.50` **y** `train_r2 - val_r2_mean < 0.05` (overfitting < 5%). Ambas condiciones deben cumplirse para que el modelo pase a producción.
>
> **Runtime Docker MVP:** `backend/Dockerfile` genera el artefacto con `python scripts/train.py --report --allow-low-r2-artifact`. Esta bandera solo permite guardar el modelo T1-T3 dentro de la imagen Docker; el comportamiento por defecto de `scripts/train.py` mantiene el gate bloqueante.

---

### 3.1 Fase 7 — Arquitectura MLOps Completa (ADR-001, Nivel Experto)

> **Referencia completa:** `backend/docs/architecture_decision_target.md` (ADR-001, 2026-06-25)

---

#### 3.1.1 Target: Múltiplo de Valoración (corrección de heterocedasticidad)

**Diagnóstico del modelo T1-T3 (bloqueante del R² ≥ 0.50):**

| Métrica diagnóstica | Valor |
|---|---|
| R² validación | 0.18–0.22 |
| R² cross-validation 5-fold | 0.24 ± 0.10 |
| Pendiente del Residual Plot | **+1.51 B USD / B USD predicho** |
| Ratio de heterocedasticidad | **5.05×** |

La causa estructural es doble: (1) **piso unicornio** — 70–75% del dataset en $1B–$3B, el modelo converge al centroide; (2) **heterocedasticidad escalar** — la varianza del error crece proporcionalmente a la magnitud de la valoración.

**Solución:** en lugar de predecir `valuation_usd` (absoluto), el modelo predice el **múltiplo de valoración**:

```
multiple = valuation_usd / funding_usd
```

Al dividir por `funding_usd` se elimina la mayor fuente de varianza condicional. El múltiplo es la métrica estándar "funding multiple" en capital riesgo y tiene distribución más simétrica.

**Flujo de inferencia (API transparente — contrato externo invariante):**

```
Input:  { funding_usd: 50_000_000, ... }
           ↓  Pipeline ML predice: multiple_pred = expm1(model.predict(features))
           ↓  Conversión interna:  valuation_usd_pred = multiple_pred × funding_usd
Output: { valuation_usd: 1_250_000_000.0, valuation_b: 1.25, ... }
```

---

#### 3.1.2 Pipeline de Entrenamiento: K-Fold + Optimización con Optuna

**Módulo:** `backend/src/mlops/tuning.py`

**Validación Cruzada K-Fold (k=5):**

- `KFold(n_splits=5, shuffle=True, random_state=42)` implementado explícitamente.
- Cada fold entrena en 4/5 del dataset y valida en 1/5 sin solapamiento.
- Las métricas reportadas son `r2_mean` y `r2_std` sobre los 5 folds.
- Elimina la sobreestimación del R² por train/test split único.

**Optimización de Hiperparámetros con Optuna (`n_trials=50`):**

- Framework: `optuna>=3.6.0` (ya declarado en `requirements.txt`).
- Espacio de búsqueda definido en `backend/config.yaml` bajo la sección `optuna`.
- Sampler: TPE (Tree-structured Parzen Estimator, por defecto de Optuna).
- Función objetivo de cada trial: **media del R² K-Fold** sobre `log1p(multiple)`.

| Hiperparámetro | Tipo | Rango canónico |
|---|---|---|
| `n_estimators` | int | [50, 300] |
| `max_depth` | int | [2, 8] |
| `learning_rate` | float log-uniform | [0.01, 0.3] |
| `subsample` | float | [0.6, 1.0] |
| `min_samples_split` | int | [2, 20] |

**Formato de `backend/models/metrics.json` (post Fase 7):**

```json
{
  "target": "multiple",
  "cv_folds": 5,
  "optuna_trials": 50,
  "best_trial_number": 37,
  "best_params": {
    "n_estimators": 200, "max_depth": 4,
    "learning_rate": 0.05, "subsample": 0.85, "min_samples_split": 5
  },
  "train":      { "r2": 0.62, "mae_multiple": 3.8 },
  "validation": { "r2_mean": 0.55, "r2_std": 0.04, "mae_mean": 4.5 },
  "overfitting_gap": 0.07
}
```

---

#### 3.1.3 A/B Testing: Modelo Producción vs Candidato

**Estrategia de enrutamiento dual en `backend/app/model_service.py`:**

| Modelo | Ruta | Condición de carga |
|---|---|---|
| **Producción** (`prod`) | `backend/models/best_model.joblib` | Siempre; error 503 si no existe |
| **Candidato** (`candidate`) | `backend/models/candidate_model.joblib` | Opcional; si no existe, 100% tráfico a producción |

**Regla de enrutamiento (peso configurable):**

```python
# backend/config.yaml → ab_testing.candidate_weight: 0.2
import random
model_used = "candidate" if (
    candidate_model and random.random() < cfg["ab_testing"]["candidate_weight"]
) else "prod"
```

**Registro en base de datos:** cada predicción persiste `model_version` (`"prod"` o `"candidate"`) en la tabla `predictions`. Esto permite calcular métricas comparativas reales por versión desde `GET /predictions`.

**Configuración en `backend/config.yaml`:**

```yaml
ab_testing:
  candidate_weight: 0.2   # proporción de tráfico al candidato (0.0–1.0)
  enabled: true
```

---

#### 3.1.4 Detección de Data Drift

**Módulo:** `backend/src/mlops/drift.py`

Se ejecuta automáticamente al inicio de cada ciclo de reentrenamiento (`POST /retrain`). Compara la distribución de features numéricas en los datos de feedback acumulados vs el dataset original de entrenamiento.

**Métodos:**

- **Test KS (Kolmogorov-Smirnov):** `scipy.stats.ks_2samp` para cada feature numérica (`funding_usd`, `year_founded`, `company_age`). p-valor < 0.05 indica drift significativo.
- **Desviación de media relativa:** `|mean_new - mean_orig| / mean_orig`. Se reporta si supera el 20%.

**Output:** `backend/models/drift_report.json`:

```json
{
  "timestamp": "2026-06-28T19:00:00Z",
  "drift_detected": true,
  "n_feedback_samples": 120,
  "n_original_samples": 978,
  "features": {
    "funding_usd":  { "ks_statistic": 0.21, "p_value": 0.003, "mean_drift_pct": 15.2, "drift": true },
    "year_founded": { "ks_statistic": 0.08, "p_value": 0.34,  "mean_drift_pct": 0.3,  "drift": false },
    "company_age":  { "ks_statistic": 0.12, "p_value": 0.07,  "mean_drift_pct": 5.1,  "drift": false }
  }
}
```

El reentrenamiento **continúa independientemente** del resultado del drift; el informe se expone al frontend como información diagnóstica.

**Dependencia:** `scipy>=1.13.0` (añadida en sección 6).

---

#### 3.1.5 Reglas MLOps del Reentrenamiento Automático (`POST /retrain`)

El endpoint dispara la siguiente lógica en `BackgroundTasks`:

```
1. DRIFT CHECK
   → drift.detect_drift() → guarda drift_report.json
   → No bloquea; el retrain continúa siempre

2. TRAIN (K-Fold + Optuna)
   → train.py → genera metrics_candidate.json
   → serializa candidate_model.joblib (provisional)

3. AUTO-REPLACEMENT DECISION
   new_r2    = metrics_candidate["validation"]["r2_mean"]
   current_r2= metrics_prod["validation"]["r2_mean"]
   gap       = metrics_candidate["train"]["r2"] - new_r2

   CASO A — Reemplazo directo:
     SI new_r2 > current_r2 AND gap < 0.05:
       best_model.joblib ← candidate_model.joblib
       metrics.json ← metrics_candidate.json
       model_service recarga best_model.joblib
       log: "Modelo reemplazado (R²: {current_r2:.3f} → {new_r2:.3f})"

   CASO B — Candidato para A/B Testing:
     SI new_r2 > current_r2 AND gap >= 0.05:
       candidate_model.joblib se mantiene activo para A/B
       log: "Candidato A/B (overfitting={gap:.3f} >= 0.05)"

   CASO C — Descarte:
     SI new_r2 <= current_r2:
       rm candidate_model.joblib
       log: "Candidato descartado (R²: {new_r2:.3f} <= {current_r2:.3f})"
```

---

#### Archivos involucrados en Fase 7

| Ticket | Archivo | Cambio principal |
|---|---|---|
| `[T-7.1]` | `backend/app/database.py` | Añadir columnas `predicted_multiple`, `actual_multiple`, `model_version` al ORM |
| `[T-7.2]` | `backend/config.yaml` | Añadir secciones `optuna`, `ab_testing`, `drift`; clave `target_transform: multiple` |
| `[T-7.3]` | `backend/src/mlops/tuning.py` (nuevo) | K-Fold + Optuna; `train.py` refactorizado para target múltiplo |
| `[T-7.4]` | `backend/app/model_service.py` | A/B Testing + reconversión `multiple → valuation_usd` |
| `[T-7.5]` | `backend/app/input_schema.py` | Schemas para `GET /predictions`, `PUT /predictions/{id}`, `POST /retrain` |
| `[T-7.6]` | `backend/app/main.py` + `feedback_service.py` | Registrar nuevos endpoints; lógica PUT y BackgroundTasks |
| `[T-7.7]` | `backend/src/mlops/drift.py` (nuevo) | Detección de Data Drift (KS + desviación de media) |
| `[T-7.8]` | `backend/tests/test_mlops.py` (nuevo) | Tests para nuevos endpoints, A/B Testing y drift |
| `[T-7.9]` | `frontend/src/` | Nueva pestaña "Panel MLOps" con tabla interactiva y panel de control |
| `[T-7.10]` | `backend/scripts/train.py` + `backend/models/` | Reentrenar con K-Fold+Optuna, validar R² ≥ 0.50, cerrar Fase 7 |

---

## 4. API FastAPI — Contrato de Endpoints

Base URL: `http://localhost:8000`

### `POST /predict`

**Request body:**
```json
{
  "year_founded": 2015,
  "funding_usd": 50000000.0,
  "company_age": 9,
  "industry": "fintech",
  "country": "United States",
  "continent": "North America"
}
```

**Response 200:**
```json
{
  "valuation_usd": 1250000000.0,
  "valuation_b": 1.25,
  "model_version": "best_model.joblib",
  "timestamp": "2026-06-23T10:00:00Z"
}
```

**Errores:**
- `422 Unprocessable Entity` — campos faltantes o tipos inválidos (validado por Pydantic)
- `503 Service Unavailable` — modelo no cargado

---

### `POST /feedback`

Permite al usuario reportar la valoración real observada para mejorar datos de entrenamiento futuros.

**Request body:**
```json
{
  "year_founded": 2015,
  "funding_usd": 50000000.0,
  "company_age": 9,
  "industry": "fintech",
  "country": "United States",
  "continent": "North America",
  "predicted_valuation_usd": 1250000000.0,
  "actual_valuation_usd": 1100000000.0,
  "comment": "Opcional: nota del usuario"
}
```

**Response 201:**
```json
{
  "id": 42,
  "status": "recorded",
  "timestamp": "2026-06-23T10:00:05Z"
}
```

---

### `GET /health`

**Response 200:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_r2": 0.52
}
```

---

### `GET /metrics`

Devuelve el contenido de `models/metrics.json` para que el frontend pueda mostrar estadísticas del modelo sin hardcodear valores.

**Response 200:** contenido completo de `backend/models/metrics.json`

---

### `GET /predictions`

Devuelve el historial completo de predicciones almacenadas en la tabla `predictions`, ordenadas por `created_at` descendente. Alimenta la tabla interactiva del Panel MLOps en el frontend.

**Query params (opcionales):**
- `limit: int = 100` — número máximo de registros
- `offset: int = 0` — paginación

**Response 200:**
```json
[
  {
    "id": 42,
    "year_founded": 2015,
    "funding_usd": 50000000.0,
    "company_age": 9,
    "industry": "fintech",
    "country": "United States",
    "continent": "North America",
    "predicted_valuation_usd": 1250000000.0,
    "predicted_multiple": 25.0,
    "actual_valuation_usd": 1100000000.0,
    "actual_multiple": 22.0,
    "comment": "Valoración real post-ronda B",
    "model_version": "prod",
    "created_at": "2026-06-28T19:00:00Z"
  }
]
```

**Errores:**
- `503 Service Unavailable` — base de datos no disponible

---

### `PUT /predictions/{id}`

Actualiza los campos `actual_valuation_usd` y/o `comment` de un registro existente. El backend calcula automáticamente `actual_multiple = actual_valuation_usd / funding_usd` y lo persiste. Permite al usuario proporcionar el valor real observado para enriquecer los datos de reentrenamiento.

**Path parameter:** `id` — integer, identificador del registro en la tabla `predictions`.

**Request body:**
```json
{
  "actual_valuation_usd": 1100000000.0,
  "comment": "Valoración real observada post-ronda B"
}
```

**Response 200:**
```json
{
  "id": 42,
  "status": "updated",
  "actual_multiple": 22.0,
  "timestamp": "2026-06-28T19:05:00Z"
}
```

**Errores:**
- `404 Not Found` — registro no encontrado
- `422 Unprocessable Entity` — tipos inválidos o `actual_valuation_usd` negativo

---

### `POST /retrain`

Dispara de forma **asíncrona** (FastAPI `BackgroundTasks`) la ejecución del ciclo MLOps completo: detección de Data Drift + reentrenamiento con K-Fold + Optuna + auto-reemplazo del modelo según las reglas de `3_spec.md §3.1.5`.

**Request body:** vacío (`{}` o sin cuerpo).

**Response 202 Accepted:**
```json
{
  "status": "retrain_started",
  "message": "El proceso de reentrenamiento se ha iniciado en segundo plano.",
  "timestamp": "2026-06-28T19:10:00Z"
}
```

**Comportamiento asíncrono (BackgroundTasks):**
1. `drift.detect_drift()` → genera `backend/models/drift_report.json`.
2. Ejecuta K-Fold + Optuna vía `src/mlops/tuning.py` → genera `models/metrics_candidate.json` y `models/candidate_model.joblib`.
3. Aplica la regla de auto-reemplazo (§3.1.5): el resultado es reemplazo directo, candidato A/B o descarte.

**Errores:**
- `503 Service Unavailable` — ya hay un reentrenamiento en curso (flag `_retrain_in_progress` en memoria)

---

## 5. Base de Datos PostgreSQL — Esquema

**Motor:** PostgreSQL 15 (imagen `postgres:15-alpine` en Docker Compose).

**Conexión:** la variable de entorno `DATABASE_URL` es la única fuente de configuración.

```
# Formato canónico
DATABASE_URL=postgresql://unicorn_user:unicorn_pass@db:5432/unicorns

# Desarrollo local sin Docker (PostgreSQL instalado en el host)
DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns
```

> `backend/app/database.py` lee `os.environ["DATABASE_URL"]`. Si la variable no está definida, la app no arranca y lanza `RuntimeError`. No existe valor por defecto con SQLite.

### Tabla `predictions`

Los tipos usan nomenclatura PostgreSQL. SQLAlchemy mapea automáticamente desde los tipos Python/SQLAlchemy.

| Columna                   | Tipo PG          | Restricciones                      |
|---------------------------|------------------|------------------------------------|
| `id`                      | SERIAL           | PRIMARY KEY                        |
| `year_founded`            | INTEGER          | NOT NULL                           |
| `funding_usd`             | DOUBLE PRECISION | NOT NULL                           |
| `company_age`             | INTEGER          | NOT NULL                           |
| `industry`                | VARCHAR(100)     | NOT NULL                           |
| `country`                 | VARCHAR(100)     | NOT NULL                           |
| `continent`               | VARCHAR(50)      | NOT NULL                           |
| `predicted_valuation_usd` | DOUBLE PRECISION | NOT NULL                           |
| `predicted_multiple`      | DOUBLE PRECISION | NOT NULL — `valuation_pred / funding_usd` |
| `actual_valuation_usd`    | DOUBLE PRECISION | NULLABLE (feedback)                |
| `actual_multiple`         | DOUBLE PRECISION | NULLABLE — calculado por `PUT /predictions/{id}` |
| `comment`                 | TEXT             | NULLABLE                           |
| `model_version`           | VARCHAR(50)      | NOT NULL DEFAULT `'prod'` — `'prod'` o `'candidate'` |
| `created_at`              | TIMESTAMPTZ      | DEFAULT NOW()                      |

> **Nota de migración:** las columnas `predicted_multiple`, `actual_multiple` y `model_version` son nuevas en Fase 7. El ticket `[T-7.1]` actualiza el ORM SQLAlchemy y ejecuta `Base.metadata.create_all(engine)` que añade las columnas en PostgreSQL vía `ALTER TABLE` implícito (o migración manual si la tabla ya existe en producción).

---

## 6. Dependencias Python Canónicas

`backend/requirements.txt` debe contener exactamente:

```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
joblib>=1.4.0
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.5.0
PyYAML>=6.0
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
matplotlib>=3.9.0
seaborn>=0.13.0
optuna>=3.6.0
scipy>=1.13.0
pytest>=8.0.0
httpx>=0.27.0
pyarrow>=14.0.0
```

> `streamlit` y `kagglehub` son eliminados. `httpx` es necesario para los tests de la API con `TestClient`. `psycopg2-binary` es el driver PostgreSQL para SQLAlchemy. `pyarrow` es obligatorio para leer/escribir `backend/data/processed/dataset.parquet` con pandas. `scipy` es requerido por `backend/src/mlops/drift.py` para el test KS (`scipy.stats.ks_2samp`). No se requiere ningún driver SQLite adicional porque SQLite queda fuera del stack de producción.

---

## 7. Stack Tecnológico Final

| Capa         | Tecnología         | Notas                                    |
|--------------|--------------------|------------------------------------------|
| ML / Training    | scikit-learn           | Pipeline + ColumnTransformer                        |
| Serialización    | joblib                 | `best_model.joblib`, `candidate_model.joblib`       |
| Hiperparámetros  | optuna>=3.6.0          | K-Fold + TPE en `src/mlops/tuning.py`               |
| Data Drift       | scipy>=1.13.0          | Test KS en `src/mlops/drift.py`                     |
| Backend API      | FastAPI + Pydantic     | Sin Streamlit; BackgroundTasks para retrain          |
| Servidor         | uvicorn                | `uvicorn app.main:app --reload` (cwd: `backend/`)   |
| Frontend         | React (Vite)           | SPA con Panel MLOps; consume `/predictions`, `/retrain` |
| Base de datos    | PostgreSQL 15 + SQLAlchemy | Servicio `db` en Docker; `DATABASE_URL` en entorno |
| CI               | GitHub Actions         | Gate de R² + pytest (cwd: `backend/`)              |
| Contenedores     | Docker Compose         | Servicios `api` (build: `./backend`), `frontend` y `db` |

---

## 8. Contrato de Interfaz Frontend

La interfaz React debe estar alineada con el contrato de la API, pero no está obligada a mostrar los nombres técnicos al usuario final.

### Reglas de idioma y terminología

- Todo texto visible de la aplicación debe estar en español.
- Usar tildes, `ñ` y signos correctos: `Predicción`, `Métricas`, `Valoración`, `Señal`, `Compañía`, `Metodología`, `Oráculo`.
- Evitar mezclar inglés y español en textos visibles. Términos como `Dashboard`, `Feedback` o `Funding` deben mostrarse como `Panel`, `Retroalimentación` y `Financiación`, salvo que formen parte de código, endpoints o nombres técnicos internos.
- No mostrar textos desactualizados del stack eliminado (`mock_model`, SQLite, Streamlit).

### Separación entre valor técnico y etiqueta visible

Los payloads enviados a FastAPI mantienen los nombres canónicos del contrato:

```json
{
  "year_founded": 2015,
  "funding_usd": 50000000.0,
  "company_age": 9,
  "industry": "Fintech",
  "country": "United States",
  "continent": "North America"
}
```

La UI puede traducir etiquetas sin alterar el valor enviado. Ejemplo obligatorio para `continent`:

| Valor enviado al backend | Etiqueta visible en frontend |
|--------------------------|------------------------------|
| `North America`          | `América del Norte`          |
| `South America`          | `América del Sur`            |
| `Europe`                 | `Europa`                     |
| `Africa`                 | `África`                     |
| `Oceania`                | `Oceanía`                    |

En la interfaz, el campo debe mostrarse como **Región geográfica**, no como "continente", para evitar el error conceptual de presentar América del Norte y América del Sur como continentes separados.

---

### Nueva pestaña: Panel MLOps (Fase 7)

La interfaz React añade una pestaña dedicada "Panel MLOps" con dos componentes principales:

**8.1 Tabla interactiva de predicciones (consume `GET /predictions`):**

| Columna visible (ES) | Campo backend | Editable |
|---|---|---|
| ID | `id` | No |
| Año fundación | `year_founded` | No |
| Financiación (M$) | `funding_usd` | No |
| Industria | `industry` | No |
| País | `country` | No |
| Valoración predicha | `predicted_valuation_usd` | No |
| Múltiplo predicho | `predicted_multiple` | No |
| Valoración real (M$) | `actual_valuation_usd` | **Sí** — llama `PUT /predictions/{id}` |
| Comentario | `comment` | **Sí** — llama `PUT /predictions/{id}` |
| Versión del modelo | `model_version` | No |
| Fecha | `created_at` | No |

- El usuario puede editar directamente las columnas "Valoración real" y "Comentario" en la tabla.
- Al confirmar la edición, el frontend llama `PUT /predictions/{id}` con `{ actual_valuation_usd, comment }`.
- La tabla muestra paginación y estado de carga/error.

**8.2 Panel de control MLOps:**

- **Botón "Reentrenar modelo":** llama `POST /retrain`. Muestra estado `"reentrenando..."` durante el proceso y notifica al completar.
- **Sección "Estado del Data Drift":** consume `GET /metrics` (que incluirá un campo `drift_report_path`) y muestra si hay drift detectado por feature, con indicadores visuales.
- **Sección "Métricas A/B Testing":** calcula en el cliente (desde `GET /predictions`) el MAE medio por `model_version` y muestra la comparativa producción vs candidato.
- **Sección "Métricas del Modelo Actual":** muestra `r2_mean`, `r2_std`, `overfitting_gap`, `optuna_trials` y `best_params` del `metrics.json`.

> **Regla de idioma:** todas las etiquetas visibles en el Panel MLOps siguen las mismas reglas de español de la sección §8 principal.

---

## 9. Codificación

Todos los archivos `.py`, `.md`, `.yaml`, `.json`, `.jsx` usan **UTF-8 sin BOM**. Cualquier cadena con mojibake (`PredicciÃ³n`, `RÂ²`) debe ser corregida a su forma correcta (`Predicción`, `R²`).
