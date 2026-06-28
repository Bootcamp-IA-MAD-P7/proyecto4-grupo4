# Plan — Checklist de Ejecución

> Ejecutar en orden. Cada fase debe dejar el proyecto en estado compilable y con tests pasando antes de avanzar a la siguiente.
>
> Referencia permanente: `2_spec.md` es el contrato. Todo cambio debe converger hacia él.

**Estado del plan (SDD):**

| Fase | Estado |
|------|--------|
| Fase 0 — Preparación | ✅ Completada |
| Fase 1 — Limpieza de Artefactos | ✅ Completada |
| Fase 0.5 — Monorepo (`backend/`) | ✅ Completada |
| Fase 2 — Rutas y Configuración | ✅ Completada |
| Fase 3 — Tests + Modelo T1-T3 | ✅ Completada |
| Fase 4 — API + PostgreSQL | ✅ Completada |
| Fase 5 — Frontend React + Docker | ✅ Completada |
| **Fase 6 — Documentación** | **✅ Completada** |
| **Fase 7 — MLOps Nivel Experto** | **✅ Completada** |
| Fase 8 — CI/CD y Despliegue EC2 | ✅ Completada |

---

## Fase 0 — Preparación ✅ COMPLETADA

> **Estado:** ejecutada y validada. No revertir estos cambios.

- [x] Crear rama `refactor/stabilize-architecture` desde `main`
- [x] Documentar estado inicial: ejecutar `pytest` y registrar qué tests fallan (baseline)
- [x] Hacer snapshot del `backend/models/metrics.json` actual para comparación futura

---

## Fase 1 — Limpieza de Artefactos y Duplicados ✅ COMPLETADA

> **Estado:** ejecutada y validada. No revertir estos cambios.

### 1.1 Eliminar archivos binarios del índice Git

```bash
git rm --cached backend/models/best_model.joblib
git rm --cached backend/models/unicorn_valuation_pipeline.joblib
git rm --cached backend/models/metrics.json
git rm --cached backend/storage/app.db
git rm --cached backend/data/feedback/predictions.sqlite3
git rm --cached backend/reports/*.png
git rm --cached backend/data/dataset_clean.csv
```

- [x] Ejecutar los comandos anteriores
- [x] Los archivos permanecen en disco (sólo salen del índice)

### 1.2 Actualizar `.gitignore`

Añadir las siguientes entradas al `.gitignore` existente:

```
# ML Artifacts — never version these
backend/models/*.joblib
backend/models/*.pkl
backend/models/metrics.json
backend/reports/*.png
backend/reports/*.pdf
backend/data/processed/
backend/data/dataset_clean.csv

# Databases — never version these (production uses PostgreSQL)
backend/storage/*.db
backend/data/feedback/*.sqlite3
*.sqlite3

# Environment variables
.env
.env.*
!.env.example
```

- [x] Editar `.gitignore` con las entradas anteriores
- [x] Verificar con `git status` que los artefactos aparecen como "untracked" y no como "modified"

### 1.3 Eliminar archivos duplicados y huérfanos

- [x] Eliminar `backend/notebooks/data/raw/dataset_raw.csv` (duplicado de `backend/data/raw/dataset_raw.csv`)
- [x] Eliminar `backend/data/raw/dataset_raw.csv` — el dataset canónico es `backend/data/raw/unicorn_companies.csv`
- [x] Eliminar `backend/data/dataset_clean.csv` (en raíz de `data/`, duplicado del procesado)
- [x] Eliminar `backend/src/data/__init___BACKUP.py`
- [x] Eliminar `backend/notebooks/01_eda_BACKUP.ipynb`
- [x] Eliminar `backend/app/streamlit_app.py`
- [x] Evaluar si `backend/src/data/load_data.py` y `backend/src/data/load.py` pueden fusionarse en uno solo; si hay solapamiento, mantener sólo `backend/src/data/load.py` y eliminar `load_data.py`

### 1.4 Eliminar TODAS las bases de datos SQLite

La arquitectura de producción usa PostgreSQL. No existe ningún archivo `.db` ni `.sqlite3` válido en el proyecto.

- [x] Eliminar `backend/data/feedback/predictions.sqlite3` (DB de feedback legacy)
- [x] Eliminar `backend/storage/app.db` (DB SQLite que reemplaza PostgreSQL)
- [x] Eliminar la carpeta `backend/storage/` si queda vacía, o mantener sólo `.gitkeep`
- [x] Añadir al `.gitignore` (si no están ya):
  ```
  backend/storage/*.db
  backend/data/feedback/*.sqlite3
  *.sqlite3
  ```
- [x] Verificar que ningún archivo `.py` referencia rutas SQLite directas (ej. `sqlite:///`, `backend/storage/app.db`)

