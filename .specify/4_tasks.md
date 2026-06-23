# Tasks — Backlog de Ejecución del Agente

> Generado desde `3_plan.md` y `2_spec.md` (revisión PostgreSQL).
> Contrato técnico de referencia permanente: `2_spec.md`.

**Estado del backlog (SDD):**

| Fase | Tickets | Estado |
|------|---------|--------|
| Fase 0 | `[T-0.1]`–`[T-0.3]` | ✅ Completados |
| Fase 1 | `[T-1.1]`–`[T-1.11]` | ✅ Completados |
| Fase 2 | `[T-2.0]`–`[T-2.9]` | ✅ Completados |
| Fases 3–6 | `[T-3.x]`–`[T-6.x]` | Bloqueadas |

---

## Protocolo de Ejecución del Agente

Antes de comenzar cualquier tarea:

1. **Leer** este archivo completo para entender el contexto de la fase en curso.
2. **Marcar `[~]`** (en progreso) la tarea que se va a ejecutar **antes** de tocar ningún archivo.
3. **Ejecutar** la tarea siguiendo exactamente las instrucciones del ticket.
4. **Marcar `[x]`** la tarea al confirmar que el cambio es correcto (archivo guardado, comando sin error, test en verde).
5. **Nunca marcar `[x]`** sin haber verificado el resultado. Un test fallido o un error de sintaxis invalidan el tick.
6. **Si una tarea bloquea**, marcar `[!]` y añadir una nota con el motivo antes de escalar.

**Leyenda de estados:**

| Símbolo | Significado                          |
|---------|--------------------------------------|
| `[ ]`   | Pendiente                            |
| `[~]`   | En progreso                          |
| `[x]`   | Completada y verificada              |
| `[!]`   | Bloqueada — requiere intervención    |
| `[-]`   | Cancelada / no aplica                |

---

## Fase 0 — Preparación ✅ COMPLETADA

> **Estado:** tickets `[T-0.1]` a `[T-0.3]` verificados y cerrados.

### [T-0.1] Crear rama de trabajo

- **Archivo(s):** ninguno (operación Git)
- **Comando:**
  ```bash
  git checkout main && git pull origin main
  git checkout -b refactor/stabilize-architecture
  ```
- **Verificación:** `git branch --show-current` devuelve `refactor/stabilize-architecture`.
- [x] Estado: completado — rama `refactor/stabilize-architecture` creada desde `main`

---

### [T-0.2] Capturar baseline de tests

- **Archivo(s):** ninguno (sólo lectura)
- **Comando:**
  ```bash
  pytest tests/ -v 2>&1 | tee /tmp/test_baseline.txt
  cat /tmp/test_baseline.txt
  ```
- **Verificación:** Registrar cuántos tests pasan y cuántos fallan. Este número es el punto de partida; al finalizar la refactorización todos deben pasar.
- [x] Estado: completado — BASELINE: 0 tests pasados, 2 errores de colección (`ModuleNotFoundError: sklearn` en `test_preprocessing.py`; `ImportError: UTC` en `test_api.py`). Entorno sin venv activo.

---

### [T-0.3] Guardar snapshot de métricas actuales

- **Archivo(s):** `models/metrics.json` (solo lectura)
- **Acción:** Leer y anotar el valor de `validation.r2` actual (`0.176`). Confirmar que el modelo actual **no** cumpliría el umbral de CI (`>= 0.50`). No modificar nada.
- **Verificación:** El valor está documentado en `2_spec.md` sección 3.
- [x] Estado: completado — SNAPSHOT: `validation.r2=0.1763`, `train.r2=0.1739`, `cv_r2_mean=0.2442`. El modelo actual NO pasa CI (< 0.50). Confirma diagnóstico de `2_spec.md`.

---

## Fase 1 — Limpieza de Artefactos y Duplicados ✅ COMPLETADA

> **Estado:** tickets `[T-1.1]` a `[T-1.11]` verificados y cerrados. No revertir estos cambios.

### [T-1.1] Sacar artefactos binarios del índice Git

- **Archivo(s):** índice Git (no toca contenido de archivos)
- **Comando:**
  ```bash
  git rm --cached models/best_model.joblib
  git rm --cached models/unicorn_valuation_pipeline.joblib
  git rm --cached models/metrics.json
  git rm --cached storage/app.db
  git rm --cached data/feedback/predictions.sqlite3
  git rm --cached reports/feature_importance.png reports/pred_vs_actual.png \
                  reports/residuals.png reports/target_distribution.png
  git rm --cached data/dataset_clean.csv
  ```
- **Nota:** Si algún archivo no está en el índice, git rm mostrará un error no fatal; continuar igualmente.
- **Verificación:** `git status` muestra esos archivos como `Untracked files`, no como `Changes to be committed`.
- [x] Estado: completado — 10 artefactos removidos del índice (`best_model.joblib`, `unicorn_valuation_pipeline.joblib`, `metrics.json`, `app.db`, `predictions.sqlite3`, 4×PNG, `dataset_clean.csv`). Archivos permanecen en disco como `??` untracked.

---

### [T-1.2] Actualizar `.gitignore` con todas las exclusiones

