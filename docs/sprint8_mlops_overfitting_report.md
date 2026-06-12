# Sprint 8 - MLOps ligero, overfitting y demo

## Objetivo
Agregar una capa de MLOps ligero al avance del Sprint 7: tablero de corridas, análisis de gap entrenamiento-validación, ablaciones, riesgos y reproducibilidad.

## Base utilizada
Se parte del entregable Sprint 7 HPO:
- Modelo ganador: `GradientBoostingClassifier`.
- Método ganador: Random Search.
- Trial ganador: 8.
- Target: `label_over_ola`.
- Validación: TimeSeriesSplit con 3 folds.

## Data
- Incidentes históricos válidos: 10,819.
- Positivos Over OLA: 3,505.
- Negativos On Time: 7,314.
- Branches anonimizados: 44.

## Tablero de corridas
Archivo principal: `results/experiment_dashboard_sprint8.csv`.

Este tablero registra:
- `exp_id`
- modelo
- features usadas
- métrica F1 train/validación
- gap train-validación
- average precision
- recall
- precision
- tiempo
- notas

## Overfitting
Archivo principal: `results/overfitting_gap_sprint8.csv`.

Se mide el gap:
`F1_train_mean - F1_val_mean`.

Un gap alto indica posible sobreajuste. Un gap bajo o negativo sugiere que el modelo no está sobreajustando de forma evidente, aunque también puede indicar bajo poder predictivo o necesidad de mejores features.

## Ablaciones
Archivo principal: `results/ablation_summary_sprint8.csv`.

Ablaciones realizadas:
- Todas las features con configuración HPO ganadora.
- Sin `branch_id`.
- Sin `reason_group`.
- Solo variables temporales.
- Variables operativas sin tiempo.

## Gráficos principales
- `fig_experiment_dashboard_sprint8.png`: tablero visual de corridas.
- `fig_overfitting_gap_sprint8.png`: gap train-validación.
- `fig_ablation_impact_sprint8.png`: impacto de ablaciones.
- `fig_precision_recall_sprint8.png`: curva PR.
- `fig_calibration_sprint8.png`: calibración.

## Conclusión
Este sprint fortalece la defensa del proyecto porque conecta HPO con MLOps ligero: se demuestra cómo se comparan corridas, cómo se controla overfitting, qué cambios mueven la métrica y cómo se reproduce el experimento.
