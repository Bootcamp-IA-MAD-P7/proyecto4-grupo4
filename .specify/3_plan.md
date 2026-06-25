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
| **Fase 5 — Frontend React** | **▶ Activa** |
| Fase 6 — Documentación | Bloqueada |
| Fase 7 — Optimización Post-MVP | 🧊 Congelada |

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

## Fase 5 — Frontend React (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 4.

### 5.1 Verificar `frontend/src/api.js`

- [ ] `BASE_URL` apunta a `http://localhost:8000`
- [ ] Función `predict(payload)` usa el esquema de `2_spec.md`
- [ ] Función `submitFeedback(payload)` usa el endpoint `/feedback`

### 5.2 Verificar `frontend/src/data/modelMetrics.js`

- [ ] Sustituir métricas hardcodeadas por una llamada al endpoint `GET /metrics`
- [ ] El componente `MetricCard` recibe R² dinámico desde la API

### 5.3 Actualizar `frontend/src/components/PredictionForm.jsx`

- [ ] Los campos del formulario coinciden con `PredictRequest`: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`
- [ ] Eliminar cualquier campo legacy (`city`, `join_year`, `join_month`, `investor_count`)

### 5.4 Actualizar `frontend/src/components/PredictionResult.jsx`

- [ ] Mostrar `valuation_b` formateado (ej: `$1.25B`) y `valuation_usd` completo
- [ ] Corregir cualquier texto con mojibake (`Predicción`, `R²`)

### 5.5 Verificar build

```bash
cd frontend && npm install && npm run build
```

- [ ] Build sin errores ni warnings críticos

### 5.6 Actualizar `docker-compose.yml` — incluir servicio `db` (PostgreSQL)

El `docker-compose.yml` debe definir exactamente tres servicios:

```yaml
services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: unicorn_user
      POSTGRES_PASSWORD: unicorn_pass
      POSTGRES_DB: unicorns
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "5173:80"
    depends_on:
      - api

volumes:
  postgres_data:
```

- [ ] Escribir el bloque anterior en `docker-compose.yml` (reemplazar contenido existente)
- [ ] Eliminar cualquier servicio `streamlit` que pudiera existir
- [ ] Eliminar cualquier volumen de `storage/` que hacía referencia a `app.db`
- [ ] Verificar que `docker compose config` no lanza errores de sintaxis

---

## Fase 6 — Documentación y Cierre (pendiente)

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

## Fase 7 — Optimización Post-MVP (Deuda Técnica) 🧊 CONGELADA

> **Estado:** 🧊 congelada — no iniciar hasta completar el MVP funcional (Fases 4–6).
> **Decisión arquitectónica:** documentada en `backend/docs/architecture_decision_target.md` (ADR-001).
> **Ticket de ejecución:** `[T-7.1]` en `4_tasks.md`.

### 7.1 Refactorizar target de entrenamiento a Múltiplo de Valoración

El modelo actual (Fases 1–4, GradientBoosting) alcanza R²≈0.22 con el target absoluto `valuation_usd`. El diagnóstico de residuos documentado en ADR-001 evidencia un patrón sistemático de heterocedasticidad: sesgo de subestimación proporcional a la magnitud (+1.5 B USD de error residual por B USD predicho, ratio 5×).

**Objetivo:** sustituir el target de entrenamiento por el *múltiplo de valoración*:

```
multiple = valuation_usd / funding_usd
```

y recuperar la valoración en inferencia mediante:

```
valuation_usd_pred = predicted_multiple × funding_usd
```

Esta transformación absorbe la escala operativa del negocio y reduce la heterocedasticidad estructural. Incremento esperado de R² hacia el rango 0.35–0.50. **El contrato de la API no cambia** — `POST /predict` seguirá devolviendo `valuation_usd` y `valuation_b` en dólares absolutos (ver `2_spec.md` §4).

#### Archivos afectados (confinados al backend ML)

| Archivo | Cambio |
|---------|--------|
| `backend/src/models/train.py` | `fit_model()` usa `log1p(multiple)`; `predict_absolute()` reconvierte por `funding_usd` |
| `backend/config.yaml` | Nueva clave `target_transform: "multiple"` |
| `backend/scripts/train.py` | `enforce_quality_gate()` con umbral R²≥0.50 sobre el múltiplo |
| `backend/app/model_service.py` | `predict_valuation()` pasa `funding_usd` al pipeline para reconversión post-inferencia |
| `backend/tests/test_pipeline.py` | `test_train_meets_min_r2` actualizado con nuevo umbral esperado |

#### Criterios de aceptación

- R² validación ≥ 0.35 (objetivo); ≥ 0.50 (gate de CI)
- Pendiente del Residual Plot < +0.8 B/B (reducción ≥ 47% del sesgo actual)
- `POST /predict` responde con el mismo esquema de `2_spec.md` §4 sin cambios de interfaz
- `test_train_meets_min_r2` pasa en verde

- [ ] Estado: pendiente — ver `[T-7.1]` en `4_tasks.md`

---

## Checklist de Verificación Final

Antes de hacer merge a `main`:

- [ ] `git status` no muestra archivos `.joblib`, `.db`, `.sqlite3`, `.png` como tracked
- [ ] `cd backend && pytest tests/ -v` — todos en verde, R² >= 0.50
- [ ] `docker compose up` levanta los tres servicios (`db`, `api`, `frontend`) sin errores
- [ ] `curl http://localhost:8000/health` devuelve `{"status": "ok", "model_loaded": true}`
- [ ] Frontend carga en `localhost:5173` y realiza una predicción exitosa
- [ ] `backend/requirements.txt` contiene `psycopg2-binary` y no contiene `streamlit` ni `kagglehub`
- [ ] No existen referencias a `current_model.pkl`, `unicorn_valuation_pipeline.joblib`, `predictions.sqlite3`, `storage/app.db`, `sqlite:///` en ningún archivo `.py` bajo `backend/`
- [ ] No existen referencias a `Valuation ($B)`, `Investors`, `investor_count` en código de producción
- [ ] `backend/config.yaml` tiene `min_r2: 0.50`, `model_file: models/best_model.joblib`, y NO tiene `storage_db`
- [ ] Raíz del repo contiene sólo: `backend/`, `frontend/`, `.specify/`, `.github/`, `docker-compose.yml`, `.gitignore`
- [ ] `DATABASE_URL` no está hardcodeada en ningún `.py`; sólo se lee de `os.environ`