- **Archivo(s):** `.gitignore`
- **Acción:** Añadir al final del archivo el siguiente bloque (sin borrar el contenido existente):
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
- **Verificación:** `git status` no muestra los artefactos listados como tracked.
- [x] Estado: completado — Bloque de exclusiones añadido. Los artefactos ya no aparecen como `??` untracked; solo como `D` (staged deletions del paso T-1.1).

---

### [T-1.3] Eliminar dataset duplicado en `notebooks/`

- **Archivo(s):** `notebooks/data/raw/dataset_raw.csv`
- **Acción:** Borrar el archivo y las carpetas vacías que queden.
- **Comando:**
  ```bash
  rm notebooks/data/raw/dataset_raw.csv
  rmdir --ignore-fail-on-non-empty notebooks/data/raw
  rmdir --ignore-fail-on-non-empty notebooks/data
  ```
- **Verificación:** `ls notebooks/` no muestra carpeta `data/`.
- [x] Estado: completado — `notebooks/data/raw/dataset_raw.csv` eliminado. Carpeta `notebooks/data/` eliminada.

---

### [T-1.4] Eliminar `data/raw/dataset_raw.csv`

- **Archivo(s):** `data/raw/dataset_raw.csv`
- **Acción:** Borrar el archivo. El dataset canónico es `data/raw/unicorn_companies.csv`.
- **Comando:**
  ```bash
  rm data/raw/dataset_raw.csv
  ```
- **Verificación:** `ls data/raw/` muestra sólo `unicorn_companies.csv` y `.gitkeep`.
- [x] Estado: completado — `data/raw/` contiene únicamente `unicorn_companies.csv`.

---

### [T-1.5] Eliminar `data/dataset_clean.csv` (raíz de `data/`)

- **Archivo(s):** `data/dataset_clean.csv`
- **Acción:** Borrar el archivo.
- **Comando:**
  ```bash
  rm data/dataset_clean.csv
  ```
- **Verificación:** `ls data/` no muestra `dataset_clean.csv`.
- [x] Estado: completado — `data/dataset_clean.csv` eliminado.

---

### [T-1.6] Eliminar archivo BACKUP en `src/data/`

- **Archivo(s):** `src/data/__init___BACKUP.py`
- **Acción:** Borrar el archivo.
- **Comando:**
  ```bash
  rm src/data/__init___BACKUP.py
  ```
- **Verificación:** `ls src/data/` no muestra ningún `*BACKUP*`.
- [x] Estado: completado — `src/data/__init___BACKUP.py` eliminado.

---

### [T-1.7] Eliminar notebook BACKUP

- **Archivo(s):** `notebooks/01_eda_BACKUP.ipynb`
- **Acción:** Borrar el archivo.
- **Comando:**
  ```bash
  rm notebooks/01_eda_BACKUP.ipynb
  ```
- **Verificación:** `ls notebooks/` no muestra `*BACKUP*`.
- [x] Estado: completado — `notebooks/01_eda_BACKUP.ipynb` eliminado.

---

### [T-1.8] Eliminar `app/streamlit_app.py`

- **Archivo(s):** `app/streamlit_app.py`
- **Acción:** Borrar el archivo. Streamlit está eliminado del stack por diseño (`2_spec.md` sección 7).
- **Comando:**
  ```bash
  rm app/streamlit_app.py
  grep -r "streamlit" app/ src/ scripts/ --include="*.py"
  ```
- **Verificación:** El grep no devuelve resultados.
- [x] Estado: completado — `app/streamlit_app.py` eliminado. Nota: `src/storage/db.py` tiene `default="streamlit"` como literal de string (no import); se corrige en Fase 2.

---

### [T-1.9] Fusionar `src/data/load_data.py` en `src/data/load.py`

- **Archivo(s):** `src/data/load_data.py`, `src/data/load.py`
- **Acción:**
  1. Leer ambos archivos e identificar funciones únicas en `load_data.py` no presentes en `load.py`.
  2. Mover esas funciones a `load.py` y actualizar todos los imports que usen `load_data`.
  3. Eliminar `load_data.py`.
- **Comando de búsqueda:**
  ```bash
  grep -r "from src.data.load_data\|import load_data" --include="*.py" .
  ```
- **Verificación:** `grep -r "load_data" --include="*.py" .` no devuelve resultados en código de producción.
- [x] Estado: completado — `load_data.py` usaba `kagglehub` (eliminado) y `save_raw()` a `dataset_raw.csv` (eliminado). Funciones completamente obsoletas; ninguna migrada a `load.py` (ya tiene equivalentes). `scripts/run_eda.py` actualizado para cargar desde `data/raw/unicorn_companies.csv` directamente. Zero referencias a `load_data` en el codebase.

---

### [T-1.10] Eliminar TODAS las bases de datos SQLite

- **Archivo(s):** `data/feedback/predictions.sqlite3`, `storage/app.db`
- **Acción:** Borrar ambos archivos. La arquitectura de producción usa PostgreSQL; no existe ningún archivo `.db` o `.sqlite3` válido.
- **Comando:**
  ```bash
  rm -f data/feedback/predictions.sqlite3
  rm -f storage/app.db
  ```
- **Verificación:**
  ```bash
  find . -name "*.sqlite3" -o -name "*.db" | grep -v ".git"
  ```
  No debe devolver ningún resultado.
