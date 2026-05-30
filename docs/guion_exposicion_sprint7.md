# Guion de exposición Sprint 7

## Apertura

Profesor, esta entrega corrige la observación anterior. Ya no presento solo una comparación simple por recall. Ahora mejoré la calidad de datos, ordené el análisis por branch y agregué diagnósticos técnicos: ablation study, importancia de variables, curva Precision-Recall, calibración y learning curve.

## Qué ha cambiado

Antes el repositorio trabajaba con una versión más simple del dataset y una comparación baseline vs modelos. Ahora integro TX + IP, proceso alarmas actuales, genero un resumen por branch y uso validación temporal de 3 folds.

## Qué estoy comparando

Estoy comparando tres enfoques:

1. Baseline: regla operacional manual.
2. Logistic Regression: modelo interpretable.
3. Random Forest: modelo de árboles con variables temporales, operativas y branch.

## Qué estoy demostrando

Estoy demostrando que el baseline tiene recall alto, pero no es suficiente porque genera muchas falsas alertas. Random Forest mejora el F1 y el Average Precision, por eso es más útil como herramienta de priorización NOC.

## Qué carpeta mostrar

Orden sugerido:

1. `README.md`
2. `docs/correcciones_observaciones_profesor_sprint7.md`
3. `results/data_quality_report_sprint7.csv`
4. `branches/README.md`
5. `notebooks/00_data_quality_branch_eda_sprint7.ipynb`
6. `notebooks/01_model_diagnostics_sprint7.ipynb`
7. `results/model_comparison_summary_sprint7.csv`
8. `results/ablation_study_sprint7.csv`
9. `results/feature_importance_random_forest_sprint7.csv`
10. `src/train_sprint7_diagnostics.py`

## Frase de cierre

En resumen, esta corrección convierte el repositorio en un pipeline más defendible: datos depurados, análisis por branch, variables creadas sin leakage, validación temporal, modelos comparados por folds y diagnósticos técnicos para justificar qué features y qué modelo se quedan.
