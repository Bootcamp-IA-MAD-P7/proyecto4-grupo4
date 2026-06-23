# Experiment Log — Features de Cola

**Fecha:** 2025-06-23  
**Fase:** 3 (post-estabilización del pipeline ML)  
**Estado:** Descartado

## Objetivo

Corregir el sesgo sistemático de subestimación en empresas de gran valoración (cola alta del target `valuation_usd`), detectado en el Residual Plot con pendiente de tendencia ≈ +1.55 B USD / B USD predicho.

## Acciones

Se añadieron dos features de interacción sin modificar el target académico:

| Feature | Definición |
|---|---|
| `is_mega_unicorn` | Flag binario: `1` si `funding_usd > P95`, `0` en caso contrario |
| `log_funding_interaction` | `funding_vs_industry × log_funding_usd` |

El esquema base T1–T3 (`log_funding_usd`, `funding_velocity`, `funding_vs_industry`) se mantuvo intacto.

## Resultados (Stress Test)

| Métrica | Baseline T1–T3 | Con features de cola |
|---|---|---|
| R² validación | ~0.22 | **0.19** |
| Pendiente residuos | +1.55 B/B | +1.51 B/B (sin mejora relevante) |
| Veredicto residual | Patrón sistemático | Patrón persistente |

El entrenamiento completo rechazó el artefacto (R² < 0.50). El modelo campeón en disco (`gradient_boosting`, R² val ≈ 0.18, CV ≈ 0.24) no fue sobrescrito.

## Conclusión

Las features de cola **no aportan señal suficiente** y aumentan la colinealidad con las variables T1–T3 existentes. La subestimación en la cola alta persiste porque el volumen de observaciones en ese rango es insuficiente para que el modelo aprenda la dinámica de decacornios solo con flags de percentil e interacciones log-lineales.

**Decisión:** Revertir al esquema estable T1–T3. No se continuarán experimentos de este tipo en Fase 3.
