# Intent — Refactorización Proyecto 4 Grupo 4

## Propósito

Este documento captura el objetivo estratégico de la refactorización del proyecto de ML para predicción de valoración de startups unicornio. Sirve de ancla para todas las decisiones técnicas posteriores.

---

## Problema Raíz

El proyecto fue desarrollado de forma distribuida y sin contrato técnico previo. Cada integrante tomó decisiones locales (nombres de columnas, rutas de archivos, umbrales, librerías) que ahora generan un sistema internamente inconsistente e imposible de mantener en producción.

---

## Objetivos de la Refactorización

### 1. Unificar el esquema de datos al nuevo flujo (USD)

El pipeline moderno (`src/data/load.py`) normaliza la valoración y el funding a valores numéricos en USD y construye features semánticas limpias. Este esquema es el **único válido** para todo el proyecto. El esquema legacy basado en columnas crudas de Kaggle (`Valuation ($B)`, `Investors`) queda obsoleto y será eliminado.

### 2. Estandarizar todas las rutas de artefactos

Existe un solo conjunto de rutas canónicas para datos, modelos y métricas. Cualquier referencia a rutas alternativas (`current_model.pkl`, `dataset_clean.csv`, `dataset.parquet`) será corregida en todos los archivos del proyecto.

### 3. Hacer cumplir el umbral de calidad del modelo

El umbral de R² se fija en un valor único y se verifica automáticamente en CI. Ningún modelo que no supere ese umbral puede fusionarse a `main`.

### 4. Migrar la interfaz de Streamlit a FastAPI + React

`app/streamlit_app.py` queda eliminado. La arquitectura final es:
- **Backend:** FastAPI (API REST, documentada con OpenAPI)
- **Frontend:** React (SPA ligera, consumiendo la API)
- **Contrato:** definido por los endpoints en `2_spec.md`

### 5. Limpiar el repositorio Git

Los artefactos binarios (modelos, bases de datos, imágenes de reportes) no pertenecen al control de versiones. Un `.gitignore` revisado los excluye. Los artefactos existentes son purgados del historial o eliminados del índice según corresponda.

### 6. Eliminar duplicidades y archivos huérfanos

Archivos `_BACKUP`, duplicados de dataset en `notebooks/data/`, y módulos de carga redundantes serán eliminados para tener un único camino de ejecución.

### 7. Cuidar la coherencia de interfaz y experiencia de usuario

La aplicación React debe presentarse como un producto coherente en español. Los textos visibles deben usar tildes, `ñ` y terminología consistente. Los nombres técnicos del backend pueden mantenerse en inglés cuando formen parte del contrato (`year_founded`, `funding_usd`, `continent`), pero la interfaz debe traducirlos o explicarlos correctamente para la persona usuaria.

Ejemplo clave: el backend conserva el campo técnico `continent` porque el modelo fue entrenado con esa feature, pero el frontend debe mostrarlo como **Región geográfica** y usar etiquetas visibles como `América del Norte` o `América del Sur`, sin presentar esas regiones como continentes.

---

## Estado Deseado

Al finalizar la refactorización, el proyecto cumple con:

- **Un solo pipeline** de datos y entrenamiento, sin ramas muertas.
- **Un solo modelo** serializado en una ruta predecible.
- **Un solo umbral** de calidad que actúa como gate de CI.
- **Una sola API** (FastAPI) como contrato entre frontend y backend.
- **Una sola base de datos** PostgreSQL para feedback y predicciones.
- **Una sola experiencia frontend** coherente, en español, sin mojibake ni mezcla innecesaria de idiomas.
- **Un repositorio limpio**, sin binarios ni código duplicado.

---

## Audiencia de Este Documento

Todos los integrantes del equipo, el revisor de CI/CD y cualquier colaborador externo que quiera entender *por qué* se tomaron las decisiones en `2_spec.md`.
