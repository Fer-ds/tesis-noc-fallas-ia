# Entregable Seminario de Tesis 2 - Sprint 8

Esta carpeta contiene el entregable académico actualizado del proyecto y la matriz de consistencia solicitada para Seminario de Tesis 2.

## Archivos

| Archivo | Descripción |
|---|---|
| `Entregable_Seminario_Tesis2_Blaz_Aleman_FINAL_con_matriz_consistencia.docx` | Documento principal del entregable, con la matriz de consistencia anexada al final. |
| `Matriz_consistencia_Seminario_Tesis2_IA_Sprint8.docx` | Matriz de consistencia en archivo independiente, para revisión rápida o entrega separada. |

## Relación con el avance del repositorio

El entregable se apoya en el avance experimental desarrollado hasta el Sprint 8:

- Sprint 6: preparación de datos, baseline inicial, diagnóstico y ordenamiento del repositorio.
- Sprint 7: búsqueda de hiperparámetros con Random Search y búsqueda Bayesiana, validación temporal, logs y artefacto ganador.
- Sprint 8: MLOps ligero, tablero de corridas, control de sobreajuste, ablaciones y reproducibilidad.

La matriz de consistencia no es una línea de trabajo aparte. Resume y ordena metodológicamente lo que ya se está implementando en el pipeline:

- Problema y objetivo general del estudio.
- Objetivos específicos vinculados al desempeño predictivo, ablaciones y control de sobreajuste.
- Hipótesis, variables independientes, variable dependiente, variables de control e indicadores.
- Evidencia del Sprint 8: `results/`, `logs/`, `artifacts/`, `config/`, `src/` y `notebooks/`.
- Plan de generalización fuera de muestra o Plan B mediante validación temporal, backtesting, análisis por branch y shadow mode.

## Evidencia técnica relacionada

Los principales archivos de soporte del Sprint 8 se encuentran en:

- `config/mlops_demo_sprint8_config.json`
- `logs/mlops_runs_sprint8.csv`
- `logs/overfitting_by_fold_sprint8.csv`
- `results/experiment_dashboard_sprint8.csv`
- `results/ablation_summary_sprint8.csv`
- `results/overfitting_gap_sprint8.csv`
- `artifacts/model_card_sprint8.md`
- `notebooks/03_mlops_overfitting_demo_sprint8.ipynb`
- `src/run_sprint8_mlops_demo.py`

## Nota de privacidad

No se publican datos crudos, tickets reales, coordenadas, nombres de enlaces, tracking incidents completos ni identificadores sensibles. El entregable y la matriz usan resultados agregados, datos procesados/anonimizados y referencias a artefactos reproducibles del repositorio.
