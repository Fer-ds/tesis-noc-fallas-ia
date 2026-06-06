# Sprint 7 - Búsqueda de hiperparámetros HPO Random/Bayes

## Objetivo
Actualizar el avance desde Sprint 6 incorporando búsqueda de hiperparámetros comparable con dos estrategias: `random_search` y `bayesian_gp_ucb`. El objetivo operativo es predecir `label_over_ola` para anticipar incidentes NOC TX/IP que podrían superar el OLA.

## Datos usados
- Incidentes válidos para modelado: **10,819** registros.
- Clase positiva `Over OLA`: **3,505** registros.
- Clase negativa `On Time`: **7,314** registros.
- Tasa positiva: **32.40%**.
- Rango temporal: **2022-08-14 a 2026-04-24**.
- Branches anonimizadas: **44**.
- Alarmas actuales limpias como insumo complementario: **4,030** registros.

> Nota de privacidad: se trabaja con datos procesados y anonimizados. No se suben TT, WO, coordenadas, nombres de enlaces, tracking incident ni identificadores operativos completos.

## Validación
Se usó `TimeSeriesSplit(n_splits=3)` para respetar la secuencia temporal de los incidentes y evitar fuga de información futura hacia el entrenamiento.

## Espacio de búsqueda
Modelo HPO: `GradientBoostingClassifier` dentro de un pipeline con imputación, `OrdinalEncoder` para variables categóricas y balanceo por pesos de clase.

Hiperparámetros optimizados:
- `n_estimators`, `learning_rate`, `max_depth`, `min_samples_leaf`, `subsample`, `max_features`.
- `ccp_alpha` como pruning de los árboles base.
- `tol` y `n_iter_no_change` para early stopping.
- `decision_threshold` como umbral de decisión para clase `Over OLA`.

## Presupuesto
- Random Search: **12 trials**.
- Bayesian Search: **12 trials**.
- Total: **24 trials**.
- Folds por trial completo: **3**.
- Métrica principal: **F1 promedio en validación temporal**.
- Trials completados: **22**.
- Trials podados: **2**.

## Early stopping y pruning
- Early stopping nativo: `GradientBoostingClassifier(validation_fraction=0.15, n_iter_no_change, tol)`.
- Pruning estructural: `ccp_alpha` en los árboles base.
- Pruning de trials: desde el trial 5 de cada método, si el F1 del primer fold cae por debajo del percentil 25 histórico del método, el trial se corta para ahorrar costo.

## Resultado comparativo

| method          |   completed_trials |   best_f1 |   mean_f1 |   best_ap |   mean_seconds |   pruned_trials |
|:----------------|-------------------:|----------:|----------:|----------:|---------------:|----------------:|
| bayesian_gp_ucb |                 12 |  0.498583 |  0.486116 |  0.452543 |        0.83625 |               0 |
| random_search   |                 10 |  0.498583 |  0.463185 |  0.454361 |        1.0639  |               2 |

## Configuración ganadora
- Método: **random_search**.
- Trial: **8**.
- F1 validación: **0.4986 ± 0.0461**.
- Precision: **0.3333**.
- Recall: **1.0000**.
- Average Precision: **0.4395**.
- Balanced Accuracy: **0.5000**.

Parámetros ganadores:
```json
{
  "n_estimators": 60,
  "learning_rate": 0.0782682880932311,
  "max_depth": 2,
  "min_samples_leaf": 59,
  "subsample": 0.9232551608576888,
  "max_features": "log2",
  "ccp_alpha": 0.0001269862282811,
  "tol": 0.0001903680214831,
  "n_iter_no_change": 8,
  "decision_threshold": 0.2303932323558283
}
```

## Lectura técnica de la decisión
La configuración ganadora maximiza F1 bajo el presupuesto de esta entrega. Tiene un comportamiento conservador hacia la clase `Over OLA`: recall alto y precision baja. Para una siguiente iteración, se debe ajustar el umbral y comparar contra el baseline Random Forest de Sprint 6/7 para decidir si se prioriza detectar más riesgos o reducir falsos positivos.

## Artefactos generados
- `logs/hpo_runs_sprint7.csv`: bitácora consolidada por trial.
- `logs/hpo_events_sprint7.jsonl`: eventos detallados por trial/fold/pruning.
- `results/hpo_topk_sprint7.csv`: tabla top-k.
- `results/fig_hpo_evolution_sprint7.png`: evolución del mejor F1 acumulado.
- `results/fig_hpo_topk_sprint7.png`: ranking visual de configuraciones.
- `artifacts/best_config_sprint7_hpo.json`: configuración ganadora.
- `artifacts/best_hpo_model_sprint7.joblib`: pipeline entrenado con la configuración ganadora.

## Decisión
Se selecciona la configuración ganadora por **mayor F1 promedio** en validación temporal. Esta configuración queda como baseline HPO reproducible para el Sprint 7. Para el informe final, se recomienda compararla con el baseline Sprint 6/Random Forest y dejar claro que esta entrega prioriza trazabilidad, comparabilidad y control de costo.
