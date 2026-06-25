# Dataset Notes - Unicorn Startups

## Fuente

- **Kaggle:** `ramjasmaurya/unicorn-startups`
- **Problema:** regresion de la valoracion de startups unicornio.
- **Target:** `valuation_usd`.

## Columnas crudas principales

| Columna | Descripcion |
|---|---|
| `Company` | Nombre de la startup |
| `Valuation` | Valoracion como texto monetario (`$140B`, `$572M`) |
| `Funding` | Financiacion acumulada como texto monetario |
| `Year Founded` | Año de fundacion |
| `Industry` | Sector |
| `Country` | Pais |
| `Continent` | Continente |

## Dataset procesado

El pipeline genera `data/processed/dataset.pkl` con estas variables clave:

| Columna | Descripcion |
|---|---|
| `valuation_usd` | Target numerico en dolares |
| `funding_usd` | Funding numerico en dolares |
| `year_founded` | Año de fundacion numerico |
| `company_age` | Edad aproximada de la empresa |
| `log_funding_usd` | Transformacion logaritmica del funding |
| `funding_velocity` | Funding dividido por edad de empresa |
| `funding_vs_industry` | Funding relativo a la mediana del sector |
| `industry` | Sector agrupando categorias raras como `Other` |
| `country` | Pais agrupando categorias raras como `Other` |
| `continent` | Continente |

## Features del modelo

Las features activas estan definidas en `config.yaml`:

- Numericas: `year_founded`, `log_funding_usd`, `funding_velocity`, `funding_vs_industry`, `company_age`.
- Categoricas: `industry`, `country`, `continent`.

## Calidad y limitaciones

- El target esta fuertemente sesgado por outliers de alta valoracion.
- El modelo mejora respecto a baselines simples, pero la señal disponible no explica toda la variabilidad.
- Las empresas con valoraciones extremas tienden a producir residuos mayores.
- El feedback de la aplicacion se guarda para monitorizar predicciones reales y alimentar futuros reentrenamientos.
