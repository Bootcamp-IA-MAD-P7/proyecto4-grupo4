# Plan — Checklist de Ejecución

> Ejecutar en orden. Cada fase debe dejar el proyecto en estado compilable y con tests pasando antes de avanzar a la siguiente.
>
> Referencia permanente: `2_spec.md` es el contrato. Todo cambio debe converger hacia él.

---

## Fase 0 — Preparación

- [ ] Crear rama `refactor/stabilize-architecture` desde `main`
- [ ] Documentar estado inicial: ejecutar `pytest` y registrar qué tests fallan (baseline)
- [ ] Hacer snapshot del `models/metrics.json` actual para comparación futura

---

## Fase 1 — Limpieza de Artefactos y Duplicados

### 1.1 Eliminar archivos binarios del índice Git

```bash
git rm --cached models/best_model.joblib
git rm --cached models/unicorn_valuation_pipeline.joblib
git rm --cached models/metrics.json
git rm --cached storage/app.db
git rm --cached data/feedback/predictions.sqlite3
git rm --cached reports/*.png
git rm --cached data/dataset_clean.csv
```

- [ ] Ejecutar los comandos anteriores
- [ ] Los archivos permanecen en disco (sólo salen del índice)

### 1.2 Actualizar `.gitignore`

Añadir las siguientes entradas al `.gitignore` existente:

```
# ML Artifacts — never version these
models/*.joblib
models/*.pkl
models/metrics.json
reports/*.png
reports/*.pdf
data/processed/
data/dataset_clean.csv

# Databases — never version these (production uses PostgreSQL)
storage/*.db
data/feedback/*.sqlite3
*.sqlite3

# Environment variables
.env
.env.*
!.env.example
```

- [ ] Editar `.gitignore` con las entradas anteriores
- [ ] Verificar con `git status` que los artefactos aparecen como "untracked" y no como "modified"

### 1.3 Eliminar archivos duplicados y huérfanos

- [ ] Eliminar `notebooks/data/raw/dataset_raw.csv` (duplicado de `data/raw/dataset_raw.csv`)
- [ ] Eliminar `data/raw/dataset_raw.csv` — el dataset canónico es `data/raw/unicorn_companies.csv`
- [ ] Eliminar `data/dataset_clean.csv` (en raíz de `data/`, duplicado del procesado)
- [ ] Eliminar `src/data/__init___BACKUP.py`
- [ ] Eliminar `notebooks/01_eda_BACKUP.ipynb`
- [ ] Eliminar `app/streamlit_app.py`
- [ ] Evaluar si `src/data/load_data.py` y `src/data/load.py` pueden fusionarse en uno solo; si hay solapamiento, mantener sólo `src/data/load.py` y eliminar `load_data.py`

### 1.4 Eliminar TODAS las bases de datos SQLite

La arquitectura de producción usa PostgreSQL. No existe ningún archivo `.db` ni `.sqlite3` válido en el proyecto.

- [ ] Eliminar `data/feedback/predictions.sqlite3` (DB de feedback legacy)
- [ ] Eliminar `storage/app.db` (DB SQLite que reemplaza PostgreSQL)
- [ ] Eliminar la carpeta `storage/` si queda vacía, o mantener sólo `.gitkeep`
- [ ] Añadir al `.gitignore` (si no están ya):
  ```
  storage/*.db
  data/feedback/*.sqlite3
  *.sqlite3
  ```
- [ ] Verificar que ningún archivo `.py` referencia rutas SQLite directas (ej. `sqlite:///`, `storage/app.db`)

---

## Fase 2 — Unificar Rutas y Configuración

### 2.1 Corregir `config.yaml`

- [ ] Cambiar `paths.model_file` de `models/unicorn_valuation_pipeline.joblib` → `models/best_model.joblib`
- [ ] Verificar `paths.processed_data` = `data/processed/dataset.parquet` ✓
- [ ] **Eliminar** la clave `paths.storage_db` — la DB ya no es un archivo local; la conexión viene de `DATABASE_URL`
- [ ] Verificar `training.min_r2` = `0.50`

### 2.2 Corregir `app/model_service.py`

- [ ] Cambiar la ruta por defecto del modelo de `models/current_model.pkl` → `models/best_model.joblib`
- [ ] Cambiar las features de `country, city, industry, join_year, join_month, investor_count` → `year_founded, funding_usd, company_age, industry, country, continent` (según `2_spec.md`)
- [ ] Eliminar el mock/heurístico de predicción; si no hay modelo, lanzar `503`

### 2.3 Corregir `scripts/train.py`

- [ ] Asegurarse de que guarda el modelo en `models/best_model.joblib` (no en `unicorn_valuation_pipeline.joblib`)
- [ ] Al finalizar el entrenamiento, verificar `validation.r2 >= config.training.min_r2`; si no, `sys.exit(1)` con mensaje claro

### 2.4 Corregir `src/preprocessing/preprocessing_pipeline.py`

- [ ] Deprecar o eliminar las referencias a columnas crudas (`Valuation ($B)`, `Investors`)
- [ ] Si algún notebook activo depende de este módulo, actualizar el notebook para usar `src/data/load.py`
- [ ] Si el módulo queda sin uso, eliminarlo en su totalidad

---

## Fase 3 — Corregir Tests y Umbrales

### 3.1 `tests/test_pipeline.py`

- [ ] Cambiar el assert de R² de `>= 0.15` → `>= 0.50`
- [ ] Cambiar el nombre de columnas en fixtures al esquema definitivo (`year_founded`, `funding_usd`, etc.)
- [ ] Verificar que el test carga el modelo desde `models/best_model.joblib`

### 3.2 `tests/test_preprocessing.py`