- [x] Estado: completado — Ambas bases SQLite eliminadas del disco. `find` no devuelve ningún `.db` ni `.sqlite3`.

---

### [T-1.11] Eliminar `models/unicorn_valuation_pipeline.joblib`

- **Archivo(s):** `models/unicorn_valuation_pipeline.joblib`
- **Acción:** Borrar el archivo. La ruta canónica del modelo es `models/best_model.joblib`.
- **Comando:**
  ```bash
  rm models/unicorn_valuation_pipeline.joblib
  ```
- **Verificación:** `ls models/` muestra sólo `best_model.joblib`, `metrics.json`, `.gitkeep`.
- [x] Estado: completado — `unicorn_valuation_pipeline.joblib` eliminado. `models/` contiene sólo `best_model.joblib` y `metrics.json`.

---

## Fase 2 — Unificar Rutas y Configuración ▶ FASE ACTIVA

> **Prerequisito:** `[T-2.0]` completado (reestructuración a monorepo).
> **Esta es la única fase en ejecución.** Todas las rutas de archivos son relativas a `backend/` (cwd del servicio `api`).
> **Siguiente bloque acordado:** Fase 3 — `[T-3.1]` (tests y umbrales).

### [T-2.0] Reestructurar carpetas — mover código backend a `/backend/`

- **Archivo(s):** estructura de directorios en la raíz del repo
- **Acción:**
  1. Crear `backend/` y mover con `git mv` (preserva historial):
     ```bash
     mkdir -p backend
     git mv app src scripts models storage tests config.yaml backend/
     git mv requirements.txt Dockerfile data notebooks docs README.md backend/
     ```
  2. Actualizar `docker-compose.yml` en la raíz:
     - Cambiar `build: .` → `build: ./backend` en el servicio `api`
     - Eliminar volúmenes y puertos legacy de Streamlit (`8501`, `./storage:/app/storage`, etc.)
     - Mantener `command: uvicorn app.main:app --host 0.0.0.0 --port 8000`
  3. Actualizar `backend/Dockerfile`:
     - Eliminar referencias a Streamlit (`8501`, `streamlit run`)
     - `EXPOSE 8000` y `CMD` con uvicorn
  4. Verificar imports Python desde el nuevo cwd:
     ```bash
     cd backend
     python -c "from app.main import app; print('OK')"
     pytest tests/ -v --collect-only
     ```
  5. Buscar imports rotos:
     ```bash
     grep -rn "from app\|from src\|import app\|import src" backend/ --include="*.py"
     ```
     Todos deben resolver con cwd `backend/`. Corregir cualquier path absoluto que apunte a la raíz antigua.
  6. Confirmar que `backend/config.yaml` mantiene rutas relativas a `backend/` (`models/best_model.joblib`, `data/processed/dataset.parquet`).
- **Verificación:**
  ```bash
  # Raíz limpia — sólo estos elementos
  ls -1
  # → backend  frontend  .specify  .github  docker-compose.yml  .gitignore

  # Backend completo
  ls backend/
  # → app src scripts models storage tests config.yaml requirements.txt Dockerfile data notebooks docs README.md

  # Docker Compose válido
  docker compose config

  # Imports Python OK
  cd backend && python -c "from app.main import app; print('OK')"
  ```
- **Nota:** No revertir ningún cambio de Fase 1. `frontend/` permanece en su ubicación actual. No mover `.specify/`, `.github/`, `docker-compose.yml` ni `.gitignore`.
- [x] Estado: completado — Código backend movido a `backend/` con `git mv`. `docker-compose.yml` actualizado: servicio `api` con `build: ./backend`, puerto `8000`, comando uvicorn; eliminados volúmenes/puertos Streamlit legacy. `backend/Dockerfile` expone `8000` y arranca con uvicorn. Imports verificados desde `backend/` (`from app.main import app` → OK; `pytest tests/ -v --collect-only` → 20 tests). Uvicorn arranca correctamente. `config.yaml` mantiene rutas relativas a `backend/`.

---

### [T-2.1] Corregir `backend/config.yaml` — ruta del modelo

- **Archivo(s):** `backend/config.yaml`
- **Acción:** Cambiar en la sección `paths`:
  ```yaml
  # Antes:
  model_file: "models/unicorn_valuation_pipeline.joblib"
  # Después:
  model_file: "models/best_model.joblib"
  ```
- **Verificación:** `grep "model_file" backend/config.yaml` devuelve `models/best_model.joblib`.
- [x] Estado: completado — `model_file` apunta a `models/best_model.joblib`.

---

### [T-2.2] Eliminar `paths.storage_db` de `backend/config.yaml`

- **Archivo(s):** `backend/config.yaml`
- **Acción:** Eliminar la clave `storage_db` de la sección `paths`. La conexión a PostgreSQL viene de `DATABASE_URL` (variable de entorno), no de `config.yaml`.
- **Verificación:** `grep "storage_db" backend/config.yaml` no devuelve resultados.
- [x] Estado: completado — clave `storage_db` eliminada; PostgreSQL vía `DATABASE_URL`.

---

### [T-2.3] Verificar `backend/config.yaml` — ruta de datos procesados y umbral R²

- **Archivo(s):** `backend/config.yaml`
- **Acción:** Confirmar que:
  - `paths.processed_data: "data/processed/dataset.parquet"` ✓
  - `training.min_r2: 0.5` ✓
