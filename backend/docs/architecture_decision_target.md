# ADR-001: Variable Objetivo del Modelo de Valoración

**Estado:** Decisión diferida — implementación programada para Fase 7 (post-MVP)  
**Fecha:** 2026-06-25  
**Autores:** Equipo proyecto4-grupo4  
**Contexto SDD:** `[T-7.1]` en `4_tasks.md`

---

## 1. Contexto y Problema

### 1.1 Objetivo declarado del sistema

El sistema predice la valoración absoluta de empresas tipo unicornio (`valuation_usd` en dólares) a partir de características de la empresa en el momento de la predicción: año de fundación, financiación recibida, sector, país y antigüedad.

### 1.2 Diagnosis del modelo actual (T1–T3, Gradient Boosting)

El pipeline de Fase 3 entrenó un `GradientBoostingRegressor` con `log1p(valuation_usd)` como target transformado. Los resultados del stress test diagnóstico muestran:

| Métrica | Valor |
|---|---|
| R² validación | 0.18–0.19 |
| R² cross-validation (5-fold) | 0.24 ± 0.10 |
| Pendiente del Residual Plot | +1.51 B USD / B USD predicho |
| Ratio de heterocedasticidad | 5.05× |
| Veredicto | Patrón sistemático — sesgo por rango |

El modelo subestima sistemáticamente las valoraciones altas. Cada B USD adicional de valoración real introduce +1.5 B USD de error residual positivo. Esto no es ruido: es una señal de que la arquitectura del problema está mal planteada.

### 1.3 Raíz del problema: "piso unicornio" y compresión del target

La distribución de `valuation_usd` en el dataset (~1 062 empresas) presenta dos patrones que el ECM (y su variante log-transformada) no puede gestionar bien:

**Compresión en el piso de $1B–$2B ("piso unicornio")**  
Por definición, toda empresa del dataset es unicornio (≥ $1B). El 70–75% de las observaciones se concentra en la banda $1B–$3B. El modelo aprende a predecir en esta zona de alta densidad y generaliza mal fuera de ella. El error cuadrático medio penaliza de forma homogénea en escala absoluta, incentivando al modelo a "pegar" predicciones al centroide de la distribución densa.

**Heterocedasticidad estructural**  
La varianza del error crece con la magnitud de la valoración. Para decacornios (> $10B), el spread real puede ser de decenas de miles de millones de dólares; para empresas de $1B–$2B, de cientos de millones. El ECM trata ambos errores de forma simétrica en escala cuadrática, lo que viola el supuesto de homocedasticidad de los estimadores ordinarios y sesga el aprendizaje hacia la cola baja.

Formalmente, si se denota el error residual como εᵢ = yᵢ − ŷᵢ, el Residual Plot mostró:

```
E[εᵢ | ŷᵢ] ≈ 1.51 · ŷᵢ  (en escala B USD)
```

Esto implica que la esperanza del error **no es cero condicional a la predicción**, violando la condición de insesgadez. El modelo no extrae señal en la cola alta; simplemente regresa al centroide.

---

## 2. Solución Diferida — Fase 7: Múltiplo de Valoración como Target

### 2.1 Formulación del nuevo target

En lugar de predecir `valuation_usd` (absoluto), se propone predecir el **múltiplo de valoración**:

```
multiple = valuation_usd / funding_usd
```

Este ratio es una métrica estándar en capital riesgo ("funding multiple" o "return on investment esperado"). Sus propiedades estadísticas son superiores para este problema:

| Propiedad | `log1p(valuation_usd)` | `log1p(multiple)` |
|---|---|---|
| Distribución | Sesgada derecha, pico en $1B | Más simétrica, normalizable |
| Correlación con features | Moderada (R² ≈ 0.22) | Esperada más alta |
| Heterocedasticidad | Alta (5×) | Reducida (el funding absorbe escala) |
| Interpretabilidad | Directa pero sesgada | Requiere post-procesado |