- [ ] Actualizar fixtures para usar el esquema de columnas de `2_spec.md`
- [ ] Eliminar referencias a `Valuation ($B)`, `Investors`, `investor_count`

### 3.3 `tests/test_api.py`

- [ ] Verificar que los payloads de prueba usan el esquema de `2_spec.md` (`year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`)
- [ ] Verificar que el endpoint `/predict` retorna `valuation_usd` y `valuation_b`

### 3.4 `tests/conftest.py`

- [ ] Revisar fixtures compartidas y actualizar columnas al esquema definitivo

### 3.5 Ejecutar suite completa

```bash
pytest tests/ -v
```

- [ ] Todos los tests pasan en verde antes de avanzar a Fase 4

---

## Fase 4 — Crear / Estabilizar la API FastAPI

### 4.1 Limpiar dependencias

- [ ] Actualizar `requirements.txt` con el listado de `2_spec.md` (añadir `fastapi`, `uvicorn`, `pydantic`, `httpx`, `psycopg2-binary`; eliminar `streamlit`, `kagglehub`)
- [ ] Ejecutar `pip install -r requirements.txt` y verificar que no hay conflictos

### 4.2 Definir Pydantic schemas en `app/input_schema.py`

- [ ] `PredictRequest`: campos `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`
- [ ] `PredictResponse`: campos `valuation_usd`, `valuation_b`, `model_version`, `timestamp`
- [ ] `FeedbackRequest`: extiende `PredictRequest` con `predicted_valuation_usd`, `actual_valuation_usd`, `comment`
- [ ] `FeedbackResponse`: campos `id`, `status`, `timestamp`

### 4.3 Implementar `app/main.py`

- [ ] Registrar routers para `/predict`, `/feedback`, `/health`, `/metrics`
- [ ] Configurar CORS para permitir el frontend en `localhost:5173`
- [ ] Eliminar cualquier referencia a Streamlit

### 4.4 Implementar `app/model_service.py`

- [ ] Carga lazy del modelo al arrancar la app (`@app.on_event("startup")`)
- [ ] Features de entrada: esquema definitivo de `2_spec.md`
- [ ] Sin mock: si el modelo no existe, la app no arranca y lanza error descriptivo

### 4.5 Configurar SQLAlchemy para PostgreSQL en `app/database.py`

- [ ] Leer `DATABASE_URL` exclusivamente desde `os.environ["DATABASE_URL"]`; si no existe, lanzar `RuntimeError` claro
- [ ] Crear engine con `create_engine(DATABASE_URL)` — sin `check_same_thread` (eso era SQLite)
- [ ] Definir `SessionLocal` y `Base` como de costumbre con SQLAlchemy ORM
- [ ] Crear un archivo `.env.example` en la raíz con:
  ```
  DATABASE_URL=postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
  ```
- [ ] Añadir `.env` al `.gitignore` (nunca versionar credenciales)

### 4.6 Implementar `app/feedback_service.py`

- [ ] Persistir cada predicción + feedback en la tabla `predictions` de PostgreSQL
- [ ] Usar la sesión de `app/database.py` (que ya lee `DATABASE_URL`)
- [ ] Verificar que no existe ninguna referencia a rutas de archivo SQLite (`storage/app.db`, `sqlite:///`)

### 4.7 Verificar modelo ORM en `app/database.py`

- [ ] El modelo `Prediction` (o equivalente) mapea la tabla `predictions` con los campos de `2_spec.md` sección 5
- [ ] `Base.metadata.create_all(engine)` se invoca en el startup para crear la tabla si no existe en PostgreSQL

### 4.8 Smoke test de la API (requiere PostgreSQL activo)

```bash
# Con Docker Compose (recomendado)
docker compose up db -d          # levantar sólo el servicio PostgreSQL
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

## Fase 5 — Frontend React

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
    build: .
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

## Fase 6 — Documentación y Cierre

### 6.1 Actualizar `README.md`

- [ ] Corregir árbol de directorios (eliminar `streamlit_app.py`, añadir `app/main.py` correcto)
- [ ] Corregir instrucciones de instalación: `requirements.txt` actualizado
- [ ] Corregir comandos de ejecución: `uvicorn` en lugar de `streamlit run`
- [ ] Corregir encoding: todos los caracteres especiales en UTF-8

### 6.2 Actualizar `docs/`

- [ ] `docs/app_usage.md`: instrucciones para la API FastAPI y el frontend React
- [ ] `docs/data_notes.md`: esquema definitivo de columnas de `2_spec.md`

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

## Checklist de Verificación Final

Antes de hacer merge a `main`:

- [ ] `git status` no muestra archivos `.joblib`, `.db`, `.sqlite3`, `.png` como tracked
- [ ] `pytest tests/ -v` — todos en verde, R² >= 0.50
- [ ] `docker compose up` levanta los tres servicios (`db`, `api`, `frontend`) sin errores
- [ ] `curl http://localhost:8000/health` devuelve `{"status": "ok", "model_loaded": true}`
- [ ] Frontend carga en `localhost:5173` y realiza una predicción exitosa
- [ ] `requirements.txt` contiene `psycopg2-binary` y no contiene `streamlit` ni `kagglehub`
- [ ] No existen referencias a `current_model.pkl`, `unicorn_valuation_pipeline.joblib`, `predictions.sqlite3`, `storage/app.db`, `sqlite:///` en ningún archivo `.py`
- [ ] No existen referencias a `Valuation ($B)`, `Investors`, `investor_count` en código de producción
- [ ] `config.yaml` tiene `min_r2: 0.50`, `model_file: models/best_model.joblib`, y NO tiene `storage_db`
- [ ] `DATABASE_URL` no está hardcodeada en ningún `.py`; sólo se lee de `os.environ`