- **Verificación:** `grep -E "processed_data|min_r2" backend/config.yaml` muestra ambos valores correctos.
- [x] Estado: completado — `processed_data: data/processed/dataset.parquet`, `min_r2: 0.5` confirmados.

---

### [T-2.4] Corregir `backend/app/model_service.py` — ruta del modelo

- **Archivo(s):** `backend/app/model_service.py`
- **Acción:**
  ```python
  # Antes:
  MODEL_PATH = os.getenv("MODEL_PATH", "models/current_model.pkl")
  # Después:
  MODEL_PATH = os.getenv("MODEL_PATH", "models/best_model.joblib")
  ```
- **Verificación:** `grep "\.pkl\|current_model" backend/app/model_service.py` no devuelve resultados.
- [x] Estado: completado — `MODEL_PATH` default `models/best_model.joblib` vía `os.getenv`.

---

### [T-2.5] Corregir `backend/app/model_service.py` — features de entrada

- **Archivo(s):** `backend/app/model_service.py`
- **Acción:** Sustituir el listado de features legacy por el esquema definitivo de `2_spec.md`:
  - **Eliminar:** `city`, `join_year`, `join_month`, `investor_count`
  - **Usar:** `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`
- **Verificación:** `grep -E "city|join_year|join_month|investor_count" backend/app/model_service.py` no devuelve resultados.
- [x] Estado: completado — features definitivas: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`.

---

### [T-2.6] Corregir `backend/app/model_service.py` — eliminar mock de predicción

- **Archivo(s):** `backend/app/model_service.py`
- **Acción:** Reemplazar el bloque de fallback/mock por una excepción HTTP 503:
  ```python
  if model is None:
      raise HTTPException(status_code=503, detail="Model not loaded. Run scripts/train.py first.")
  ```
- **Verificación:** `grep -i "mock\|heuristic\|fallback" backend/app/model_service.py` no devuelve resultados.
- [x] Estado: completado — fallback mock eliminado; `HTTPException(503)` si el modelo no está cargado.

---

### [T-2.7] Corregir `backend/scripts/train.py` — ruta de guardado del modelo

- **Archivo(s):** `backend/scripts/train.py`
- **Acción:** El modelo se serializa usando la ruta de `config.yaml`:
  ```python
  joblib.dump(pipeline, cfg["paths"]["model_file"])
  # → guarda en models/best_model.joblib
  ```
- **Verificación:** `grep "unicorn_valuation\|\.pkl" backend/scripts/train.py` no devuelve resultados.
- [x] Estado: completado — `save_artifacts` serializa vía `cfg["paths"]["model_file"]` → `models/best_model.joblib`.

---

### [T-2.8] Añadir gate de R² en `backend/scripts/train.py`

- **Archivo(s):** `backend/scripts/train.py`
- **Acción:** Después de calcular métricas de validación, añadir:
  ```python
  import sys
  min_r2 = cfg["training"]["min_r2"]
  val_r2 = metrics["validation"]["r2"]
  if val_r2 < min_r2:
      print(f"[FAIL] R²={val_r2:.4f} < threshold {min_r2}. Training rejected.")
      sys.exit(1)
  print(f"[OK] R²={val_r2:.4f} >= threshold {min_r2}. Model saved.")
  ```
- **Verificación:** Ejecutar `cd backend && python scripts/train.py` con el modelo actual — debe imprimir `[FAIL]` y salir con código 1 (`echo $?` → `1`).
- [x] Estado: completado — `enforce_quality_gate()` rechaza R² < 0.5 con `sys.exit(1)` antes de `save_artifacts`.

---

### [T-2.9] Deprecar `backend/src/preprocessing/preprocessing_pipeline.py`

- **Archivo(s):** `backend/src/preprocessing/preprocessing_pipeline.py`
- **Acción:**
  1. Ejecutar `grep -r "preprocessing_pipeline\|from src.preprocessing" --include="*.py" backend/`
  2. Si sólo lo usan notebooks, añadir comentario de deprecación al inicio del módulo.
  3. Si lo usa código de producción (`backend/app/`, `backend/scripts/`, `backend/src/models/`), migrar esas referencias a `backend/src/data/load.py` y luego eliminar el archivo.
- **Verificación:** Ningún archivo en `backend/app/`, `backend/src/models/`, `backend/scripts/` importa `preprocessing_pipeline`.
- [x] Estado: completado — módulo deprecado; producción usa `src.data.load` + parquet `data/processed/dataset.parquet`.

---

## Fase 3 — Corregir Tests y Umbrales (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 2.

### [T-3.1] Corregir umbral de R² en `backend/tests/test_pipeline.py`

- **Archivo(s):** `backend/tests/test_pipeline.py`
- **Acción:**
  ```python
  # Antes:
  assert r2 >= 0.15
  # Después:
  assert r2 >= 0.50, f"R² {r2:.4f} is below the required threshold of 0.50"
  ```
- **Verificación:** `grep "0\.15" backend/tests/test_pipeline.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-3.2] Actualizar fixtures de columnas en `backend/tests/test_pipeline.py`

