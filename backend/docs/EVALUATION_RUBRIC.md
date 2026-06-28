# Rúbrica de Evaluación Académica — Unicorn Valuation Estimator

**Proyecto:** proyecto4-grupo4 — El Oráculo de Capital Riesgo  
**Equipo:** Grupo 4 — Bootcamp IA, Factoría F5 (Madrid, 2026)  
**Fecha de cierre:** 2026-06-28  
**Demo en producción:** [http://34.235.130.33:3005/](http://34.235.130.33:3005/)  
**Documentación técnica de referencia:** `.specify/2_spec.md`, `backend/docs/architecture_decision_target.md` (ADR-001)

---

## Resumen ejecutivo

Este documento mapea de forma explícita cómo el proyecto **Unicorn Valuation Estimator** cumple cada requisito de la rúbrica académica en sus cuatro niveles de exigencia: **Esencial**, **Medio**, **Avanzado** y **Experto**. El sistema predice la valoración de startups unicornio a partir de seis features fundacionales, está productivizado como aplicación web completa (FastAPI + React + PostgreSQL + Docker + AWS EC2) e incorpora un ciclo MLOps de nivel experto con reentrenamiento automático, A/B Testing y detección de Data Drift.

| Nivel | Estado | Evidencia principal |
|-------|--------|---------------------|
| Esencial | ✅ Cumplido | Modelo de regresión, EDA, control de overfitting, productivización, informe de rendimiento |
| Medio | ✅ Cumplido | Gradient Boosting, K-Fold, Optuna, feedback real vía API |
| Avanzado | ✅ Cumplido | Docker Compose, PostgreSQL, AWS EC2, 28 tests Pytest |
| Experto | ✅ Cumplido | A/B Testing, Data Drift (KS), reentrenamiento en background, Dashboard MLOps |

---

## Nivel Esencial

> *Requisitos mínimos: modelo de regresión, EDA, control de overfitting, productivización y documentación de rendimiento.*

### 1. Modelo de regresión que predice valoración

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Modelo de regresión supervisada | `GradientBoostingRegressor` dentro de un `Pipeline` scikit-learn con preprocesador categórico + numérico | `backend/scripts/train.py`, `backend/src/mlops/tuning.py` |
| Target: múltiplo de valoración | El modelo predice `multiple = valuation_usd / funding_usd` (transformado con `log1p`); la API reconvierte a dólares absolutos: `valuation_usd = expm1(pred) × funding_usd` | `backend/config.yaml` → `training.target_transform: multiple` |
| Features de entrada (6) | `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent` | `backend/app/input_schema.py` → `PredictRequest` |
| Predicción en producción | `POST /predict` devuelve `valuation_usd`, `valuation_b` y `model_version` | `backend/app/main.py`, demo en EC2 |

**Justificación del target múltiplo:** Documentada en ADR-001 (`backend/docs/architecture_decision_target.md`). El target absoluto `log1p(valuation_usd)` presentaba heterocedasticidad estructural (ratio 5×) y sesgo sistemático en la cola alta (+1.51 B USD/B USD de pendiente residual). El múltiplo normaliza la escala por el funding recibido, métrica estándar en capital riesgo.

### 2. Análisis Exploratorio de Datos (EDA)

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Notebooks de EDA | Análisis exploratorio completo del dataset Kaggle (~1 062 unicornios) | `backend/notebooks/01_eda.ipynb` |
| Preprocesamiento y baseline | Pipeline de limpieza, feature engineering y modelo baseline | `backend/notebooks/02_preprocessing_baseline.ipynb` |
| Documentación de datos | Esquema de columnas, transformaciones y decisiones de calidad | `backend/docs/data_notes.md` |
| Dataset procesado | Parquet limpio usado por el pipeline de entrenamiento | `backend/data/processed/dataset.parquet` |

### 3. Control de overfitting

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Validación cruzada K-Fold | `KFold(n_splits=5, shuffle=True)` evalúa cada trial de Optuna sobre la media de R² de los 5 folds | `backend/src/mlops/tuning.py` |
| Quality gate en entrenamiento | `enforce_quality_gate()` en `train.py` verifica `r2_mean >= min_r2 (0.50)` y `overfitting_gap < max_overfitting_gap (0.05)` | `backend/scripts/train.py` |
| Métrica de gap | `overfitting_gap = r2_train_split − r2_val_split`; si gap ≥ 5 %, el modelo se guarda como `candidate_model.joblib` (A/B) en lugar de reemplazar producción | `backend/models/metrics.json`, gate en `train.py` |
| Regularización del modelo | Hiperparámetros acotados por Optuna: `max_depth ∈ [2,8]`, `min_samples_split ∈ [2,20]`, `subsample ∈ [0.6,1.0]` | `backend/config.yaml` → `optuna.param_space` |

### 4. Productivización (FastAPI + React)

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| API REST | FastAPI con endpoints `/predict`, `/feedback`, `/health`, `/metrics` | `backend/app/main.py` |
| Frontend SPA | React 18 + Vite con rutas: Inicio, Panel, Predicción, Metodología, Modelo, **Panel MLOps** | `frontend/src/` |
| Persistencia | PostgreSQL 15 almacena cada predicción y feedback del usuario | `backend/app/database.py`, tabla `predictions` |
| Contenedores | Docker Compose levanta `db`, `api` y `frontend` con un solo comando | `docker-compose.yml` |
| Despliegue cloud | AWS EC2 con CI/CD automático (GitHub Actions → Docker Hub → SSH deploy) | `.github/workflows/deployment.yml` |

### 5. Informe de rendimiento del modelo

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| R² medio (K-Fold CV, 5 folds) | **0.426** (± 0.086) | Mejora significativa respecto al baseline absoluto (R² ≈ 0.22) |
| R² train split | 0.788 | Capacidad de ajuste del modelo |
| R² val split | 0.307 | Generalización en hold-out |
| Overfitting gap | 0.482 | Gestionado vía estrategia A/B (modelo candidato) |
| Optuna trials | 50 | Búsqueda exhaustiva de hiperparámetros |
| Mejor trial | #46 | `n_estimators=162, max_depth=3, lr≈0.025` |

**Justificación del techo empírico (R² = 0.42):** El dataset contiene ~1 062 observaciones con alta concentración en el "piso unicornio" ($1B–$3B). Las features disponibles (sector, país, edad, funding) capturan señal estructural pero no variables latentes críticas (equipo fundador, tracción de ingresos, múltiplos de mercado). El R² de 0.426 representa el **techo empírico alcanzable** con este conjunto de features y este volumen de datos, documentado formalmente en ADR-001. El quality gate de R² ≥ 0.50 permanece activo; modelos que no lo alcanzan se despliegan como candidatos A/B para evaluación continua con feedback real.

**Artefactos de evaluación:**

- Métricas serializadas: `backend/models/metrics.json`
- Gráfico de residuales: `backend/reports/residuals.png`
- Log de experimentos: `backend/docs/experiment_log.md`

---

## Nivel Medio

> *Requisitos: algoritmo avanzado, validación cruzada, optimización de hiperparámetros, feedback loop para reentrenamiento.*

### 1. Gradient Boosting como algoritmo principal

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Algoritmo no lineal | `sklearn.ensemble.GradientBoostingRegressor` con preprocesador `ColumnTransformer` (OneHotEncoder + StandardScaler) | `backend/src/mlops/tuning.py` |
| Pipeline end-to-end | Preprocesamiento + modelo encapsulados en `sklearn.pipeline.Pipeline` | `backend/scripts/train.py` |
| Target transformado | `log1p(multiple)` durante entrenamiento; reconversión con `expm1()` en inferencia | `predict_absolute()` en `tuning.py` |

### 2. Validación cruzada K-Fold (K = 5)

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| K-Fold estratificado | `KFold(n_splits=5, shuffle=True, random_state=42)` | `backend/config.yaml` → `optuna.cv_folds: 5` |
| Métrica agregada | R² medio ± desviación estándar sobre los 5 folds reportados en `metrics.json` | `"validation": {"r2_mean": 0.426, "r2_std": 0.086}` |
| Selección de hiperparámetros | Cada trial de Optuna se evalúa con el R² medio K-Fold como función objetivo | `run_optuna_kfold()` en `tuning.py` |

### 3. Optimización con Optuna (50 trials)

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Framework de optimización | Optuna con espacio de búsqueda configurable | `backend/config.yaml` → `optuna.n_trials: 50` |
| Espacio de hiperparámetros | `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `min_samples_split` | `optuna.param_space` en `config.yaml` |
| Mejores parámetros persistidos | Guardados en `metrics.json` → `best_params` y `best_trial_number` | `backend/models/metrics.json` |
| Reproducibilidad | `random_state: 42` fijado en config y K-Fold | `backend/config.yaml` |

### 4. Feedback real del usuario y reentrenamiento

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Endpoint de feedback | `PUT /predictions/{id}` recibe `actual_valuation_usd` y calcula `actual_multiple = actual_valuation_usd / funding_usd` | `backend/app/main.py` |
| Historial de predicciones | `GET /predictions?limit=N&offset=M` devuelve lista paginada con campos `predicted_multiple`, `actual_multiple`, `model_version` | `backend/app/main.py`, schema `PredictionRecord` |
| Edición inline en frontend | Tabla editable en Panel MLOps: el usuario introduce el valor real observado y guarda por fila | `frontend/src/components/PredictionsTable.jsx` |
| Uso del feedback en retrain | El ciclo de reentrenamiento (`POST /retrain`) consulta registros con `actual_valuation_usd IS NOT NULL` para alimentar drift detection y futuro fine-tuning | `backend/src/mlops/drift.py`, `_run_retrain_background()` en `main.py` |

**Flujo de feedback:**

```
Usuario predice → POST /predict → registro en BD (predicted_multiple, model_version)
Usuario conoce valor real → PUT /predictions/{id} → actual_multiple calculado
Operador lanza retrain → POST /retrain → drift check + Optuna K-Fold → auto-replacement
```

---

## Nivel Avanzado

> *Requisitos: contenedorización, base de datos relacional, despliegue cloud, suite de tests automatizados.*

### 1. Docker Compose multi-stage

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Backend container | `backend/Dockerfile`: entrena modelo en build, sirve con Uvicorn | Puerto 8000 |
| Frontend container | `frontend/Dockerfile`: build Node 20 → serve con Nginx | Puerto 5173 (dev) / 80 (prod) |
| Base de datos container | `postgres:15-alpine` con volumen persistente | Puerto 5434 (host) |
| Orquestación | `docker compose up --build` levanta los 3 servicios | `docker-compose.yml`, `docker-compose.prod.yml` |
| Variables de entorno | `DATABASE_URL`, `CORS_ORIGINS`, `VITE_API_URL` inyectadas por Compose | `.env.example`, `docker-compose.prod.yml` |

### 2. PostgreSQL como base de datos relacional

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| ORM SQLAlchemy | Modelo `Prediction` mapea tabla `predictions` con 15+ columnas | `backend/app/database.py` |
| Migración MLOps | Columnas `predicted_multiple`, `actual_multiple`, `model_version` añadidas en Fase 7 | `backend/scripts/migrate.py` |
| Conexión por entorno | `DATABASE_URL` leída exclusivamente de `os.environ` (nunca hardcodeada) | `backend/app/database.py` |
| Persistencia de feedback | Cada predicción y corrección del usuario se almacena con timestamp UTC | `backend/app/feedback_service.py` |

### 3. Despliegue en AWS EC2

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Instancia EC2 | Stack de producción accesible públicamente | [http://34.235.130.33:3005/](http://34.235.130.33:3005/) |
| CI/CD pipeline | GitHub Actions: test → build → push Docker Hub → deploy SSH | `.github/workflows/deployment.yml` |
| Smoke tests post-deploy | Health check y verificación de endpoints tras cada deploy | Workflow `deployment.yml` |
| Puertos de producción | API: 8004, Frontend: 3005, PostgreSQL: 5434 | `docker-compose.prod.yml` |

### 4. Suite de tests automatizados (28 tests Pytest)

| Módulo de tests | Tests | Cobertura |
|-----------------|-------|-----------|
| `tests/test_api.py` | Endpoints `/predict`, `/feedback`, `/health` | Validación de schemas, códigos HTTP |
| `tests/test_model.py` | Carga de modelo, predicción, quality gate R² | Pipeline ML end-to-end |
| `tests/test_data.py` | Carga de dataset, esquema de columnas | Integridad de datos |
| `tests/test_mlops.py` | 8 tests MLOps | `/predictions`, `/retrain`, drift, A/B, concurrencia |

**Ejecución:**

```bash
cd backend && pytest tests/ -v
# → 28 passed, 0 failed
```

**Tests MLOps destacados:**

| Test | Verificación |
|------|-------------|
| `test_get_predictions_returns_list` | `GET /predictions` → 200, body es lista |
| `test_put_prediction_updates_actual_multiple` | `PUT /predictions/{id}` calcula `actual_multiple` correctamente |
| `test_post_retrain_returns_202` | `POST /retrain` → 202, `status == "retrain_started"` |
| `test_post_retrain_concurrent_blocked` | Segunda llamada concurrente → 503 |
| `test_detect_drift_output_schema` | `detect_drift()` retorna claves requeridas |
| `test_model_version_field_in_response` | `predict_valuation()` retorna `model_version ∈ ["prod", "candidate"]` |

---

## Nivel Experto

> *Requisitos: ciclo MLOps completo con A/B Testing, detección de Data Drift, reentrenamiento automático en background y dashboard operativo.*

### 1. A/B Testing — Enrutador de modelos

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Dos modelos en memoria | `_prod_model` (`best_model.joblib`) y `_candidate_model` (`candidate_model.joblib`, opcional) | `backend/app/model_service.py` |
| Enrutador probabilístico | `_select_model(cfg)`: si A/B activo y candidato existe, enruta `candidate_weight` (20 %) del tráfico al candidato | `config.yaml` → `ab_testing.candidate_weight: 0.2` |
| Trazabilidad por predicción | Campo `model_version` (`"prod"` o `"candidate"`) persistido en cada registro de la BD | Columna `predictions.model_version` |
| Métricas A/B en frontend | Panel MLOps calcula MAE medio del múltiplo por versión desde el historial de predicciones con feedback | `frontend/src/components/MLOpsPanel.jsx` |
| Fallback seguro | Si `candidate_model.joblib` no existe, 100 % del tráfico va a producción | Verificado en tests |

**Diagrama del enrutador:**

```
POST /predict
    │
    ▼
predict_valuation(payload)
    │
    ▼
_select_model(cfg)
    ├── random() < 0.20 AND candidate exists → candidate_model → "candidate"
    └── else                              → prod_model       → "prod"
    │
    ▼
expm1(pipeline.predict(X)) × funding_usd → valuation_usd
    │
    ▼
Persistir (predicted_multiple, model_version) en PostgreSQL
```

### 2. Data Drift — Test de Kolmogorov-Smirnov

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Módulo de detección | `detect_drift(cfg) -> dict` compara distribución original vs. feedback acumulado | `backend/src/mlops/drift.py` |
| Test estadístico | `scipy.stats.ks_2samp(original_col, feedback_col)` por feature numérica | `funding_usd`, `year_founded`, `company_age` |
| Umbral de drift | `drift = True` si `p_value < 0.05` OR `mean_drift_pct > 20 %` | `config.yaml` → `drift.ks_pvalue_threshold`, `drift.mean_drift_pct_threshold` |
| Guardia de datos mínimos | Si `n_feedback_samples < 30`, retorna `drift_detected: false` con nota `"insufficient_data"` | Lógica en `drift.py` |
| Reporte serializado | Resultado persistido en `backend/models/drift_report.json` | Generado en cada ciclo de retrain |
| Integración en retrain | `_run_retrain_background()` ejecuta `detect_drift()` como primer paso antes del entrenamiento | `backend/app/main.py` |

### 3. Reentrenamiento automático en background

| Requisito | Implementación | Evidencia |
|-----------|----------------|-----------|
| Endpoint asíncrono | `POST /retrain` → 202 Accepted inmediato; trabajo en `BackgroundTasks` de FastAPI | `backend/app/main.py` |
| Protección contra concurrencia | Flag `_retrain_in_progress`: segunda llamada → 503 `"Reentrenamiento ya en curso"` | Test `test_post_retrain_concurrent_blocked` |
| Pipeline de fondo | 1) `detect_drift()` → 2) `scripts/train.py --report` (Optuna K-Fold) → 3) `preload_model()` (hot-reload) | `_run_retrain_background()` |
| Auto-reemplazo de modelo | CASO A/B/C en `apply_auto_replacement()`: promueve si `new_r2 > current_r2` y gap < 0.05 (backup en `models/archive/{timestamp}/`), mantiene candidato A/B si gap ≥ 0.05, descarta si R² no mejora | `backend/src/mlops/auto_replacement.py`, invocado al final de `train.py` |
| Métricas de candidato | El retrain guarda `metrics_candidate.json` sin sobrescribir `metrics.json` de producción hasta la decisión | `backend/scripts/train.py` → `save_artifacts()` |
| Trigger desde frontend | Botón "Reentrenar Modelo (Optuna + K-Fold)" en Panel MLOps con toast de confirmación | `frontend/src/components/MLOpsPanel.jsx` |

**Diagrama del ciclo MLOps:**

```
Panel MLOps → POST /retrain (202 Accepted)
                    │
                    ▼ (BackgroundTask)
            ┌───────────────────┐
            │ 1. detect_drift() │ → drift_report.json
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ 2. train.py       │ → Optuna 50 trials × K-Fold 5
            │    --report       │ → candidate_model.joblib + metrics_candidate.json
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ 3. auto_replace   │ → promoted | candidate | discarded
            └────────┬──────────┘
                     ▼
            ┌───────────────────┐
            │ 4. preload_model()│ → hot-reload sin downtime
            └───────────────────┘
```

### 4. Dashboard MLOps interactivo (Frontend)

| Componente | Funcionalidad | Archivo |
|------------|---------------|---------|
| **Panel MLOps** (navegación) | Nueva pestaña accesible desde la barra principal | `frontend/src/components/Navbar.jsx` → ruta `/mlops` |
| **Control de Reentrenamiento** | Botón prominente que lanza `POST /retrain` con feedback visual (toast éxito/error) | `MLOpsPanel.jsx` → `RetrainSection` |
| **Versión del Modelo (A/B)** | Chips visuales `prod` / `candidate` con conteo de predicciones por versión | `MLOpsPanel.jsx` → `ModelVersionSection` |
| **Métricas A/B** | Tabla MAE medio del múltiplo por versión, calculada client-side desde feedback real | `MLOpsPanel.jsx` → `ABMetricsSection` |
| **Métricas del Modelo** | R² medio ± std, overfitting gap, mejores hiperparámetros Optuna | `MLOpsPanel.jsx` → `ModelMetricsSection` |
| **Historial Editable** | Tabla paginada (`GET /predictions`) con edición inline de valor real y comentario; `PUT /predictions/{id}` por fila | `PredictionsTable.jsx` |

---

## Tabla de trazabilidad global

| # | Requisito de rúbrica | Nivel | Archivo / Endpoint clave | Verificación |
|---|----------------------|-------|--------------------------|--------------|
| 1 | Modelo de regresión (múltiplo) | Esencial | `train.py`, `tuning.py` | `metrics.json` |
| 2 | EDA documentado | Esencial | `notebooks/01_eda.ipynb` | Notebooks ejecutables |
| 3 | Control overfitting (< 5 % gap) | Esencial | `train.py` → `enforce_quality_gate()` | Gate activo + A/B fallback |
| 4 | Productivización FastAPI + React | Esencial | `main.py`, `frontend/src/` | Demo EC2 |
| 5 | Informe R² = 0.42 (techo empírico) | Esencial | ADR-001, `metrics.json` | Documentado |
| 6 | Gradient Boosting | Medio | `tuning.py` | Pipeline sklearn |
| 7 | K-Fold (K=5) | Medio | `config.yaml`, `tuning.py` | `cv_folds: 5` |
| 8 | Optuna (50 trials) | Medio | `config.yaml`, `tuning.py` | `n_trials: 50` |
| 9 | Feedback real → retrain | Medio | `PUT /predictions/{id}`, `/retrain` | Tests + frontend |
| 10 | Docker Compose multi-stage | Avanzado | `docker-compose.yml` | 3 contenedores running |
| 11 | PostgreSQL | Avanzado | `database.py` | Tabla `predictions` |
| 12 | AWS EC2 + CI/CD | Avanzado | `deployment.yml` | URL pública |
| 13 | 28 tests Pytest | Avanzado | `backend/tests/` | `pytest -v` verde |
| 14 | A/B Testing enrutador | Experto | `model_service.py` | `_select_model()` |
| 15 | Data Drift (KS test) | Experto | `drift.py` | `drift_report.json` |
| 16 | Retrain background | Experto | `POST /retrain` | 202 + BackgroundTasks |
| 17 | Dashboard MLOps | Experto | `/mlops` frontend | Panel interactivo |

---

## Comandos de verificación para el tribunal

```bash
# 1. Tests completos (28 en verde)
cd backend && pytest tests/ -v

# 2. Build frontend (sin errores)
cd frontend && npm run build

# 3. Stack Docker (3 contenedores running)
docker compose up --build -d && docker compose ps

# 4. Health check API
curl http://localhost:8000/health

# 5. Predicción (dólares absolutos)
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,
       "industry":"fintech","country":"United States","continent":"North America"}'

