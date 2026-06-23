# Spec — Single Source of Truth

> Este documento es el contrato técnico del proyecto. Cualquier archivo de código, configuración o test que contradiga lo aquí escrito debe ser corregido.

---

## 1. Esquema de Columnas Definitivo

### Dataset Crudo de Entrada

Archivo fuente: `data/raw/unicorn_companies.csv`

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

### Variable Objetivo (y)

| Nombre Columna | Dtype | Derivación                                      |
|----------------|-------|-------------------------------------------------|
| `valuation_usd`| float | Parseo de `Valuation ($B)` → dólares (×1e9)    |

> **Prohibido:** usar `Valuation`, `Funding`, `Valuation ($B)`, `Investors`, `investor_count`, `join_year`, `join_month` como features del modelo en producción. Pueden existir sólo en notebooks históricos.

---

## 2. Rutas Canónicas de Artefactos

Toda referencia a archivos en `config.yaml`, `app/`, `src/`, `scripts/` y `tests/` debe apuntar a estas rutas. Sin excepciones.

| Artefacto                | Ruta Canónica                      | Notas                                                  |
|--------------------------|------------------------------------|--------------------------------------------------------|
| Dataset crudo            | `data/raw/unicorn_companies.csv`   | Nunca en `notebooks/data/`                             |
| Dataset procesado        | `data/processed/dataset.parquet`   | Formato parquet (eficiente, tipado)                    |
| Modelo serializado       | `models/best_model.joblib`         | Única ruta válida; `unicorn_valuation_pipeline.joblib` y `current_model.pkl` quedan eliminados |
| Métricas del modelo      | `models/metrics.json`              | Generado por `scripts/train.py`                        |
| Base de datos            | Servicio PostgreSQL (`db`)         | Sin archivo local. Conexión vía `DATABASE_URL`. Ambas SQLite (`storage/app.db`, `data/feedback/predictions.sqlite3`) eliminadas. |
| Reportes EDA             | `reports/`                         | Generados, nunca versionados en Git                    |

---

## 3. Umbral de Calidad del Modelo

```yaml
# config.yaml — sección training
training:
  min_r2: 0.50
```

### Regla de CI

- El script `scripts/train.py` finaliza con `sys.exit(1)` si `validation.r2 < 0.50`.
- El test `tests/test_pipeline.py` afirma `r2 >= 0.50` (no `>= 0.15`).
- Ningún PR a `main` puede fusionarse si CI falla por este motivo.

> **Diagnóstico actual:** `metrics.json` reporta R²=0.176. Esto significa que el modelo actual no pasaría CI. La refactorización del pipeline de features (unificar esquema, añadir ingeniería de features correcta) es la acción correctiva. El umbral NO se baja para acomodar un modelo deficiente.

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

**Response 200:** contenido completo de `models/metrics.json`

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

> `app/database.py` lee `os.environ["DATABASE_URL"]`. Si la variable no está definida, la app no arranca y lanza `RuntimeError`. No existe valor por defecto con SQLite.

### Tabla `predictions`

Los tipos usan nomenclatura PostgreSQL. SQLAlchemy mapea automáticamente desde los tipos Python/SQLAlchemy.

| Columna                   | Tipo PG       | Restricciones              |
|---------------------------|---------------|----------------------------|
| `id`                      | SERIAL        | PRIMARY KEY                |
| `year_founded`            | INTEGER       | NOT NULL                   |
| `funding_usd`             | DOUBLE PRECISION | NOT NULL               |
| `company_age`             | INTEGER       | NOT NULL                   |
| `industry`                | VARCHAR(100)  | NOT NULL                   |
| `country`                 | VARCHAR(100)  | NOT NULL                   |
| `continent`               | VARCHAR(50)   | NOT NULL                   |
| `predicted_valuation_usd` | DOUBLE PRECISION | NOT NULL               |
| `actual_valuation_usd`    | DOUBLE PRECISION | NULLABLE (feedback)    |
| `comment`                 | TEXT          | NULLABLE                   |
| `created_at`              | TIMESTAMPTZ   | DEFAULT NOW()              |

---

## 6. Dependencias Python Canónicas

`requirements.txt` debe contener exactamente:

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
pytest>=8.0.0
httpx>=0.27.0
```

> `streamlit` y `kagglehub` son eliminados. `httpx` es necesario para los tests de la API con `TestClient`. `psycopg2-binary` es el driver PostgreSQL para SQLAlchemy; no se requiere ningún driver SQLite adicional porque SQLite queda fuera del stack de producción.

---

## 7. Stack Tecnológico Final

| Capa         | Tecnología         | Notas                                    |
|--------------|--------------------|------------------------------------------|
| ML / Training| scikit-learn       | Pipeline + ColumnTransformer             |
| Serialización| joblib             | `best_model.joblib`                      |
| Hiperparámetros | optuna          | Usado en `src/mlops/tuning.py`           |
| Backend API  | FastAPI + Pydantic | Sin Streamlit                            |
| Servidor     | uvicorn            | `uvicorn app.main:app --reload`          |
| Frontend     | React (Vite)       | SPA en `frontend/`, consume `/predict`   |
| Base de datos| PostgreSQL 15 + SQLAlchemy | Servicio `db` en Docker; `DATABASE_URL` en entorno |
| CI           | GitHub Actions     | Gate de R² + pytest                      |
| Contenedores | Docker Compose     | Servicios `api`, `frontend` y `db`       |

---

## 8. Codificación

Todos los archivos `.py`, `.md`, `.yaml`, `.json`, `.jsx` usan **UTF-8 sin BOM**. Cualquier cadena con mojibake (`PredicciÃ³n`, `RÂ²`) debe ser corregida a su forma correcta (`Predicción`, `R²`).