- **Archivo(s):** `backend/tests/test_pipeline.py`
- **Acción:** Reemplazar columnas legacy en fixtures o DataFrames de prueba por el esquema de `2_spec.md`: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`, `valuation_usd`.
- **Verificación:** `grep -E "Valuation \(\\\$B\)|Investors|investor_count" backend/tests/test_pipeline.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-3.3] Verificar ruta del modelo en `backend/tests/test_pipeline.py`

- **Archivo(s):** `backend/tests/test_pipeline.py`
- **Acción:** Confirmar que el test carga el modelo desde `models/best_model.joblib`.
- **Verificación:** `grep -E "\.pkl|unicorn_valuation" backend/tests/test_pipeline.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-3.4] Actualizar fixtures en `backend/tests/test_preprocessing.py`

- **Archivo(s):** `backend/tests/test_preprocessing.py`
- **Acción:** Sustituir columnas legacy en todos los DataFrames de prueba por el esquema de `2_spec.md`.
- **Verificación:** `grep -E "Valuation|Investors|investor_count" backend/tests/test_preprocessing.py` no devuelve resultados en fixtures.
- [ ] Estado: pendiente

---

### [T-3.5] Actualizar payloads en `backend/tests/test_api.py`

- **Archivo(s):** `backend/tests/test_api.py`
- **Acción:** Los payloads de `POST /predict` y `POST /feedback` deben usar:
  ```python
  payload = {
      "year_founded": 2015,
      "funding_usd": 50_000_000.0,
      "company_age": 9,
      "industry": "fintech",
      "country": "United States",
      "continent": "North America"
  }
  ```
  El assert sobre la respuesta debe verificar `valuation_usd` y `valuation_b`.
- **Verificación:** `grep -E "city|join_year|join_month|investor_count" backend/tests/test_api.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-3.6] Revisar y actualizar `backend/tests/conftest.py`

- **Archivo(s):** `backend/tests/conftest.py`
- **Acción:** Leer el archivo. Actualizar fixtures con columnas legacy al esquema definitivo. Cambiar ruta del modelo si aparece.
- **Verificación:** `grep -E "\.pkl|unicorn_valuation|Valuation \(\\\$B\)" backend/tests/conftest.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-3.7] Ejecutar suite de tests completa y verificar verde

- **Archivo(s):** ninguno (ejecución)
- **Comando:**
  ```bash
  cd backend && pytest tests/ -v
  ```
- **Verificación:** Todos los tests pasan. Si alguno falla, marcar `[!]` y **no avanzar** a Fase 4.
- [ ] Estado: pendiente

---

## Fase 4 — Estabilizar la API FastAPI + PostgreSQL (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 3.

### [T-4.1] Actualizar `backend/requirements.txt`

- **Archivo(s):** `backend/requirements.txt`
- **Acción:** Reemplazar el contenido completo con el listado canónico de `2_spec.md` sección 6:
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
- **Verificación:** `grep -E "streamlit|kagglehub" backend/requirements.txt` no devuelve resultados. `grep "psycopg2" backend/requirements.txt` devuelve la línea correcta.
- [ ] Estado: pendiente

---

### [T-4.2] Instalar dependencias actualizadas

- **Archivo(s):** ninguno (entorno)
- **Comando:**
  ```bash
  cd backend && pip install -r requirements.txt
  ```
- **Verificación:** Sin errores de conflicto. `python -c "import fastapi, pydantic, uvicorn, psycopg2"` no lanza `ImportError`.
- [ ] Estado: pendiente

---

### [T-4.3] Definir schemas Pydantic en `backend/app/input_schema.py`

- **Archivo(s):** `backend/app/input_schema.py`
- **Acción:** Asegurarse de que el archivo define exactamente estas clases:
  - `PredictRequest`: `year_founded: int`, `funding_usd: float`, `company_age: int`, `industry: str`, `country: str`, `continent: str`
  - `PredictResponse`: `valuation_usd: float`, `valuation_b: float`, `model_version: str`, `timestamp: str`
  - `FeedbackRequest`: hereda `PredictRequest` + `predicted_valuation_usd: float`, `actual_valuation_usd: float | None`, `comment: str | None`
  - `FeedbackResponse`: `id: int`, `status: str`, `timestamp: str`
- **Verificación:**
  ```bash
  cd backend && python -c "from app.input_schema import PredictRequest, PredictResponse, FeedbackRequest, FeedbackResponse; print('OK')"
  ```
  Imprime `OK`.
- [ ] Estado: pendiente

---

### [T-4.4] Implementar endpoints en `backend/app/main.py`

- **Archivo(s):** `backend/app/main.py`
- **Acción:** Verificar y corregir que el archivo registra los cuatro endpoints del contrato (`2_spec.md` sección 4):
  - `POST /predict`
  - `POST /feedback`
  - `GET /health`
  - `GET /metrics`
  - CORS habilitado para `http://localhost:5173`
  - Sin ninguna referencia a Streamlit
- **Verificación:** `grep -i "streamlit" backend/app/main.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-4.5] Configurar SQLAlchemy para PostgreSQL en `backend/app/database.py`

- **Archivo(s):** `backend/app/database.py`
- **Acción:**
  1. Leer `DATABASE_URL` desde `os.environ["DATABASE_URL"]`; si no existe, lanzar `RuntimeError("DATABASE_URL environment variable is not set")`.
  2. Crear engine: `engine = create_engine(DATABASE_URL)` (sin parámetros SQLite como `check_same_thread`).
  3. Definir `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`.
  4. Definir `Base = declarative_base()`.
  5. Ninguna referencia a `sqlite:///` ni a `storage/app.db`.
