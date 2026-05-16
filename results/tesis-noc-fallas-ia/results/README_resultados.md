# Resultados Semana 5

Este directorio contiene los resultados comparables de los experimentos iniciales.

## Archivos

- `metricas_semana5.csv`: tabla de comparación entre baseline y variantes.
- `pr_curve_semana5.png`: curva Precision-Recall del mejor escenario evaluado.
- `comparacion_clasificacion_semana5.png`: gráfico comparativo de Accuracy, Recall y F1-score.

## Interpretación técnica

La métrica principal considerada es **Recall**, debido a que en un entorno NOC es prioritario detectar la mayor cantidad posible de incidentes con riesgo de incumplimiento o criticidad operativa. Aunque una variante pueda reducir ligeramente el Accuracy, una mejora en Recall y F1-score puede ser más útil para reducir falsos negativos en la operación.
