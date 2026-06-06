# Guion breve de exposición - Sprint 7 HPO

Buenas noches. En este Sprint 7 actualicé el trabajo incorporando búsqueda de hiperparámetros, tal como se solicitó para la semana.

Primero, mantuve la base procesada y anonimizada. No estoy usando datos sensibles como tickets completos, coordenadas, nombres de enlaces ni identificadores operativos. La variable objetivo sigue siendo `label_over_ola`, que identifica si un incidente supera o no el OLA.

Segundo, definí una validación temporal con `TimeSeriesSplit`. Esto es importante porque en incidentes NOC no debo entrenar con información futura para predecir eventos pasados.

Tercero, ejecuté dos estrategias comparables: Random Search y búsqueda Bayesiana. Ambas usan el mismo dataset, la misma métrica, los mismos folds y la misma semilla, para que la comparación sea justa.

También apliqué early stopping y pruning. El early stopping corta el entrenamiento cuando el Gradient Boosting deja de mejorar. El pruning se aplicó de dos maneras: con `ccp_alpha` en los árboles base y cortando trials malos después del primer fold cuando estaban por debajo del rendimiento histórico esperado.

La métrica principal fue F1, porque el problema está desbalanceado y me interesa equilibrar precision y recall para detectar incidentes con riesgo de superar el OLA.

La configuración ganadora fue el método **random_search**, trial **8**, con F1 promedio de **0.4986**. El resultado tiene recall alto y precision baja, entonces para producción tendría que ajustar el umbral, pero para esta semana ya queda cumplido el objetivo principal: trazabilidad completa del proceso HPO.

Finalmente, la decisión es quedarme con esta configuración como baseline HPO reproducible de Sprint 7. El aporte principal de esta semana no es solo mejorar una métrica, sino dejar espacio de búsqueda, presupuesto, logs, pruning, tabla top-k, gráficos y configuración ganadora.
