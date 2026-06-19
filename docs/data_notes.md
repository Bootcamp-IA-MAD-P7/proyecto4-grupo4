# Dataset Notes - Unicorn Startups

## Fuente
- **Kaggle:** [ramjasmaurya/unicorn-startups](https://www.kaggle.com/datasets/ramjasmaurya/unicorn-startups)
- **Version:** 14 (ultima disponible)
- **Periodo:** Startups unicornio hasta septiembre 2022

## Estructura Original (Cruda)

| Columna | Tipo | Descripcion | Nulos |
|---------|------|-------------|-------|
| Company | str | Nombre de la empresa | 0 |
| Valuation ($B) | str | Valuacion en miles de millones USD (con $) | 0 |
| Date Joined | str | Fecha en que se convirtio en unicornio (M/D/YYYY) | 0 |
| Country | str | Pais de origen | 0 |
| City | str | Ciudad (tiene encoding \\xa0 en nombre) | 0 |
| Industry | str | Sector industrial | 0 |
| Investors | str | Lista de inversores separados por coma | 18 |

**Total:** 1186 filas, 7 columnas

## Estructura Limpia (Procesada)

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| company | str | Nombre de la empresa |
| valuation_b | float64 | Valuacion en miles de millones USD |
| date_joined | datetime | Fecha de inclusion como unicornio |
| country | str | Pais de origen |
| city | str | Ciudad |
| industry | str | Sector industrial |
| investors | str | Lista de inversores (original) |
| join_year | Int64 | Ano de inclusion |
| join_month | Int64 | Mes de inclusion |
| investor_count | int64 | Cantidad de inversores |

## Transformaciones Aplicadas

1. **Limpieza de columnas:** Se elimina `\\xa0` del nombre `City`
2. **Valuacion:** Se extrae `$` y `,`, se convierte a float64
3. **Fecha:** Se parsea string a datetime, se extraen `join_year` y `join_month`
4. **Inversores:** Se cuenta la cantidad de inversores por coma

## Calidad de Datos

### Duplicados
- **0 filas duplicadas** exactas
- **0 empresas duplicadas** (cada startup aparece una vez)

### Nulos
- **18 filas** con `Investors` = NaN (1.5% del dataset)
- Sin nulos en otras columnas criticas
- Las filas sin inversores se marcan como `investor_count = 0`

### Outliers
- **~150 outliers** en `valuation_b` (por encima de IQR * 1.5)
- ByteDance ($140B), SpaceX ($127B), SHEIN ($100B) son los mas extremos
- La distribucion es **muy sesgada a la derecha**

## Limitaciones del Dataset

1. **Fecha de corte:** Solo incluye startups hasta septiembre 2022
2. **Valuacion auto-declarada:** No hay verificacion independiente
3. **Sin fecha de fundacion:** Solo se tiene la fecha de inclusion como unicornio
4. **Inversores no estructurados:** El campo es texto libre, dificulta analisis
5. **Encoding inconsistente:** La columna City tiene caracteres no-ASCII
6. **Sin series de tiempo:** No hay datos historicos de valuacion

## Uso del Dataset

### Para Integrante 2 (Pipeline)
```python
from src.data.load_data import download_dataset
from src.preprocessing.preprocessing_pipeline import save_clean_data

csv_path = download_dataset()
output_path, df_clean = save_clean_data(csv_path)
```

### Para Validacion
```python
from src.data.data_validation import run_all_checks_clean

checks = run_all_checks_clean(df_clean)
```

## Estadisticas Clave

- **Total startups:** 1186
- **Paises:** 48
- **Industrias:** 34
- **Valuacion mediana:** $1.6B
- **Valuacion promedio:** $3.25B
- **Valuacion maxima:** $140B (ByteDance)
- **Pais con mas startups:** United States (636)
- **Industria con mas startups:** Fintech (239)