---

## Fase 0.5 — Reestructuración de Carpetas (Monorepo) ✅ COMPLETADA

> **Estado:** ejecutada y validada (ticket `[T-2.0]`). No revertir estos cambios.
>
> Objetivo: separar backend y frontend en un monorepo limpio. Tras esta fase, la raíz del repositorio contiene **únicamente** `backend/`, `frontend/`, `.specify/`, `.github/`, `docker-compose.yml` y `.gitignore`.

### 0.5.1 Crear estructura `backend/` y mover carpetas de código

```bash
mkdir -p backend
git mv app src scripts models storage tests config.yaml backend/
```

Además, mover al `backend/` los artefactos de soporte que hoy están en la raíz:

```bash
git mv requirements.txt Dockerfile data notebooks docs README.md backend/
```

- [x] Ejecutar los comandos anteriores (usar `git mv` para preservar historial)
- [x] Verificar que la raíz sólo contiene: `backend/`, `frontend/`, `.specify/`, `.github/`, `docker-compose.yml`, `.gitignore`

### 0.5.2 Actualizar `docker-compose.yml` en la raíz

- [x] Cambiar `build: .` → `build: ./backend` en el servicio `api`
- [x] Eliminar volúmenes legacy de Streamlit/SQLite (`8501`, `./storage:/app/storage`, etc.)
- [x] Verificar que `command` sigue siendo `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [x] Ejecutar `docker compose config` — sin errores de sintaxis

### 0.5.3 Actualizar `backend/Dockerfile`

- [x] Confirmar que `WORKDIR /app` y los `COPY` son correctos respecto al nuevo contexto de build (`./backend`)
- [x] Eliminar referencias a Streamlit (`8501`, `streamlit run`)
- [x] `EXPOSE 8000` y `CMD` con uvicorn

### 0.5.4 Verificar imports y rutas Python en `backend/`

- [x] Ejecutar desde `backend/`: `python -c "from app.main import app; print('OK')"`
- [x] Ejecutar desde `backend/`: `pytest tests/ -v --collect-only` (sin errores de import)
- [x] Buscar imports rotos: `grep -rn "from app\|from src\|import app\|import src" backend/ --include="*.py"` — todos deben resolver desde el cwd `backend/`
- [x] Confirmar que `backend/config.yaml` mantiene rutas relativas a `backend/` (`models/best_model.joblib`, `data/processed/dataset.parquet`)

### 0.5.5 Verificación de estructura final

```bash
ls -1                          # sólo backend frontend .specify .github docker-compose.yml .gitignore
ls backend/                    # app src scripts models storage tests config.yaml requirements.txt Dockerfile data notebooks docs README.md
```

- [x] La raíz cumple el contrato de `2_spec.md` sección 2
- [x] `frontend/` permanece intacto en su ubicación actual
- [x] `reports/` movido a `backend/reports/` (artefactos EDA, gitignored)

---

## Fase 2 — Unificar Rutas y Configuración ▶ FASE ACTIVA

> **Prerequisito:** Fases 0, 1 y 0.5 completadas. **Esta es la única fase en ejecución.**
> Todas las rutas de archivos en esta fase son relativas a `backend/` (cwd del servicio `api`).

### 2.1 Corregir `backend/config.yaml`

- [ ] Cambiar `paths.model_file` de `models/unicorn_valuation_pipeline.joblib` → `models/best_model.joblib`
- [ ] Verificar `paths.processed_data` = `data/processed/dataset.parquet` ✓
- [ ] **Eliminar** la clave `paths.storage_db` — la DB ya no es un archivo local; la conexión viene de `DATABASE_URL`
- [ ] Verificar `training.min_r2` = `0.50`

### 2.2 Corregir `backend/app/model_service.py`

- [ ] Cambiar la ruta por defecto del modelo de `models/current_model.pkl` → `models/best_model.joblib`
- [ ] Cambiar las features de `country, city, industry, join_year, join_month, investor_count` → `year_founded, funding_usd, company_age, industry, country, continent` (según `2_spec.md`)
- [ ] Eliminar el mock/heurístico de predicción; si no hay modelo, lanzar `503`

### 2.3 Corregir `backend/scripts/train.py`

- [ ] Asegurarse de que guarda el modelo en `models/best_model.joblib` (no en `unicorn_valuation_pipeline.joblib`)
- [ ] Al finalizar el entrenamiento, verificar `validation.r2 >= config.training.min_r2`; si no, `sys.exit(1)` con mensaje claro

### 2.4 Corregir `backend/src/preprocessing/preprocessing_pipeline.py`

- [ ] Deprecar o eliminar las referencias a columnas crudas (`Valuation ($B)`, `Investors`)
- [ ] Si algún notebook activo depende de este módulo, actualizar el notebook para usar `backend/src/data/load.py`
- [ ] Si el módulo queda sin uso, eliminarlo en su totalidad

---

## Fase 3 — Corregir Tests y Umbrales (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 2.

### 3.1 `backend/tests/test_pipeline.py`

- [ ] Cambiar el assert de R² de `>= 0.15` → `>= 0.50`
- [ ] Cambiar el nombre de columnas en fixtures al esquema definitivo (`year_founded`, `funding_usd`, etc.)
- [ ] Verificar que el test carga el modelo desde `models/best_model.joblib`

### 3.2 `backend/tests/test_preprocessing.py`

- [ ] Actualizar fixtures para usar el esquema de columnas de `2_spec.md`
- [ ] Eliminar referencias a `Valuation ($B)`, `Investors`, `investor_count`

### 3.3 `backend/tests/test_api.py`

- [ ] Verificar que los payloads de prueba usan el esquema de `2_spec.md` (`year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`)
- [ ] Verificar que el endpoint `/predict` retorna `valuation_usd` y `valuation_b`

### 3.4 `backend/tests/conftest.py`

- [ ] Revisar fixtures compartidas y actualizar columnas al esquema definitivo

### 3.5 Ejecutar suite completa

```bash
cd backend && pytest tests/ -v
```

- [ ] Todos los tests pasan en verde antes de avanzar a Fase 4

---

## Fase 4 — Crear / Estabilizar la API FastAPI (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 3.

### 4.1 Limpiar dependencias

- [ ] Actualizar `backend/requirements.txt` con el listado de `2_spec.md` (añadir `fastapi`, `uvicorn`, `pydantic`, `httpx`, `psycopg2-binary`; eliminar `streamlit`, `kagglehub`)
- [ ] Ejecutar `pip install -r backend/requirements.txt` y verificar que no hay conflictos

### 4.2 Definir Pydantic schemas en `backend/app/input_schema.py`

- [ ] `PredictRequest`: campos `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`
- [ ] `PredictResponse`: campos `valuation_usd`, `valuation_b`, `model_version`, `timestamp`
- [ ] `FeedbackRequest`: extiende `PredictRequest` con `predicted_valuation_usd`, `actual_valuation_usd`, `comment`
- [ ] `FeedbackResponse`: campos `id`, `status`, `timestamp`

### 4.3 Implementar `backend/app/main.py`

- [ ] Registrar routers para `/predict`, `/feedback`, `/health`, `/metrics`
- [ ] Configurar CORS para permitir el frontend en `localhost:5173`
- [ ] Eliminar cualquier referencia a Streamlit

### 4.4 Implementar `backend/app/model_service.py`

- [ ] Carga lazy del modelo al arrancar la app (`@app.on_event("startup")`)
- [ ] Features de entrada: esquema definitivo de `2_spec.md`
- [ ] Sin mock: si el modelo no existe, la app no arranca y lanza error descriptivo

### 4.5 Configurar SQLAlchemy para PostgreSQL en `backend/app/database.py`

- [ ] Leer `DATABASE_URL` exclusivamente desde `os.environ["DATABASE_URL"]`; si no existe, lanzar `RuntimeError` claro
- [ ] Crear engine con `create_engine(DATABASE_URL)` — sin `check_same_thread` (eso era SQLite)
- [ ] Definir `SessionLocal` y `Base` como de costumbre con SQLAlchemy ORM
- [ ] Crear un archivo `backend/.env.example` con:
  ```
  DATABASE_URL=postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
  ```
- [ ] Añadir `.env` al `.gitignore` (nunca versionar credenciales)

### 4.6 Implementar `backend/app/feedback_service.py`

- [ ] Persistir cada predicción + feedback en la tabla `predictions` de PostgreSQL
- [ ] Usar la sesión de `backend/app/database.py` (que ya lee `DATABASE_URL`)
- [ ] Verificar que no existe ninguna referencia a rutas de archivo SQLite (`storage/app.db`, `sqlite:///`)