- **Verificación:** `grep -E "sqlite|storage/app" backend/app/database.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-4.6] Crear `backend/.env.example`

- **Archivo(s):** `backend/.env.example` (crear si no existe)
- **Acción:** Crear el archivo con el siguiente contenido:
  ```
  # Copy this file to .env and fill in your values
  DATABASE_URL=postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
  ```
- **Verificación:** El archivo existe. `grep "DATABASE_URL" backend/.env.example` devuelve la línea de ejemplo.
- [ ] Estado: pendiente

---

### [T-4.7] Implementar `backend/app/feedback_service.py` — persistencia en PostgreSQL

- **Archivo(s):** `backend/app/feedback_service.py`
- **Acción:**
  - Usar la sesión de `backend/app/database.py` para persistir registros en la tabla `predictions`.
  - Ninguna referencia a rutas de archivo SQLite (`backend/storage/app.db`, `sqlite:///`).
- **Verificación:** `grep -E "sqlite|storage/app|data/feedback" backend/app/feedback_service.py` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-4.8] Verificar modelo ORM en `backend/app/database.py`

- **Archivo(s):** `backend/app/database.py`
- **Acción:** Confirmar que el modelo `Prediction` (o equivalente) mapea la tabla `predictions` con todos los campos de `2_spec.md` sección 5. Confirmar que `Base.metadata.create_all(engine)` se invoca en el startup para crear la tabla si no existe en PostgreSQL.
- **Verificación:** `cd backend && DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns python -c "from app.database import Base, engine; Base.metadata.create_all(engine); print('OK')"` imprime `OK` (requiere `DATABASE_URL` activa).
- [ ] Estado: pendiente

---

### [T-4.9] Verificar carga del modelo al startup en `app/model_service.py`

- **Archivo(s):** `app/model_service.py`
- **Acción:** Confirmar que el modelo se carga una sola vez al arrancar la aplicación (usando `lifespan` o `@app.on_event("startup")`). Si no hay modelo en `models/best_model.joblib`, lanzar `RuntimeError` descriptivo.
- **Verificación:** Al lanzar sin el archivo del modelo, la app falla con mensaje claro (no silencia el error).
- [ ] Estado: pendiente

---

### [T-4.10] Smoke test de la API (requiere servicio `db` activo)

- **Archivo(s):** ninguno (ejecución)
- **Comando:**
  ```bash
  # Levantar PostgreSQL
  docker compose up db -d
  sleep 5

  # Lanzar API apuntando al PostgreSQL dockerizado
  cd backend
  DATABASE_URL=postgresql://unicorn_user:unicorn_pass@localhost:5432/unicorns \
    uvicorn app.main:app --reload &
  sleep 3

  # Probar endpoint predict
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,"industry":"fintech","country":"United States","continent":"North America"}'

  # Probar health
  curl -s http://localhost:8000/health
  ```
- **Verificación:** Respuesta de `/predict` contiene `valuation_usd` (número). Respuesta de `/health` contiene `"status":"ok"`.
- [ ] Estado: pendiente

---

## Fase 5 — Frontend React + Docker Compose (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 4.

### [T-5.1] Verificar `frontend/src/api.js` — BASE_URL y payloads

