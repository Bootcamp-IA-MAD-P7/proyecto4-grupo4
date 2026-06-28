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

### Variable Objetivo (y)

| Nombre Columna | Dtype | Derivación                                      |
|----------------|-------|-------------------------------------------------|
| `valuation_usd`| float | Parseo de `Valuation ($B)` → dólares (×1e9)    |

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

> **Estado actual del modelo (post Fase 4):** El modelo GradientBoosting con schema definitivo alcanza R²≈0.18–0.22 en validación. El umbral de 0.50 no se ha alcanzado; `test_train_meets_min_r2` falla en CI de forma esperada y documentada.
>
> **Deuda técnica diferida a Fase 7:** La optimización del R² se resuelve en Fase 7 con el múltiplo de valoración (ver sección 3.1). El umbral de CI (0.50) **no se baja**; permanece como gate bloqueante hasta que `[T-7.1]`–`[T-7.5]` se implementen.
>
> **Runtime Docker MVP:** `backend/Dockerfile` genera el artefacto con `python scripts/train.py --report --allow-low-r2-artifact`. Esta bandera solo permite guardar el modelo T1-T3 dentro de la imagen Docker; el comportamiento por defecto de `scripts/train.py` mantiene el gate bloqueante.

---

### 3.1 Fase 7 — Estrategia del Múltiplo de Valoración (ADR-001)

> **Referencia completa:** `backend/docs/architecture_decision_target.md` (ADR-001, 2026-06-25)

#### Diagnóstico del modelo actual (bloqueante del R² ≥ 0.50)

El modelo T1-T3 presenta un **patrón sistemático de heterocedasticidad** diagnosticado en el stress test post-Fase 4:

| Métrica diagnóstica | Valor |
|---|---|
| R² validación | 0.18–0.22 |
| R² cross-validation 5-fold | 0.24 ± 0.10 |
| Pendiente del Residual Plot | **+1.51 B USD / B USD predicho** |
| Ratio de heterocedasticidad | **5.05×** |

El residuo medio no es cero condicional a la predicción — viola el supuesto de insesgadez del estimador. La causa estructural es doble:

1. **Piso unicornio:** el 70–75% del dataset se concentra en $1B–$3B. El modelo aprende a predecir el centroide y generaliza mal fuera de esa banda.
2. **Heterocedasticidad escalar:** la varianza del error crece proporcionalmente a la magnitud de la valoración. La función de pérdida ECM trata ambos extremos de forma simétrica, sesga el aprendizaje hacia la cola baja.

#### Solución: target múltiplo de valoración

En lugar de predecir `valuation_usd` (absoluto), el modelo predecirá el **múltiplo de valoración sobre el funding**:

```
multiple = valuation_usd / funding_usd
```

Este ratio es la métrica estándar de "funding multiple" en capital riesgo. Al dividir por `funding_usd` se elimina la mayor fuente de varianza condicional (la escala del negocio), normalizando la heterocedasticidad estructural.

**Propiedades esperadas del nuevo target (`log1p(multiple)`):**

| Propiedad | `log1p(valuation_usd)` actual | `log1p(multiple)` objetivo |
|---|---|---|
| Distribución | Sesgada derecha, pico en $1B | Más simétrica, normalizable |
| Correlación con features | Moderada (R²≈0.22) | Superior (esperado 0.35–0.50) |
| Heterocedasticidad | Alta (5×) | Reducida (funding absorbe escala) |
| Penaliza escala absol. | Sí (sesgante) | No (el ratio es adimensional) |

**Criterios de aceptación de Fase 7:**
- R² validación ≥ 0.35 (objetivo) / ≥ 0.50 (gate CI)
- Pendiente del Residual Plot < ±0.5 B/B (reducción ≥ 66% del sesgo actual de +1.51)
- Eliminación del sesgo de compresión en el piso $1B–$3B

#### Flujo de inferencia con el nuevo target (API transparente)

El cambio es **completamente interno** al pipeline de ML. El contrato de `POST /predict` no cambia:

```
Input:  { funding_usd: 50_000_000, ... }
           ↓
        Pipeline ML predice: multiple_pred = expm1(model.predict(features))
           ↓
        Conversión interna: valuation_usd_pred = multiple_pred × funding_usd
           ↓
Output: { valuation_usd: 1_250_000_000.0, valuation_b: 1.25, ... }
```

El frontend, los tests de contrato y cualquier integración externa **no requieren ningún cambio** al implementar `[T-7.1]`–`[T-7.5]`.

#### Archivos modificados en Fase 7 (confinados al backend ML)

| Ticket | Archivo | Cambio |
|---|---|---|
| `[T-7.2]` | `backend/config.yaml` | Nueva clave `target_transform: multiple` |
| `[T-7.3]` | `backend/src/models/train.py` | `fit_model()` usa `log1p(multiple)`; `predict_absolute()` reconvierte por `funding_usd` |
| `[T-7.4]` | `backend/app/model_service.py` | `predict_valuation()` pasa `funding_usd` para reconversión post-inferencia |
| `[T-7.5]` | `backend/scripts/train.py` | `enforce_quality_gate()` ajustado al umbral R² del múltiplo |
| `[T-7.6]` | `backend/tests/test_pipeline.py` | `test_train_meets_min_r2` actualizado al baseline del múltiplo |

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
pytest>=8.0.0
httpx>=0.27.0
pyarrow>=14.0.0
```

> `streamlit` y `kagglehub` son eliminados. `httpx` es necesario para los tests de la API con `TestClient`. `psycopg2-binary` es el driver PostgreSQL para SQLAlchemy. `pyarrow` es obligatorio para leer/escribir `backend/data/processed/dataset.parquet` con pandas. No se requiere ningún driver SQLite adicional porque SQLite queda fuera del stack de producción.

---

## 7. Stack Tecnológico Final

| Capa         | Tecnología         | Notas                                    |
|--------------|--------------------|------------------------------------------|
| ML / Training| scikit-learn       | Pipeline + ColumnTransformer             |
| Serialización| joblib             | `best_model.joblib`                      |
| Hiperparámetros | optuna          | Usado en `src/mlops/tuning.py`           |
| Backend API  | FastAPI + Pydantic | Sin Streamlit                            |
| Servidor     | uvicorn            | `uvicorn app.main:app --reload` (cwd: `backend/`) |
| Frontend     | React (Vite)       | SPA en `frontend/`, consume `/predict`   |
| Base de datos| PostgreSQL 15 + SQLAlchemy | Servicio `db` en Docker; `DATABASE_URL` en entorno |
| CI           | GitHub Actions     | Gate de R² + pytest (cwd: `backend/`)    |
| Contenedores | Docker Compose     | Servicios `api` (build: `./backend`), `frontend` y `db` |

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

## 9. Codificación

Todos los archivos `.py`, `.md`, `.yaml`, `.json`, `.jsx` usan **UTF-8 sin BOM**. Cualquier cadena con mojibake (`PredicciÃ³n`, `RÂ²`) debe ser corregida a su forma correcta (`Predicción`, `R²`).