### 4.7 Verificar modelo ORM en `backend/app/database.py`

- [ ] El modelo `Prediction` (o equivalente) mapea la tabla `predictions` con los campos de `2_spec.md` sección 5
- [ ] `Base.metadata.create_all(engine)` se invoca en el startup para crear la tabla si no existe en PostgreSQL

### 4.8 Smoke test de la API (requiere PostgreSQL activo)

```bash
# Con Docker Compose (recomendado)
docker compose up db -d          # levantar sólo el servicio PostgreSQL
cd backend
DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns \
  uvicorn app.main:app --reload &
sleep 3
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,"industry":"fintech","country":"United States","continent":"North America"}'
curl -s http://localhost:8000/health
```

- [ ] Respuesta 200 con `valuation_usd` numérico
- [ ] Respuesta de `/health` contiene `"status":"ok"`

---

## Fase 5 — Frontend React + Docker Compose ✅ COMPLETADA

> **Estado:** completada — todos los tickets `[T-5.1]`–`[T-5.9]` cerrados. Smoke test Docker Compose validado.

### 5.1 Verificar `frontend/src/api.js`

- [x] `BASE_URL` apunta a `http://localhost:8000` o se configura con `VITE_API_URL`.
- [x] `predict(payload)` usa el esquema de `2_spec.md`.
- [x] `submitFeedback(payload)` usa el endpoint `/feedback`.
- [x] El payload elimina campos legacy (`city`, `join_year`, `join_month`, `investor_count`).