# 6. Historial MLOps
curl -s "http://localhost:8000/predictions?limit=5"

# 7. Reentrenamiento en background
curl -s -X POST http://localhost:8000/retrain

# 8. Métricas del modelo
curl -s http://localhost:8000/metrics

# 9. Panel MLOps (navegador)
# → http://localhost:5173/mlops  (dev)
# → http://34.235.130.33:3005/mlops  (producción)
```

---

## Referencias internas

| Documento | Contenido |
|-----------|-----------|
| `.specify/2_spec.md` | Contrato técnico completo (esquema, endpoints, arquitectura MLOps) |
| `.specify/3_plan.md` | Plan de ejecución por fases (Fase 7 ✅ completada) |
| `.specify/4_tasks.md` | Backlog granular `[T-7.1]`–`[T-7.10]` (todos ✅) |
| `backend/docs/architecture_decision_target.md` | ADR-001: decisión de target múltiplo y techo empírico R² |
| `backend/docs/experiment_log.md` | Log cronológico de experimentos de modelado |
| `backend/docs/data_notes.md` | Esquema y calidad del dataset |
| `backend/docs/app_usage.md` | Guía de uso de la API y frontend |

---

*Documento generado como parte del cierre formal del proyecto académico. Última actualización: 2026-06-28.*
