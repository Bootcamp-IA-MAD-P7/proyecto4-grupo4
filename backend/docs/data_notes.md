# Dataset Notes — Unicorn Startups

## Fuente

- **Kaggle:** [ramjasmaurya/unicorn-startups](https://www.kaggle.com/datasets/ramjasmaurya/unicorn-startups)
- **Version:** 14 (ultima disponible)
- **Periodo:** Startups unicornio hasta septiembre 2022
- **Ruta canonica del dataset crudo:** `backend/data/raw/unicorn_companies.csv`

---

## Esquema del Dataset Crudo de Entrada

Archivo fuente: `backend/data/raw/unicorn_companies.csv`

| Columna Original (Kaggle) | Tipo   | Descripcion                                   |
|---------------------------|--------|-----------------------------------------------|
| `Company`                 | string | Nombre de la startup                          |
| `Valuation ($B)`          | string | Valoracion cruda, ej. `"$1.5"` — parsear a `float` |
| `Date Joined`             | string | Fecha de ingreso al club unicornio            |
| `Country`                 | string | Pais de origen                                |
| `City`                    | string | Ciudad de origen (puede contener `\xa0`)      |
| `Industry`                | string | Industria/sector                              |
| `Select Investors`        | string | Lista de inversores separada por `,`          |
| `Funding`                 | string | Funding crudo, ej. `"$500M"` — parsear a `float` |
| `Year Founded`            | int    | Anio de fundacion                             |

**Total:** ~1062 filas, 9 columnas

---

## Features de Modelado (X) — Esquema Definitivo Post-Parseo

Estos son los **unicos** nombres de columna validos en todo el codigo Python, tests y API.

| Nombre Columna | Dtype  | Derivacion                                           |
|----------------|--------|------------------------------------------------------|
| `year_founded` | int    | Directo de `Year Founded`                            |
| `funding_usd`  | float  | Parseo de `Funding` — dolares (M=1e6, B=1e9)        |
| `company_age`  | int    | `anio_actual - year_founded`                         |
| `industry`     | string | `Industry` normalizado (lowercase, top-N + "other") |
| `country`      | string | `Country` normalizado (top-N + "other")              |
| `continent`    | string | Derivado de `country` mediante lookup                |

### Variable Objetivo (y)

| Nombre Columna  | Dtype | Derivacion                                   |
|-----------------|-------|----------------------------------------------|
| `valuation_usd` | float | Parseo de `Valuation ($B)` — dolares (x1e9)  |

> **Prohibido en produccion:** `Valuation ($B)`, `Investors`, `investor_count`, `join_year`, `join_month`. Pueden existir solo en notebooks historicos.

---

## Base de Datos de Produccion

La persistencia de feedback se realiza en **PostgreSQL** via la variable de entorno `DATABASE_URL`.

No existe ningun archivo SQLite local. Las rutas `storage/app.db` y `data/feedback/predictions.sqlite3` han sido eliminadas del proyecto.

Conexion interna (Docker): `postgresql://unicorn_user:pass@db:5432/unicorns`

---

## Estructura de Directorios de Datos

```
backend/data/
├── raw/
│   └── unicorn_companies.csv        # Dataset crudo de Kaggle
└── processed/
    └── dataset.parquet              # Dataset procesado (generado, no versionado)
```

---

## Calidad de Datos

### Duplicados

- **0 filas duplicadas** exactas
- **0 empresas duplicadas** (cada startup aparece una vez)

### Nulos

- **~18 filas** con `Select Investors` = NaN (~1.5% del dataset)
- Sin nulos en columnas criticas (`Company`, `Valuation ($B)`, `Date Joined`, `Country`, `Industry`)

### Outliers

- **~150 outliers** en `valuation_usd` (por encima de IQR x 1.5)
- ByteDance ($140B), SpaceX ($127B), SHEIN ($100B) son los mas extremos
- La distribucion es **muy sesgada a la derecha**

---

## Transformaciones Aplicadas

1. **Limpieza de columnas:** Se elimina `\xa0` del nombre `City`
2. **Valoracion:** Se extrae `$`, se convierte `Valuation ($B)` a `valuation_usd` en dolares (x1e9)
3. **Funding:** Se parsea `Funding` (M=1e6, B=1e9) a `funding_usd` en dolares
4. **Edad de empresa:** Se calcula `company_age = anio_actual - year_founded`
5. **Normalizacion categorica:** `industry` y `country` se normalizan con agrupacion top-N + "other"
6. **Continente:** Se deriva `continent` desde `country` mediante lookup geografico

---

## Estadisticas Clave

- **Total startups:** ~1062
- **Paises:** 48
- **Industrias:** 20 (top-N normalizado)
- **Valoracion mediana:** ~$1.6B
- **Valoracion promedio:** ~$3.25B
- **Valoracion maxima:** $140B (ByteDance)
- **Pais con mas startups:** United States
- **Industria con mas startups:** Fintech

---

## Limitaciones del Dataset

1. **Fecha de corte:** Solo incluye startups hasta septiembre 2022
2. **Valoracion autodeclarada:** Sin verificacion independiente
3. **Sin series de tiempo:** No hay datos historicos de valoracion
4. **R2 bajo del modelo actual:** R2~0.22 por heterocedasticidad estructural (ver `architecture_decision_target.md`)
