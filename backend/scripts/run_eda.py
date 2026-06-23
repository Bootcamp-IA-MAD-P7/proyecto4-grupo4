import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '.')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)

from src.data.data_validation import run_all_checks_raw, run_all_checks_clean, print_check_results

FIGURES_DIR = 'reports/figures'
RAW_DATA_PATH = 'data/raw/unicorn_companies.csv'
os.makedirs(FIGURES_DIR, exist_ok=True)

df_raw = pd.read_csv(RAW_DATA_PATH)
print(f'Dataset cargado desde: {RAW_DATA_PATH} ({len(df_raw)} filas)')

raw_checks = run_all_checks_raw(df_raw)
print_check_results('VALIDACION - DATOS CRUDOS', raw_checks)

df = df_raw.copy()
df.columns = [c.strip().replace('\xa0', '') for c in df.columns]
df['valuation_b'] = (
    df.iloc[:, 1]
    .str.replace('$', '', regex=False)
    .str.replace(',', '', regex=False)
    .str.strip()
)
df['valuation_b'] = pd.to_numeric(df['valuation_b'], errors='coerce')
df['date_joined'] = pd.to_datetime(df.iloc[:, 2], errors='coerce')
df['join_year'] = df['date_joined'].dt.year.astype('Int64')
df['join_month'] = df['date_joined'].dt.month.astype('Int64')
df['investor_count'] = df.iloc[:, 6].apply(
    lambda x: len(str(x).split(',')) if pd.notna(x) and str(x).strip() else 0
)
df = df.rename(columns={
    'Company': 'company',
    'Country': 'country',
    'City': 'city',
    'Industry': 'industry',
    'Investors': 'investors',
})

clean_checks = run_all_checks_clean(df)
print_check_results('VALIDACION - DATOS LIMPIOS', clean_checks)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df['valuation_b'], bins=50, edgecolor='black', alpha=0.7)
axes[0].set_title('Distribucion de Valuation')
axes[0].set_xlabel('Valuation ($B)')
axes[0].set_ylabel('Frecuencia')
med = df['valuation_b'].median()
axes[0].axvline(med, color='red', linestyle='--', label='Mediana: {:.1f}'.format(med))
axes[0].legend()
axes[1].boxplot(df['valuation_b'].dropna(), vert=True)
axes[1].set_title('Boxplot de Valuation')
axes[1].set_ylabel('Valuation ($B)')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '01_valuation_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 01 guardada')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
country_counts = df['country'].value_counts().head(10)
country_counts.plot(kind='barh', ax=axes[0], color='steelblue')
axes[0].set_title('Top 10 Paises - Cantidad de Startups')
axes[0].set_xlabel('Cantidad')
axes[0].invert_yaxis()
country_val = df.groupby('country')['valuation_b'].mean().nlargest(10)
country_val.plot(kind='barh', ax=axes[1], color='coral')
axes[1].set_title('Top 10 Paises - Valuacion Promedio')
axes[1].set_xlabel('Valuacion Promedio ($B)')
axes[1].invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '02_valuation_by_country.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 02 guardada')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
ind_counts = df['industry'].value_counts().head(10)
ind_counts.plot(kind='barh', ax=axes[0], color='mediumseagreen')
axes[0].set_title('Top 10 Industrias - Cantidad de Startups')
axes[0].set_xlabel('Cantidad')
axes[0].invert_yaxis()
ind_val = df.groupby('industry')['valuation_b'].mean().nlargest(10)
ind_val.plot(kind='barh', ax=axes[1], color='goldenrod')
axes[1].set_title('Top 10 Industrias - Valuacion Promedio')
axes[1].set_xlabel('Valuacion Promedio ($B)')
axes[1].invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '03_valuation_by_industry.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 03 guardada')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
year_counts = df['join_year'].value_counts().sort_index()
year_counts.plot(kind='bar', ax=axes[0], color='mediumpurple')
axes[0].set_title('Startups por Ano de Incorporacion')
axes[0].set_xlabel('Ano')
axes[0].set_ylabel('Cantidad')
year_val = df.groupby('join_year')['valuation_b'].mean()
year_val.plot(kind='bar', ax=axes[1], color='salmon')
axes[1].set_title('Valuacion Promedio por Ano')
axes[1].set_xlabel('Ano')
axes[1].set_ylabel('Valuacion Promedio ($B)')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '04_startups_by_year.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 04 guardada')

Q1 = df['valuation_b'].quantile(0.25)
Q3 = df['valuation_b'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
fig, ax = plt.subplots(figsize=(10, 5))
ax.boxplot(df['valuation_b'].dropna(), vert=True)
ax.axhline(upper, color='red', linestyle='--', label='Limite superior (IQR): {:.2f}'.format(upper))
ax.set_title('Boxplot con Outliers detectados')
ax.set_ylabel('Valuation ($B)')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '05_outliers_boxplot.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 05 guardada')

num_cols = ['valuation_b', 'join_year', 'join_month', 'investor_count']
corr = df[num_cols].corr()
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, ax=ax)
ax.set_title('Matriz de Correlaciones')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '06_correlation_matrix.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Figura 06 guardada')

os.makedirs('data/processed', exist_ok=True)
processed_path = 'data/processed/dataset.parquet'
df.to_parquet(processed_path, index=False)
print(f'Dataset procesado guardado: {processed_path}')

figures = sorted([f for f in os.listdir(FIGURES_DIR) if f.endswith('.png')])
print('\nFiguras generadas ({}):'.format(len(figures)))
for f in figures:
    print('  - {}'.format(f))
