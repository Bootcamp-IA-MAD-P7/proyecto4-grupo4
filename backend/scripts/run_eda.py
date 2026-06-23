import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, ".")

from src.config import load_config
from src.data.load import build_and_save_processed_dataset, build_features, load_raw_dataset

FIGURES_DIR = "reports/figures"
os.makedirs(FIGURES_DIR, exist_ok=True)
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

config = load_config()
raw_path = config["paths"]["raw_data"]
df_raw = load_raw_dataset()
print(f"Dataset cargado desde: {raw_path} ({len(df_raw)} filas)")

df = build_features(df_raw)
df = df.dropna(subset=[config["project"]["target"], *config["features"]["numeric"]]).copy()
df["valuation_b"] = df["valuation_usd"] / 1_000_000_000

numeric_features = config["features"]["numeric"]
print(f"Muestras modelables: {len(df)}")
print(f"Features numericas: {numeric_features}")

print("\n--- Correlaciones vs valuation_usd ---")
for col in numeric_features:
    pearson = df[col].corr(df["valuation_usd"])
    spearman = df[col].corr(df["valuation_usd"], method="spearman")
    print(f"  {col:20s}  Pearson={pearson:+.4f}  Spearman={spearman:+.4f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df["valuation_b"], bins=50, edgecolor="black", alpha=0.7)
axes[0].set_title("Distribucion de Valuation")
axes[0].set_xlabel("Valuation ($B)")
axes[0].set_ylabel("Frecuencia")
median_b = df["valuation_b"].median()
axes[0].axvline(median_b, color="red", linestyle="--", label=f"Mediana: {median_b:.1f}")
axes[0].legend()
axes[1].boxplot(df["valuation_b"], vert=True)
axes[1].set_title("Boxplot de Valuation")
axes[1].set_ylabel("Valuation ($B)")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "01_valuation_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Figura 01 guardada")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
country_counts = df["country"].value_counts().head(10)
country_counts.plot(kind="barh", ax=axes[0], color="steelblue")
axes[0].set_title("Top 10 Paises - Cantidad de Startups")
axes[0].set_xlabel("Cantidad")
axes[0].invert_yaxis()
country_val = df.groupby("country")["valuation_b"].mean().nlargest(10)
country_val.plot(kind="barh", ax=axes[1], color="coral")
axes[1].set_title("Top 10 Paises - Valuacion Promedio")
axes[1].set_xlabel("Valuacion Promedio ($B)")
axes[1].invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "02_valuation_by_country.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Figura 02 guardada")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
ind_counts = df["industry"].value_counts().head(10)
ind_counts.plot(kind="barh", ax=axes[0], color="mediumseagreen")
axes[0].set_title("Top 10 Industrias - Cantidad de Startups")
axes[0].set_xlabel("Cantidad")
axes[0].invert_yaxis()
ind_val = df.groupby("industry")["valuation_b"].mean().nlargest(10)
ind_val.plot(kind="barh", ax=axes[1], color="goldenrod")
axes[1].set_title("Top 10 Industrias - Valuacion Promedio")
axes[1].set_xlabel("Valuacion Promedio ($B)")
axes[1].invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "03_valuation_by_industry.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Figura 03 guardada")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
year_counts = df["year_founded"].value_counts().sort_index()
year_counts.plot(kind="bar", ax=axes[0], color="mediumpurple")
axes[0].set_title("Startups por Ano de Fundacion")
axes[0].set_xlabel("Ano")
axes[0].set_ylabel("Cantidad")
year_val = df.groupby("year_founded")["valuation_b"].mean()
year_val.plot(kind="bar", ax=axes[1], color="salmon")
axes[1].set_title("Valuacion Promedio por Ano de Fundacion")
axes[1].set_xlabel("Ano")
axes[1].set_ylabel("Valuacion Promedio ($B)")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "04_startups_by_year.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Figura 04 guardada")

corr_cols = ["valuation_b", *numeric_features]
corr = df[corr_cols].corr()
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax, fmt=".2f")
ax.set_title("Matriz de Correlaciones - Esquema Definitivo")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "06_correlation_matrix.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Figura 06 guardada")

processed_path = build_and_save_processed_dataset()
print(f"Dataset procesado guardado: {processed_path}")

figures = sorted(f for f in os.listdir(FIGURES_DIR) if f.endswith(".png"))
print(f"\nFiguras generadas ({len(figures)}):")
for figure in figures:
    print(f"  - {figure}")
