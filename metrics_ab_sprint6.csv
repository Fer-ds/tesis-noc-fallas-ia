# Reporte Sprint Semana 6

## 1. Contexto

El proyecto busca aplicar modelos de inteligencia artificial para apoyar la detección proactiva de fallas físicas en infraestructura de red dentro de un entorno NOC. Para esta semana se trabajó con dos fuentes: incidentes históricos TX/IP y un nuevo Excel de alarmas actuales. El dataset histórico se usa para entrenar/validar; el snapshot de alarmas actuales se incorpora como fuente adicional para análisis y priorización.

## 2. Dataset y entorno

- Incidentes procesados y anonimizados: **4215** registros.
- Alarmas actuales procesadas y anonimizadas: **4029** registros.
- Snapshot de alarmas: **2026-05-04 17:57:19**.
- Variable objetivo: `label_over_ola`.
- Métrica central: `Recall Over OLA`.

## 3. Línea base

La línea base no usa entrenamiento estadístico. Aplica una regla operacional basada en prioridad, familia de incidente, tipo de problema y OLA corto. Su función es servir como referencia simple para comparar si los modelos realmente aportan mejora.

## 4. Experimentos A/B

- **Baseline:** regla operacional.
- **Var1:** Logistic Regression con One-Hot Encoding, variables temporales, SLA/OLA y balanceo de clases.
- **Var2:** Random Forest con branch anonimizado y umbral de decisión 0.40 para mejorar recall.

## 5. Resultados comparables

| Experimento | Modelo | Recall | Precision | F1 | Avg Precision | Train sec | Latency ms/1000 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | Regla operacional | 1.0 | 0.1922 | 0.3224 | 0.185 | 0.0 | 2.7079 |
| Var1 | LogisticRegression | 0.6728 | 0.4467 | 0.5369 | 0.4413 | 0.0526 | 6.4577 |
| Var2 | RandomForestClassifier | 0.7346 | 0.4375 | 0.5484 | 0.3888 | 1.5331 | 296.5485 |

Gráfico generado: `results/pr_curve_sprint6.png`.

## 6. Validación

Se aplicó split temporal 80/20. Los registros más antiguos se usaron para entrenamiento y los más recientes para validación. Se evitó usar `duration_hours`, `status` o textos de cierre como variables predictivas, porque pueden generar leakage al contener información posterior al inicio del incidente. La semilla de reproducción usada fue 42.

## 7. Conclusión y decisión

Se adopta provisionalmente **Baseline** porque ofrece el mejor recall sobre la clase `Over OLA`. En un contexto NOC, esta métrica es prioritaria, ya que el objetivo es anticipar la mayor cantidad posible de incidentes que podrían incumplir el tiempo operativo, aunque se genere revisión adicional por falsos positivos.

## 8. Riesgos y próximos pasos

- Riesgo: posible drift operacional si cambian criterios de escalamiento, branch, herramienta de monitoreo o severidad de alarmas.
- Próximo paso: integrar más variables de alarmas de energía/BTS y validar si el score preliminar de alarmas se puede convertir en una etiqueta supervisada con datos de cierre.
