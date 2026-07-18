# Nota aclaratoria — clase positiva, alertas y recall

## Definición correcta

- **Clase real positiva (`y_true = 1`)**: el incidente realmente incumplió o superó el OLA.
- **Predicción positiva (`y_pred = 1`)**: el sistema emite una alerta porque estima riesgo de incumplimiento.
- Una alerta es, por tanto, una **predicción positiva**; no es la verdad real por sí misma.

## Lectura de la matriz

- **TP**: se emitió alerta y el incidente sí incumplió el OLA.
- **FP**: se emitió alerta, pero el incidente no incumplió; es una falsa alarma.
- **FN**: no se emitió alerta, pero el incidente sí incumplió; es un caso crítico perdido.
- **TN**: no se emitió alerta y el incidente no incumplió.

## Resultado con el umbral original 0.245

- Baseline BAU: TP=697, FN=19, FP=1420, TN=25, recall=97.35%.
- Modelo actual: TP=662, FN=54, FP=1254, TN=191, recall=92.46%.

El umbral 0.245 reduce 166 falsas alarmas, pero genera
35 falsos negativos adicionales. Si el objetivo principal es no perder
incumplimientos, este punto de operación no debe usarse como reemplazo directo del baseline.

## Corrección propuesta

1. Mantener `incumple OLA = 1` como clase positiva; no invertir las etiquetas.
2. Cambiar la selección del umbral a una restricción de negocio basada en recall o FNR.
3. Usar el modelo primero como **ranking o priorización**, sin suprimir las alertas del baseline.
4. Validar cualquier umbral nuevo en un periodo temporal futuro o en shadow mode.

Como análisis exploratorio, el umbral 0.200 produce en este holdout:
TP=698, FN=18, FP=1377, TN=68,
recall=97.49% y tasa de alertas=96.02%.
Como el ajuste surge después del feedback, debe confirmarse con datos temporales nuevos antes de presentarlo
como estimación final no sesgada.
