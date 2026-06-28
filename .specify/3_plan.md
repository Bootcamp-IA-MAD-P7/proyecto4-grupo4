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
| **Fase 6 — Documentación** | **▶ Pendiente** |
| Fase 7 — Optimización Post-MVP | 🧊 Congelada |
| Fase 8 — CI/CD y Despliegue EC2 | ▶ Pendiente |

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

## Fase 7 — Optimización Post-MVP: Múltiplo de Valoración 🧊 CONGELADA

> **Estado:** 🧊 congelada — no iniciar hasta completar el MVP funcional (Fases 4–6 y 8).
> **Decisión arquitectónica:** `backend/docs/architecture_decision_target.md` (ADR-001, 2026-06-25).
> **Tickets de ejecución:** `[T-7.1]`–`[T-7.6]` en `4_tasks.md`.
> **Prerequisito técnico:** MVP desplegado y estable en EC2 (Fase 8 completada).

### Problema diagnosticado (por qué el modelo no supera R² ≥ 0.50)

El modelo T1-T3 presenta heterocedasticidad estructural confirmada por el stress test post-Fase 4:

- **Pendiente residual:** +1.51 B USD por cada B USD predicho (ratio 5×)
- **Causa raíz 1 — piso unicornio:** 70–75% del dataset en $1B–$3B; el modelo converge al centroide y no extrae señal en la cola alta
- **Causa raíz 2 — escala absoluta del target:** `valuation_usd` tiene varianza condicional proporcional a su magnitud; ECM trata ambos extremos de forma simétrica, sesgando el aprendizaje

### Solución: target `multiple = valuation_usd / funding_usd`

Dividir por `funding_usd` elimina la escala operativa del negocio y normaliza la heterocedasticidad. El múltiplo es el "funding multiple" estándar en capital riesgo y tiene distribución más simétrica.

**Flujo de inferencia (la API no cambia):**

```
features (incluyendo funding_usd) → Pipeline ML → multiple_pred = expm1(predict)
                                   → valuation_usd_pred = multiple_pred × funding_usd
                                   → Response: { valuation_usd, valuation_b, ... }
```

### Archivos a modificar (en orden de ejecución)

| Ticket | Archivo | Responsabilidad |
|--------|---------|-----------------|
| `[T-7.2]` | `backend/config.yaml` | Añadir `target_transform: multiple` |
| `[T-7.3]` | `backend/src/models/train.py` | Cambiar target a `log1p(multiple)`, reconvertir en inferencia |
| `[T-7.4]` | `backend/app/model_service.py` | Pasar `funding_usd` al pipeline para reconversión |
| `[T-7.5]` | `backend/scripts/train.py` | Ajustar `enforce_quality_gate()` |
| `[T-7.6]` | `backend/tests/test_pipeline.py` | Actualizar umbral `test_train_meets_min_r2` |

### Criterios de aceptación (gate de Fase 7)

- [ ] R² validación ≥ 0.35 (objetivo mínimo para demo); ≥ 0.50 (gate CI que desbloquea merge a `main`)
- [ ] Pendiente del Residual Plot < ±0.5 B/B (reducción ≥ 66% del sesgo actual de +1.51)
- [ ] `POST /predict` devuelve el mismo esquema JSON de `2_spec.md §4` sin cambiar ninguna clave
- [ ] `test_train_meets_min_r2` pasa en verde
- [ ] `npm run build` del frontend pasa sin cambios (la API no cambia)

### Checklist de ejecución

- [ ] `[T-7.2]` — Añadir `target_transform: multiple` a `backend/config.yaml`
- [ ] `[T-7.3]` — Refactorizar `fit_model()` y añadir `predict_absolute()` en `backend/src/models/train.py`
- [ ] `[T-7.4]` — Actualizar `predict_valuation()` en `backend/app/model_service.py`
- [ ] `[T-7.5]` — Revisar `enforce_quality_gate()` en `backend/scripts/train.py`
- [ ] `[T-7.6]` — Actualizar umbral en `backend/tests/test_pipeline.py`
- [ ] Reentrenar: `cd backend && python scripts/train.py --report`
- [ ] Verificar R² y Residual Plot en `backend/models/metrics.json` y `backend/reports/residuals.png`
- [ ] Ejecutar suite completa: `cd backend && pytest tests/ -v`

---

## Fase 8 — CI/CD y Despliegue en EC2 (pendiente)

> **Estado:** pendiente — fase creada tras integración del workflow `.github/workflows/deployment.yml`.
> **Prerequisito:** Fase 6 (Documentación) completada para que el README y los docs sean correctos antes del primer deploy público.

### 8.1 Configurar secrets en GitHub

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

- [ ] Secrets creados en GitHub Actions environment `production`.

### 8.2 Verificar puertos en el servidor EC2

Puertos que deben estar **abiertos en el Security Group de AWS**:

| Puerto (host) | Uso | Estado |
|---------------|-----|--------|
| `8004` | API FastAPI (unicorn) | Confirmar apertura |
| `3005` | Frontend Nginx (unicorn) | Confirmar apertura |
| `22` | SSH | ✅ Abierto |
| `5434` | PostgreSQL externo (debug, opcional) | Confirmar si necesario |

> **Nota:** el puerto 5432 del host ya está ocupado por otra instancia PostgreSQL. El proyecto usa `5434` como puerto externo del contenedor (variable `POSTGRES_HOST_PORT`). Internamente los contenedores se comunican por el puerto estándar `5432`.

- [ ] Puertos `8004` y `3005` verificados abiertos en Security Group.

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

- [ ] Docker y Docker Compose instalados en EC2.
- [ ] Directorio `~/unicorn/` creado.

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

- [ ] Stack levantado manualmente y smoke test pasa.
- [ ] Verificar `http://EC2_PUBLIC_IP:3005` desde el navegador.

### 8.5 Activar pipeline CI/CD

- [ ] Hacer push a `main` con todos los cambios.
- [ ] Verificar que el job `test` pasa en GitHub Actions.
- [ ] Verificar que `build-and-push` sube imágenes a Docker Hub.
- [ ] Verificar que `deploy` actualiza el stack en EC2 sin downtime.
- [ ] Confirmar URL pública accesible desde el navegador.

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
