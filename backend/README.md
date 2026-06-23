# Proyecto 4 - Grupo 4: Unicorn Startups

Predicción de la valuación de startups unicornio utilizando datos de Kaggle.

## Estructura del Proyecto

```
proyecto4-grupo4/
├── data/
│   ├── raw/
│   │   └── dataset_raw.csv            # Dataset crudo descargado de Kaggle
│   └── dataset_clean.csv              # Dataset limpio con features
├── models/
│   └── best_model.joblib              # Modelo pipeline guardado
├── notebooks/
│   ├── 01_eda.ipynb                   # Análisis exploratorio y calidad de datos
│   └── 02_preprocessing_baseline.ipynb # Pipeline de preprocesamiento y baselines
├── src/
│   ├── data/
│   │   ├── load_data.py               # Descarga y carga del dataset
│   │   └── data_validation.py         # Checks reutilizables de calidad
│   ├── preprocessing/
│   │   └── preprocessing_pipeline.py  # Feature engineering + ColumnTransformer
│   └── models/
│       ├── train.py                   # Entrenamiento de modelos baseline
│       └── evaluate.py                # Métricas y detección de overfitting
├── tests/
│   └── test_preprocessing.py          # Tests unitarios del pipeline
├── docs/
│   └── data_notes.md                  # Documentación del dataset
├── requirements.txt
└── README.md
```

## Integrantes y Responsabilidades

### Integrante 1 - Dataset, Calidad y EDA
- Carga y validación del dataset crudo
- Limpieza de columnas (nombres, encoding)
- Detección de nulos, duplicados, outliers
- Feature engineering básico (fechas, inversores)
- Visualizaciones: distribución del target, países, industrias, años
- Validaciones reutilizables en `src/data/data_validation.py`
- Documentación en `docs/data_notes.md`

### Integrante 2 - Preprocesamiento y Baseline
- Pipeline de preprocesamiento con `Pipeline` y `ColumnTransformer`
- Imputación, escalado (numéricas) y OneHotEncoder (categóricas)
- Entrenamiento de DummyRegressor, LinearRegression y Ridge
- Cálculo de métricas: MAE, MSE, RMSE, R2
- Control de overfitting (comparación train/test)
- Guardado del modelo con `joblib`

## Flujo de Trabajo

### 1. Instalación

```bash
# Crear entorno virtual
python -m venv venvp4g4
venvp4g4\Scripts\activate        # Windows
# source venvp4g4/bin/activate   # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecución del EDA (Integrante 1)

```bash
# Abrir Jupyter desde la raíz del proyecto
jupyter notebook notebooks/01_eda.ipynb
```

Este notebook:
- Descarga el dataset de Kaggle automáticamente
- Guarda el crudo en `data/raw/dataset_raw.csv`
- Ejecuta validaciones de calidad
- Genera visualizaciones inline (6 figuras)
- Guarda el limpio en `data/processed/dataset_clean.csv`

### 3. Ejecución del Pipeline y Entrenamiento (Integrante 2)

```bash
# Ejecutar el notebook
jupyter notebook notebooks/02_preprocessing_baseline.ipynb

# O ejecutar desde línea de comandos
python -m src.models.train
```

Este flujo:
- Descarga el dataset de Kaggle
- Aplica FeatureEngineering (fechas, inversores, limpieza)
- Guarda `data/dataset_clean.csv`
- Entrena 3 modelos baseline
- Guarda el mejor en `models/best_model.joblib`

### 4. Ejecución de Tests

```bash
python -m pytest tests/ -v
```

## Pipeline de Preprocesamiento

El pipeline completo (`preprocessing_pipeline.py`) consta de:

**FeatureEngineer** (custom transformer):
1. Limpieza de nombres de columnas (elimina `\xa0`)
2. Extracción de features desde `Date Joined`: `join_year`, `join_month`, `years_since_joined`
3. Conteo de inversores: `investor_count`
4. Limpieza de `Valuation ($B)`: elimina `$` y `,`, convierte a float -> `valuation_b`
5. Elimina columnas originales (`Company`, `Date Joined`, `Investors`, `Valuation ($B)`)

**Preprocessor** (ColumnTransformer):
- Numéricas (`join_year`, `join_month`, `years_since_joined`, `investor_count`): `SimpleImputer(median)` + `StandardScaler`
- Categóricas (`Country`, `Industry`): `SimpleImputer(most_frequent)` + `OneHotEncoder`

## Modelos Entrenados

| Modelo | Descripción |
|--------|-------------|
| DummyRegressor | Baseline mínimo (predice la media) |
| LinearRegression | Regresión lineal simple |
| Ridge | Regresión lineal con regularización L2 |

## Métricas

- **MAE** - Error absoluto promedio
- **MSE** - Error cuadrático medio
- **RMSE** - Raíz del error cuadrático medio
- **R2** - Coeficiente de determinación

## Uso del Modelo Guardado

```python
import joblib
import pandas as pd

# Cargar el pipeline completo
pipe = joblib.load('models/best_model.joblib')

# Predecir con datos crudos (el pipeline hace todo el preprocesamiento)
nuevos_datos = pd.DataFrame({
    'Company': ['MiStartup'],
    'Valuation ($B)': ['$5'],
    'Date Joined': ['1/1/2020'],
    'Country': ['United States'],
    'City ': ['San Francisco'],
    'Industry': ['Fintech'],
    'Investors': ['VC1, VC2, VC3'],
})

prediccion = pipe.predict(nuevos_datos)
print('Valuación estimada: ${:.2f}B'.format(prediccion[0]))
```

## Dataset

- **Fuente:** [Kaggle - Unicorn Startups](https://www.kaggle.com/datasets/ramjasmaurya/unicorn-startups)
- **Registros:** 1186 startups unicornio
- **Periodo:** Hasta septiembre 2022
- **Target:** `valuation_b` (valuación en miles de millones USD)
- **Features:** país, ciudad, industria, año/mes de inclusión, cantidad de inversores

Más detalles en `docs/data_notes.md`.