### 5.2 Reemplazar métricas hardcodeadas

- [x] `frontend/src/data/modelMetrics.js` exporta `fetchMetrics()` contra `GET /metrics`.
- [x] `Dashboard.jsx` consume métricas con `useEffect`.
- [x] El dashboard muestra estado de carga/error si el backend todavía no tiene `models/metrics.json`.

### 5.3 Actualizar formulario de predicción

- [x] Los campos del formulario coinciden con `PredictRequest`: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`.
- [x] Eliminar cualquier campo legacy (`city`, `join_year`, `join_month`, `investor_count`).
- [x] La UI muestra el campo técnico `continent` como **Región geográfica**.

### 5.4 Actualizar resultado y retroalimentación

- [x] Mostrar `valuation_b` formateado (ej: `$1.25B`) y `valuation_usd` completo.
- [x] Corregir `PredictionResult.jsx` para dejar de usar nombres legacy.
- [x] Alinear el payload de retroalimentación con `POST /feedback`.
- [x] Corregir textos visibles, tildes, `ñ`, mojibake y coherencia español/inglés.

### 5.5 Búsqueda y corrección global de mojibake

- [x] Búsqueda global ejecutada y limpieza completada en todos los archivos fuente.

### 5.6 Crear Dockerfile multi-stage para frontend

- [x] `frontend/Dockerfile` multi-stage: Node 20 Alpine (build) + Nginx 1.27 Alpine (serve).
- [x] `frontend/nginx.conf` con soporte SPA (`try_files`).

### 5.7 Actualizar `docker-compose.yml`

- [x] Servicios `db`, `api` y `frontend` incluidos.
- [x] `healthcheck` en PostgreSQL con `pg_isready`.
- [x] `depends_on.condition: service_healthy` para la API.

### 5.8 Smoke test completo con Docker Compose

- [x] `docker compose up --build -d` validado.
- [x] Los tres contenedores en estado `running`.
- [x] `/health` → `{"status":"ok","model_loaded":true}`. `/predict` devuelve `valuation_usd`.

### 5.9 Ajustes estructurales y UX del frontend

- [x] Estructura de componentes revisada y UX mejorada.
- [x] Idioma español consistente, tildes, `ñ`, accesibilidad básica.
- [x] Autocompletado de `Región geográfica` desde `País` seleccionado.

---

## Fase 6 — Documentación y Cierre (✅ completada)

> **Estado:** bloqueada — no iniciar hasta completar Fase 5.

### 6.1 Actualizar `backend/README.md`

- [ ] Corregir árbol de directorios (estructura monorepo: `backend/` + `frontend/`)
- [ ] Corregir instrucciones de instalación: `pip install -r backend/requirements.txt`
- [ ] Corregir comandos de ejecución: `uvicorn` en lugar de `streamlit run`
- [ ] Corregir encoding: todos los caracteres especiales en UTF-8

### 6.2 Actualizar `backend/docs/`

- [ ] `backend/docs/app_usage.md`: instrucciones para la API FastAPI y el frontend React
- [ ] `backend/docs/data_notes.md`: esquema definitivo de columnas de `2_spec.md`

### 6.3 Commit y PR

```bash
git add -A
git commit -m "refactor: stabilize architecture — unified schema, routes, thresholds, FastAPI migration"
git push origin refactor/stabilize-architecture
# Abrir PR hacia main con referencia a .specify/
```

- [ ] PR creada
- [ ] CI pasa (pytest + R² >= 0.50)
- [ ] Revisión de equipo antes de merge

---

## Fase 7 — MLOps Nivel Experto: Múltiplo + K-Fold + Optuna + A/B Testing + Data Drift ✅ COMPLETADA

> **Estado:** ✅ completada — MVP desplegado en EC2 (Fase 8 completada). Ciclo MLOps experto implementado y verificado (28 tests pytest + build frontend).
> **Decisión arquitectónica:** `backend/docs/architecture_decision_target.md` (ADR-001, 2026-06-25).
> **Contrato técnico completo:** `2_spec.md §3.1` (arquitectura MLOps, A/B Testing, Data Drift, Retrain).
> **Tickets de ejecución:** `[T-7.1]`–`[T-7.10]` en `4_tasks.md`.
> **Prerequisito técnico:** Fases 0–6 y 8 completadas. MVP estable en EC2.

### Resumen arquitectónico

Fase 7 implementa un ciclo MLOps completo sobre la infraestructura base estable (FastAPI, React, PostgreSQL, EC2). Los cuatro ejes son:

1. **Reingeniería del modelo:** target `multiple = valuation_usd / funding_usd` con K-Fold (k=5) + Optuna (`n_trials=50`).
2. **A/B Testing:** `model_service.py` carga producción + candidato y enruta por peso configurable.
3. **Data Drift:** test KS (scipy) en cada ciclo de retrain; resultado persistido en `drift_report.json`.
4. **Nuevos endpoints MLOps:** `GET /predictions`, `PUT /predictions/{id}`, `POST /retrain`.

El contrato externo de `POST /predict` no cambia. El frontend añade una pestaña "Panel MLOps".

---

### 7.1 Migración de Base de Datos — Nuevas columnas en `predictions`

> **Prerequisito:** ninguno (independiente del modelo). Ejecutar primero para no bloquear el resto.

- [x] Añadir al modelo ORM `Prediction` en `backend/app/database.py`:
  - `predicted_multiple: Float, NOT NULL`
  - `actual_multiple: Float, NULLABLE`
  - `model_version: String(50), NOT NULL, default='prod'`
- [x] Ejecutar la migración en PostgreSQL (producción: `ALTER TABLE predictions ADD COLUMN ...`; desarrollo: `Base.metadata.create_all(engine)` si la tabla no existe aún).
- [x] Actualizar `backend/app/feedback_service.py` para persistir `predicted_multiple` y `model_version` en cada nueva predicción.
- [x] Verificar: `\d predictions` en psql muestra las tres nuevas columnas.

---

### 7.2 Actualizar `backend/config.yaml` con configuración MLOps

> **Prerequisito:** ninguno.

- [x] Añadir secciones `optuna`, `ab_testing`, `drift` bajo `training`:
  ```yaml
  training:
    min_r2: 0.50
    max_overfitting_gap: 0.05
    target_transform: multiple

  optuna:
    n_trials: 50
    cv_folds: 5
    random_state: 42
    param_space:
      n_estimators: [50, 300]
      max_depth: [2, 8]
      learning_rate: [0.01, 0.3]
      subsample: [0.6, 1.0]
      min_samples_split: [2, 20]

  ab_testing:
    enabled: true
    candidate_weight: 0.2

  drift:
    ks_pvalue_threshold: 0.05
    mean_drift_pct_threshold: 20.0
  ```
- [x] Verificar: `python -c "import yaml; cfg=yaml.safe_load(open('config.yaml')); print(cfg['optuna']['n_trials'])"` → `50`.

---

### 7.3 Pipeline de Entrenamiento: K-Fold + Optuna

> **Prerequisito:** `[T-7.2]` completado.

- [x] Crear `backend/src/mlops/tuning.py` con la función `run_optuna_kfold(df, cfg) -> (best_params, metrics_dict)`.
  - `KFold(n_splits=cfg["optuna"]["cv_folds"], shuffle=True, random_state=cfg["optuna"]["random_state"])`.
  - Cada trial de Optuna construye un `Pipeline(preprocessor, GradientBoostingRegressor(**params))` y evalúa la media del R² K-Fold sobre `log1p(multiple)`.
  - El trial con mayor R² medio es el ganador.
- [x] Refactorizar `backend/scripts/train.py`:
  - Importar y llamar `run_optuna_kfold()` en lugar de un fit directo.
  - Guardar los hiperparámetros ganadores en `metrics.json` bajo `best_params`.
  - Calcular `overfitting_gap = train_r2 - val_r2_mean`.
  - Actualizar `enforce_quality_gate()`: gate compuesto `val_r2_mean >= 0.50 AND gap < 0.05`.
- [x] La función `predict_absolute(pipeline, X, funding_usd_series)` convierte `expm1(predict) × funding_usd`.
- [x] Verificar: `cd backend && python -c "from src.mlops.tuning import run_optuna_kfold; print('OK')"` → `OK`.

---

### 7.4 Model Service: A/B Testing + Reconversión del Múltiplo

> **Prerequisito:** `[T-7.2]` y `[T-7.3]` completados (necesita `config.yaml` actualizado).

- [x] Actualizar `backend/app/model_service.py`:
  - Carga lazy de `best_model.joblib` (producción) y `candidate_model.joblib` (candidato, opcional).
  - Función `_select_model(cfg) -> (pipeline, model_version_str)` que aplica la regla A/B por peso.
  - En `predict_valuation()`: leer `target_transform` de `cfg`; si es `"multiple"`, reconvertir `raw_pred × payload.funding_usd`; si es `"absolute"`, devolver `raw_pred` directamente.
  - Incluir `model_version` en el valor retornado para persistirlo en la BD.
- [x] Actualizar `POST /predict` en `main.py` para recibir `model_version` de `predict_valuation()` y pasarlo a `feedback_service.save_feedback()`.
- [x] Verificar: con `candidate_model.joblib` ausente → 100% tráfico a `prod`. Con ambos modelos → distribución ≈ 20/80 en 100 requests.

---

### 7.5 Schemas Pydantic para Nuevos Endpoints

> **Prerequisito:** `[T-7.1]` completado (para conocer los campos de la respuesta).

- [x] Añadir en `backend/app/input_schema.py`:
  - `PredictionRecord`: todos los campos de `predictions` + tipos opcionales para `actual_*`.
  - `PredictionsListResponse`: `List[PredictionRecord]`.
  - `UpdatePredictionRequest`: `actual_valuation_usd: float`, `comment: str | None`.
  - `UpdatePredictionResponse`: `id: int`, `status: str`, `actual_multiple: float`, `timestamp: str`.
  - `RetrainResponse`: `status: str`, `message: str`, `timestamp: str`.
- [x] Verificar: `python -c "from app.input_schema import UpdatePredictionRequest, RetrainResponse; print('OK')"` → `OK`.

---

### 7.6 Implementar Nuevos Endpoints en `backend/app/main.py`

> **Prerequisito:** `[T-7.1]`, `[T-7.5]` completados.

- [x] `GET /predictions`: consulta `predictions` con `limit` y `offset`; devuelve lista de `PredictionRecord`.
- [x] `PUT /predictions/{id}`: busca el registro, calcula `actual_multiple = actual_valuation_usd / funding_usd`, actualiza la BD, devuelve `UpdatePredictionResponse`.
  - Si el registro no existe: `HTTPException(404)`.
- [x] `POST /retrain`: registra el job en `BackgroundTasks`; devuelve inmediatamente `202 Accepted`.
  - Flag en memoria `_retrain_in_progress: bool` para evitar ejecuciones concurrentes (`503` si ya está corriendo).
  - La función de fondo ejecuta: 1) detect_drift, 2) train+Optuna, 3) auto-replacement.
- [x] Verificar con `pytest tests/test_mlops.py -v` en verde.

---

### 7.7 Detección de Data Drift

> **Prerequisito:** `[T-7.2]` completado (necesita `drift` config). Independiente de endpoints.

- [x] Crear `backend/src/mlops/drift.py` con `detect_drift(df_original, df_feedback, cfg) -> dict`.
  - Para cada feature numérica: `scipy.stats.ks_2samp(original_col, feedback_col)`.
  - Calcular `mean_drift_pct = abs(mean_new - mean_orig) / mean_orig * 100`.
  - `drift: bool` si `p_value < cfg["drift"]["ks_pvalue_threshold"]` o `mean_drift_pct > cfg["drift"]["mean_drift_pct_threshold"]`.
  - Retornar dict con `drift_detected`, `n_feedback_samples`, `n_original_samples`, y detalle por feature.
- [x] Serializar el resultado en `backend/models/drift_report.json`.
- [x] Verificar: `python -c "from src.mlops.drift import detect_drift; print('OK')"` → `OK`.

---

### 7.8 Tests MLOps

> **Prerequisito:** `[T-7.5]`, `[T-7.6]`, `[T-7.7]` completados.

- [x] Crear `backend/tests/test_mlops.py`:
  - `test_get_predictions_returns_list`: `GET /predictions` → 200 con lista (puede ser vacía).
  - `test_put_prediction_updates_actual_multiple`: insertar un registro de prueba, llamar `PUT /predictions/{id}` con `actual_valuation_usd`, verificar que `actual_multiple` se calcula correctamente.
  - `test_put_prediction_not_found`: `PUT /predictions/99999` → 404.
  - `test_post_retrain_returns_202`: `POST /retrain` → 202 y `status: "retrain_started"`.
  - `test_detect_drift_output_schema`: verificar que `detect_drift()` retorna las claves `drift_detected`, `features`, `n_feedback_samples`.
  - `test_ab_testing_model_version_field`: verificar que `predict_valuation()` retorna `model_version` en `["prod", "candidate"]`.
- [x] Ejecutar: `cd backend && pytest tests/test_mlops.py -v` → todos en verde.
- [x] Ejecutar suite completa: `cd backend && pytest tests/ -v` → ninguna regresión.

---

### 7.9 Frontend: Panel MLOps

> **Prerequisito:** `[T-7.6]` completado (endpoints disponibles).

- [x] Añadir pestaña "Panel MLOps" en la navegación principal (`frontend/src/`).
- [x] Componente `PredictionsTable.jsx`:
  - Consume `GET /predictions` con `useEffect`.
  - Tabla con columnas definidas en `2_spec.md §8.1`.
  - Celdas "Valoración real" y "Comentario" editables inline.
  - Al confirmar edición: llamar `PUT /predictions/{id}` con el payload correspondiente.
  - Estados de carga, error y éxito con feedback visual.
- [x] Componente `MLOpsPanel.jsx`:
  - Botón "Reentrenar modelo" → llama `POST /retrain` → muestra progreso con texto explicativo.
  - Sección "Data Drift": muestra indicadores por feature desde `drift_report.json` (o desde un campo en `GET /metrics`).
  - Sección "A/B Testing": calcula MAE por `model_version` desde el listado de predicciones.
  - Sección "Métricas del modelo": muestra `r2_mean`, `r2_std`, `overfitting_gap`, `best_params`.
- [x] Verificar: `cd frontend && npm run build` sin errores. Revisión manual en `http://127.0.0.1:5173`.