**Intuición:** Dos empresas con valoración de $5B pero con $50M y $4B de financiación respectivamente tienen múltiplos muy distintos (100× vs 1.25×). Esta diferencia captura la señal de "eficiencia de capital" que el modelo absoluto no puede separar.

### 2.2 Por qué el múltiplo normaliza la heterocedasticidad

Al dividir por `funding_usd`, se elimina la mayor fuente de varianza condicional: la escala del negocio. El funding actúa como proxy del tamaño operativo. El múltiplo mide cuánto "apalancamiento de valoración" genera ese funding en ese sector y contexto. La dispersión del múltiplo entre sectores y geografías es más homogénea que la dispersión de `valuation_usd` bruto.

Formalmente, si `valuation = funding × multiple`, entonces:

```
Var(valuation | funding) = funding² · Var(multiple | funding)
```

Si `Var(multiple | funding)` es aproximadamente constante (homocedasticidad del múltiplo), el modelo en espacio de múltiplo tiene un problema de regresión bien condicionado.

### 2.3 Impacto esperado

- Reducción de la pendiente del Residual Plot por debajo de ±0.5 B/B
- Incremento del R² de validación hacia el rango 0.35–0.50
- Eliminación del sesgo sistemático de compresión en el piso unicornio

Estos son los criterios de aceptación de `[T-7.1]`.

---

## 3. Contrato de la API — Sin Cambios de Interfaz

Esta es la decisión arquitectónica más importante de este ADR: **el cambio de target es interno al pipeline de ML y es completamente transparente para cualquier consumidor de la API**.

### 3.1 Flujo de inferencia con el nuevo target

```
Input:  { funding_usd: 50_000_000, ... }
           ↓
        Pipeline ML predice: multiple_pred = expm1(model.predict(features))
           ↓
        Conversión interna: valuation_usd = multiple_pred × funding_usd
           ↓
Output: { valuation_usd: 1_250_000_000.0, valuation_b: 1.25, ... }
```

### 3.2 Contrato de la API (invariante)

El endpoint `POST /predict` seguirá respondiendo exactamente con el mismo esquema definido en `2_spec.md` sección 4:

```json
{
  "valuation_usd": 1250000000.0,
  "valuation_b": 1.25,
  "model_version": "best_model.joblib",
  "timestamp": "2026-06-25T10:00:00+00:00"
}
```

El frontend, los tests de contrato y cualquier integración externa **no requieren ningún cambio** cuando se implemente `[T-7.1]`.

### 3.3 Cambios de implementación confinados al backend ML

Los únicos archivos que se modificarán en Fase 7 son:

| Archivo | Cambio |
|---|---|
| `backend/src/models/train.py` | `fit_model()` usa `log1p(multiple)` como target; `predict_absolute()` reconvierte multiplicando por `funding_usd` |
| `backend/config.yaml` | Nueva clave `target_transform: multiple` |
| `backend/app/model_service.py` | `predict_valuation()` pasa `funding_usd` al pipeline para la reconversión post-inferencia |
| `backend/scripts/train.py` | `enforce_quality_gate()` ajustado si el umbral de R² del múltiplo difiere |
| `backend/tests/test_pipeline.py` | Umbral R² actualizado según baseline del múltiplo |

---

## 4. Decisión

**Decisión adoptada:** mantener `valuation_usd` como target del modelo en producción hasta completar el MVP (Fases 4–6). Implementar el múltiplo de valoración en Fase 7 como mejora post-MVP.

**Razonamiento:** El cambio de target requiere reentrenamiento, revalidación de umbrales y ajuste del pipeline de inferencia. Estos cambios, aunque bien definidos, introducen riesgo en la entrega del MVP. El modelo actual (R² ≈ 0.18–0.24) es suficiente para demostrar el flujo extremo a extremo. La calidad predictiva es deuda técnica documentada, no un bloqueante del MVP.

**Consecuencia asumida:** `test_train_meets_min_r2` continuará fallando (R²=0.18 < 0.50) hasta que `[T-7.1]` se implemente y el modelo se reentrene con el nuevo target.