- **Archivo(s):** `frontend/src/api.js`
- **Acción:**
  - Confirmar que `BASE_URL` es `http://localhost:8000` (o configurable vía `.env`).
  - La función `predict()` envía: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`.
  - Existe `submitFeedback()` apuntando a `POST /feedback`.
  - Eliminar campos legacy: `city`, `join_year`, `join_month`, `investor_count`.
- **Verificación:** `grep -E "city|join_year|join_month|investor_count" frontend/src/api.js` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-5.2] Reemplazar métricas hardcodeadas en `frontend/src/data/modelMetrics.js`

- **Archivo(s):** `frontend/src/data/modelMetrics.js`
- **Acción:** Eliminar el objeto de métricas estático. Exportar una función `fetchMetrics()` que llame a `GET /metrics`:
  ```js
  export async function fetchMetrics() {
    const res = await fetch(`${BASE_URL}/metrics`);
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return res.json();
  }
  ```
  Actualizar los componentes que consuman este módulo para llamar `fetchMetrics()` en un `useEffect`.
- **Verificación:** `grep -E "r2.*0\.|mae.*[0-9]{8}" frontend/src/data/modelMetrics.js` no devuelve valores hardcodeados.
- [ ] Estado: pendiente

---

### [T-5.3] Actualizar campos en `frontend/src/components/PredictionForm.jsx`

- **Archivo(s):** `frontend/src/components/PredictionForm.jsx`
- **Acción:** Los campos del formulario deben ser exactamente: `year_founded`, `funding_usd`, `company_age`, `industry`, `country`, `continent`. Eliminar: `city`, `join_year`, `join_month`, `investor_count`.
- **Verificación:** `grep -E "city|join_year|join_month|investor_count" frontend/src/components/PredictionForm.jsx` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-5.4] Actualizar `frontend/src/components/PredictionResult.jsx`

- **Archivo(s):** `frontend/src/components/PredictionResult.jsx`
- **Acción:**
  - Mostrar `valuation_b` como `$X.XXB` y `valuation_usd` como cifra completa.
  - Corregir mojibake: buscar y reemplazar `PredicciÃ³n` → `Predicción`, `RÂ²` → `R²`.
- **Comando de detección:**
  ```bash
  grep -n "Ã\|Â" frontend/src/components/PredictionResult.jsx
  ```
- **Verificación:** El comando anterior no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-5.5] Búsqueda y corrección global de mojibake

- **Archivo(s):** todos los `.py`, `.md`, `.jsx`, `.js`, `.yaml`
- **Acción:** Ejecutar y corregir cada ocurrencia:
  ```bash
  grep -rn "Ã\|Â" --include="*.py" --include="*.md" \
                   --include="*.jsx" --include="*.js" --include="*.yaml" .
  ```
  Reemplazos comunes: `PredicciÃ³n` → `Predicción`, `RÂ²` → `R²`, `valoraciÃ³n` → `valoración`.
- **Verificación:** El comando de búsqueda no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-5.6] Crear Dockerfile multi-stage para el frontend (Node build + Nginx)

- **Archivo(s):** `frontend/Dockerfile` (crear o reescribir)
- **Acción:** El frontend usa un Dockerfile multi-stage: la primera etapa usa Node para compilar los estáticos con Vite, y la segunda etapa usa Nginx (Alpine) para servirlos en el puerto 80. Esto produce una imagen final ligera sin Node en producción.
  ```dockerfile
  # ── Stage 1: Build ──────────────────────────────────────────────
  FROM node:20-alpine AS builder
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci --omit=dev
  COPY . .
  RUN npm run build

  # ── Stage 2: Serve ──────────────────────────────────────────────
  FROM nginx:1.27-alpine AS runner
  COPY --from=builder /app/dist /usr/share/nginx/html
  # Ruta de configuración de nginx para SPA (react-router)
  COPY nginx.conf /etc/nginx/conf.d/default.conf
  EXPOSE 80
  CMD ["nginx", "-g", "daemon off;"]
  ```
- **Archivo adicional:** `frontend/nginx.conf` con soporte SPA (redirige 404 → index.html):
  ```nginx
  server {
      listen 80;
      root /usr/share/nginx/html;
      index index.html;
      location / {
          try_files $uri $uri/ /index.html;
      }
  }
  ```
- **Verificación:**
  ```bash
  docker build -t unicorn-frontend ./frontend
  docker run --rm -p 5173:80 unicorn-frontend &
  sleep 2 && curl -s http://localhost:5173 | grep -c "<!DOCTYPE html"
  ```
  Devuelve `1` (el HTML se sirve correctamente).
- [ ] Estado: pendiente

---

### [T-5.7] Escribir `docker-compose.yml` con healthcheck y depends_on condicional

- **Archivo(s):** `docker-compose.yml`
- **Acción:** Reemplazar el contenido completo del archivo con la versión de producción que incluye `healthcheck` en `db` y `condition: service_healthy` en `api`. Esto garantiza que la API no arranca hasta que PostgreSQL esté realmente listo para aceptar conexiones (crítico en EC2 donde el pull de la imagen puede ser lento).
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
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U unicorn_user -d unicorns"]
        interval: 10s
        timeout: 5s
        retries: 5
        start_period: 10s

    api:
      build: ./backend
      restart: unless-stopped
      ports:
        - "8000:8000"
      environment:
        DATABASE_URL: postgresql://unicorn_user:unicorn_pass@db:5432/unicorns
      depends_on:
        db:
          condition: service_healthy
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
- **Verificación:**
  ```bash
  docker compose config                    # sin errores de sintaxis
  grep -i "streamlit" docker-compose.yml  # sin resultados
  grep "service_healthy" docker-compose.yml  # aparece en api.depends_on
  grep "pg_isready" docker-compose.yml    # aparece en db.healthcheck
  ```
- [ ] Estado: pendiente

---

### [T-5.8] Smoke test completo con Docker Compose

- **Archivo(s):** ninguno (ejecución)
- **Comando:**
  ```bash
  docker compose up --build -d
  sleep 10  # esperar a que PostgreSQL esté listo y la API arranque
  docker compose ps  # todos en estado "running"
  curl -s http://localhost:8000/health
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"year_founded":2015,"funding_usd":50000000,"company_age":9,"industry":"fintech","country":"United States","continent":"North America"}'
  ```
- **Verificación:** Los tres contenedores están en estado `running`. `/health` devuelve `"status":"ok"`. `/predict` devuelve `valuation_usd` numérico.
- [ ] Estado: pendiente

---

## Fase 6 — Documentación y Cierre (pendiente)

> **Estado:** bloqueada — no iniciar hasta completar Fase 5.

### [T-6.1] Actualizar árbol de directorios en `backend/README.md`

- **Archivo(s):** `backend/README.md`
- **Acción:**
  - Eliminar `streamlit_app.py` del árbol.
  - Documentar estructura monorepo: raíz con `backend/` + `frontend/`.
  - Reemplazar `best_model.joblib` en el árbol con una nota `(generado por scripts/train.py, no versionado)`.
  - Corregir `dataset_raw.csv` → `unicorn_companies.csv`.
  - Eliminar referencias a `storage/app.db` como archivo local.
  - Corregir encoding mojibake en todo el archivo.
- **Verificación:** `grep -E "streamlit|dataset_raw|storage/app.db|Ã|Â" backend/README.md` no devuelve resultados problemáticos.
- [ ] Estado: pendiente

---

### [T-6.2] Actualizar instrucciones de ejecución en `backend/README.md`

- **Archivo(s):** `backend/README.md`
- **Acción:**
  - Setup: `pip install -r backend/requirements.txt`
  - Ejecución: `docker compose up --build` (desde la raíz) o `cd backend && uvicorn app.main:app --reload` (desarrollo local, requiere `DATABASE_URL` activo)
  - Frontend: `cd frontend && npm install && npm run dev`
  - Eliminar cualquier `streamlit run`
- **Verificación:** `grep -i "streamlit run" backend/README.md` no devuelve resultados.
- [ ] Estado: pendiente

---

### [T-6.3] Actualizar `backend/docs/app_usage.md`

- **Archivo(s):** `backend/docs/app_usage.md`
- **Acción:** Reescribir con instrucciones para:
  1. Levantar el stack: `docker compose up --build`
  2. Endpoints: `POST /predict`, `POST /feedback`, `GET /health`, `GET /metrics`
  3. Ejemplo curl de `/predict` con el payload de `2_spec.md`
  4. Desarrollo local del frontend: `cd frontend && npm run dev`
- **Verificación:** El archivo no menciona Streamlit ni SQLite.
- [ ] Estado: pendiente

---

### [T-6.4] Actualizar `backend/docs/data_notes.md`

- **Archivo(s):** `backend/docs/data_notes.md`
- **Acción:** Añadir o reemplazar la sección de esquema de columnas con la tabla de `2_spec.md` sección 1. Mencionar la ruta canónica del dataset (`backend/data/raw/unicorn_companies.csv`) y la DB de producción (PostgreSQL vía `DATABASE_URL`).
- **Verificación:** El documento no menciona columnas obsoletas como `Valuation ($B)` en posición de fuente de verdad.
- [ ] Estado: pendiente

---

### [T-6.5] Commit final de refactorización

- **Archivo(s):** todos los archivos modificados
- **Comando:**
  ```bash
  git add -A
  git status  # revisar que NO hay artefactos binarios staged
  git commit -m "refactor: stabilize architecture — PostgreSQL, unified schema, FastAPI, clean Git"
  git push origin refactor/stabilize-architecture
  ```
- **Verificación:** `git status` limpio tras el push. No hay `.joblib`, `.db`, `.sqlite3`, `.png` en el commit (`git show --stat HEAD | grep -E "\.joblib|\.db|\.sqlite3|\.png"`).
- [ ] Estado: pendiente

---

### [T-6.6] Verificación final integral

- **Archivo(s):** ninguno (ejecución)
- **Comandos:**
  ```bash
  # 1. Tests unitarios
  cd backend && pytest tests/ -v

  # 2. Sin artefactos binarios versionados
  git ls-files | grep -E "\.joblib|\.pkl|\.db|\.sqlite3|\.png"

  # 3. Sin rutas/columnas obsoletas en código de producción
  grep -rn "current_model\.pkl\|unicorn_valuation_pipeline\|storage/app\.db\|sqlite:///" \
    --include="*.py" backend/
  grep -rn "Valuation \(\\\$B\)\|investor_count\|join_year" \
    --include="*.py" backend/

  # 4. Sin Streamlit
  grep -rn "streamlit" --include="*.py" --include="*.yaml" --include="*.txt" backend/

  # 5. DATABASE_URL no hardcodeada
  grep -rn "postgresql://unicorn" --include="*.py" backend/

  # 6. Raíz limpia
  ls -1  # → backend frontend .specify .github docker-compose.yml .gitignore

  # 7. Docker Compose arranca
  docker compose up --build -d && sleep 10 && docker compose ps
  ```
- **Verificación:** Tests en verde. Ningún `grep` devuelve resultados. Los tres contenedores están en estado `running`. Proyecto listo para merge.
- [ ] Estado: pendiente

---

## Resumen de Progreso

| Fase | Tareas | Completadas | Pendientes | Estado |
|------|--------|-------------|------------|--------|
| Fase 0 — Preparación           | 3  | 3  | 0  | ✅ Completada |
| Fase 1 — Limpieza              | 11 | 11 | 0  | ✅ Completada |
| Fase 2 — Rutas y Configuración | 10 | 1  | 9  | ▶ **Activa** |
| Fase 3 — Tests                 | 7  | 0  | 7  | Bloqueada |
| Fase 4 — API + PostgreSQL      | 10 | 0  | 10 | Bloqueada |
| Fase 5 — Frontend + Docker     | 8  | 0  | 8  | Bloqueada |
| Fase 6 — Documentación         | 6  | 0  | 6  | Bloqueada |
| **Total**                      | **55** | **15** | **40** | |

> Actualizar esta tabla al completar cada fase. **Siguiente ticket:** `[T-3.1]` Corregir umbral de R² en `backend/tests/test_pipeline.py`.