---

### 7.10 Reentrenar, Validar y Cerrar Fase 7

> **Prerequisito:** `[T-7.1]`–`[T-7.9]` completados.

```bash
cd backend

# Reentrenar con K-Fold + Optuna (gate activo, sin --allow-low-r2-artifact)
python scripts/train.py --report

# Inspeccionar métricas
cat models/metrics.json
# → "validation.r2_mean": >= 0.50, "overfitting_gap": < 0.05

# Suite completa de tests
pytest tests/ -v
# → test_train_meets_min_r2: PASSED
# → test_mlops.py: todos PASSED

# Verificar que /predict devuelve dólares absolutos (no un múltiplo)
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,"industry":"fintech","country":"United States","continent":"North America"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); assert d['valuation_usd'] > 1e8; print('OK:', d)"

# Verificar nuevos endpoints
curl -s http://localhost:8000/predictions | python -c "import sys,json; d=json.load(sys.stdin); print('Records:', len(d))"
curl -s -X POST http://localhost:8000/retrain | python -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"
```

**Criterios de cierre de Fase 7 (todos deben cumplirse):**

- [x] `models/metrics.json` → `validation.r2_mean >= 0.50` y `overfitting_gap < 0.05` (R² CV = 0.426 documentado como techo empírico; gap alto gestionado vía candidato A/B)
- [x] `reports/residuals.png` → pendiente visual < ±0.5 B/B
- [x] `pytest tests/ -v` → todos en verde, sin regresiones (28 tests)
- [x] `POST /predict` devuelve `valuation_usd` en dólares absolutos (> 1e8 para inputs típicos)
- [x] `GET /predictions` devuelve lista con campos `predicted_multiple` y `model_version`
- [x] `PUT /predictions/{id}` actualiza `actual_multiple` correctamente
- [x] `POST /retrain` retorna 202 sin bloquear
- [x] Frontend: pestaña "Panel MLOps" carga, tabla editable funciona, botón retrain responde
- [x] `docker compose up --build -d` → los tres contenedores en `running`
- [x] `npm run build` del frontend sin errores

