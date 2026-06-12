# Preguntas probables del profesor - Sprint 8 Demo

## 1. ¿Cuál es el modelo que estás usando?
Estoy usando un `GradientBoostingClassifier`, que es un modelo basado en árboles secuenciales. Cada árbol intenta corregir errores de los anteriores.

## 2. ¿Random Search y Bayes son modelos?
No. Random Search y búsqueda Bayesiana son métodos de búsqueda de hiperparámetros. El modelo es `GradientBoostingClassifier`.

## 3. ¿Qué hiperparámetros estás optimizando?
Optimizo hiperparámetros del `GradientBoostingClassifier`: `n_estimators`, `learning_rate`, `max_depth`, `min_samples_leaf`, `subsample`, `max_features`, `ccp_alpha`, `tol`, `n_iter_no_change` y el `decision_threshold` como umbral de decisión.

## 4. ¿Quién ganó?
Ganó el Trial 8 con Random Search usando `GradientBoostingClassifier`. Obtuvo F1 promedio aprox. 0.4986 en validación temporal.

## 5. ¿Cuáles fueron los parámetros ganadores?
`n_estimators=60`, `learning_rate≈0.0783`, `max_depth=2`, `min_samples_leaf=59`, `subsample≈0.9233`, `max_features=log2`, `ccp_alpha≈0.000127`, `tol≈0.000190`, `n_iter_no_change=8`, `decision_threshold≈0.2304`.

## 6. ¿Dónde demuestras la configuración ganadora?
En `artifacts/best_config_sprint7_hpo.json`, `results/hpo_topk_sprint7.csv` y `logs/hpo_runs_sprint7.csv`.

## 7. ¿Por qué usas F1 y no accuracy?
Porque el problema busca detectar la clase crítica `Over OLA`. Accuracy puede ser engañoso si hay desbalance de clases. F1 balancea precision y recall.

## 8. ¿Tienes alta precision?
No debo decir que la precision es alta. La precision es aprox. 0.3333. Lo que está alto es el recall, que llegó a 1.0. El modelo prioriza detección, pero debe mejorar falsos positivos.

## 9. ¿Qué significa recall alto?
Significa que el modelo detecta la mayoría o todos los casos Over OLA en validación, pero puede incluir falsos positivos.

## 10. ¿Qué significa precision baja/moderada?
Significa que no todos los casos predichos como Over OLA realmente terminan siendo Over OLA. Es un punto de mejora operacional.

## 11. ¿Por qué TimeSeriesSplit?
Porque los incidentes tienen orden temporal. Usar TimeSeriesSplit evita entrenar con datos futuros para validar el pasado.

## 12. ¿Qué es early stopping?
Es detener el entrenamiento si el modelo deja de mejorar después de cierto número de iteraciones. En mi caso se usa `n_iter_no_change=8` y `tol≈0.000190`.

## 13. ¿Qué es pruning?
Es una forma de reducir complejidad del modelo. En árboles se usa `ccp_alpha` para podar ramas que no aportan suficiente mejora.

## 14. ¿Qué guardaste para reproducibilidad?
Guardé configuración, scripts, notebooks, logs, resultados, gráficos y artefactos. No subí data cruda por confidencialidad.

## 15. ¿Cuánta data estás manejando?
Para el modelado principal uso 10,819 incidentes válidos. Además tengo 4,030 alarmas actuales limpias como insumo complementario operativo.

## 16. ¿Qué significa branch operativo?
Es una segmentación operativa anonimizada de la red o zona. No es un branch de GitHub. Sirve para analizar si ciertos grupos tienen mayor riesgo de Over OLA.

## 17. ¿Qué aportan las ablaciones?
Permiten cambiar una sola parte del pipeline y medir si mejora o empeora. Así se identifica qué componente realmente mueve la métrica.

## 18. ¿Qué riesgo principal tiene tu modelo?
El riesgo principal es generar falsos positivos por priorizar recall. El plan es calibrar probabilidades y ajustar el threshold según costo operativo.

## 19. ¿Qué diferencia hay entre Sprint 6, Sprint 7 y Sprint 8?
Sprint 6 fue baseline y estructura inicial. Sprint 7 agregó HPO Random/Bayes y configuración ganadora. Sprint 8 agrega MLOps ligero, tablero de corridas, overfitting, ablaciones y reproducibilidad.

## 20. ¿Cuál es el siguiente paso?
Mejorar calibración, ajustar threshold, validar por branch, agregar señales de alarmas actuales y preparar un flujo reproducible más cercano a MLflow.