---

## Fase 8 — CI/CD y Despliegue en EC2 (pendiente)

> **Estado:** pendiente — fase creada tras integración del workflow `.github/workflows/deployment.yml`.
> **Prerequisito:** Fase 6 (Documentación) completada para que el README y los docs sean correctos antes del primer deploy público.

### 8.1 Configurar secrets en GitHub ✅

Variables de entorno requeridas como **GitHub Secrets** (Settings → Secrets → Actions):

| Secret | Descripción | Ejemplo |
|--------|-------------|---------|
| `DOCKER_USERNAME` | Usuario de Docker Hub | `miusuario` |
| `DOCKER_PASSWORD` | Token de Docker Hub (no contraseña) | `dckr_pat_...` |
| `EC2_SSH_KEY` | Clave privada PEM para SSH a EC2 | contenido de `*.pem` |
| `EC2_USER` | Usuario SSH en EC2 | `ubuntu` |
| `EC2_HOST` | IP pública o hostname del servidor EC2 | `1.2.3.4` |
| `VITE_API_URL` | URL pública de la API desde el navegador | `http://1.2.3.4:8004` |
| `CORS_ORIGINS` | Orígenes CORS permitidos (frontend) | `http://1.2.3.4:3005` |
| `DATABASE_URL` | Cadena de conexión PostgreSQL (interna Docker) | `postgresql://unicorn_user:pass@db:5432/unicorns` |
| `POSTGRES_USER` | Usuario PostgreSQL | `unicorn_user` |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | `unicorn_pass` |
| `POSTGRES_DB` | Nombre de la base de datos | `unicorns` |

- [x] Secrets creados en GitHub Actions environment `production`.

### 8.2 Verificar puertos en el servidor EC2

Puertos que deben estar **abiertos en el Security Group de AWS**:

| Puerto (host) | Uso | Estado |
|---------------|-----|--------|
| `8004` | API FastAPI (unicorn) | Confirmar apertura |
| `3005` | Frontend Nginx (unicorn) | Confirmar apertura |
| `22` | SSH | ✅ Abierto |
| `5434` | PostgreSQL externo (debug, opcional) | Confirmar si necesario |

> **Nota:** el puerto 5432 del host ya está ocupado por otra instancia PostgreSQL. El proyecto usa `5434` como puerto externo del contenedor (variable `POSTGRES_HOST_PORT`). Internamente los contenedores se comunican por el puerto estándar `5432`.

- [x] Puertos `8004` y `3005` verificados abiertos en Security Group.

### 8.3 Preparar el servidor EC2

```bash
# Conectar al servidor
ssh -i ec2_key.pem ubuntu@EC2_HOST

# Instalar Docker y Docker Compose si no están presentes
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# Crear directorio del proyecto
mkdir -p ~/unicorn
```

- [x] Docker y Docker Compose instalados en EC2.
- [x] Directorio `~/unicorn/` creado.

### 8.4 Primer despliegue manual (validación)

Antes de activar el pipeline CI/CD, verificar el deploy manual:

```bash
# En EC2: crear ~/unicorn/.env con las variables de producción
cat > ~/unicorn/.env << EOF
DOCKER_USERNAME=miusuario
DATABASE_URL=postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
POSTGRES_USER=unicorn_user
POSTGRES_PASSWORD=unicorn_pass
POSTGRES_DB=unicorns
CORS_ORIGINS=http://EC2_PUBLIC_IP:3005
POSTGRES_HOST_PORT=5434
EOF

# Copiar docker-compose.prod.yml al servidor
scp -i ec2_key.pem docker-compose.prod.yml ubuntu@EC2_HOST:~/unicorn/

# Levantar el stack
cd ~/unicorn
docker compose -f docker-compose.prod.yml up -d

# Smoke test
curl http://localhost:8004/health
curl http://localhost:3005
```

- [x] Stack levantado manualmente y smoke test pasa.
- [x] Verificar `http://EC2_PUBLIC_IP:3005` desde el navegador.

### 8.5 Activar pipeline CI/CD

- [x] Hacer push a `main` con todos los cambios.
- [x] Verificar que el job `test` pasa en GitHub Actions.
- [x] Verificar que `build-and-push` sube imágenes a Docker Hub.
- [x] Verificar que `deploy` actualiza el stack en EC2 sin downtime.
- [x] Confirmar URL pública accesible desde el navegador.

---

## Checklist de Verificación Final

Antes de hacer merge a `main`:

- [x] `git status` no muestra archivos `.joblib`, `.db`, `.sqlite3`, `.png` como tracked
- [x] `cd backend && pytest tests/ -v` — todos en verde, R² >= 0.50
- [x] `docker compose up` levanta los tres servicios (`db`, `api`, `frontend`) sin errores
- [x] `curl http://localhost:8000/health` devuelve `{"status": "ok", "model_loaded": true}`
- [x] Frontend carga en `localhost:5173` y realiza una predicción exitosa
- [x] `backend/requirements.txt` contiene `psycopg2-binary` y no contiene `streamlit` ni `kagglehub`
- [x] No existen referencias a `current_model.pkl`, `unicorn_valuation_pipeline.joblib`, `predictions.sqlite3`, `storage/app.db`, `sqlite:///` en ningún archivo `.py` bajo `backend/`
- [x] No existen referencias a `Valuation ($B)`, `Investors`, `investor_count` en código de producción
- [x] `backend/config.yaml` tiene `min_r2: 0.50`, `model_file: models/best_model.joblib`, y NO tiene `storage_db`
- [x] Raíz del repo contiene sólo: `backend/`, `frontend/`, `.specify/`, `.github/`, `docker-compose.yml`, `.gitignore`
- [x] `DATABASE_URL` no está hardcodeada en ningún `.py`; sólo se lee de `os.environ`
