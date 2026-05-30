# Correcciones aplicadas según observaciones del profesor - Sprint 7

## Observación 1: La data no es la mejor

**Acción aplicada:**  
Se agregó un reporte formal de calidad de datos en:

```text
results/data_quality_report_sprint7.csv
```

Este reporte identifica:
- registros fuera del rango temporal 2024-2026;
- etiquetas KPI faltantes;
- campos críticos nulos;
- inconsistencias entre duración, umbral OLA y KPI;
- cantidad final de registros válidos para modelamiento.

**Decisión técnica:**  
Para el modelamiento se trabaja solo con registros 2024-2026 y con etiqueta KPI válida `On Time` / `Over Time`.

## Observación 2: No es razonable que Machine Learning pierda tanto frente a una regla manual

**Acción aplicada:**  
Se corrigió la lectura de resultados. El baseline tiene mayor recall, pero menor precisión, menor F1 y menor Average Precision. La comparación ya no se hace solo por recall.

**Resultado promedio por folds:**

| Modelo | Precision | Recall | F1 | Average Precision |
|---|---:|---:|---:|---:|
| Baseline | 0.3203 | 0.9594 | 0.4802 | 0.3589 |
| Logistic Regression | 0.3754 | 0.8296 | 0.5162 | 0.4502 |
| Random Forest | 0.4014 | 0.7967 | 0.5313 | 0.4561 |

**Conclusión:**  
El baseline detecta casi todo, pero genera muchas falsas alertas. Random Forest mejora el equilibrio operativo.

## Observación 3: Trabajar el análisis por branch

**Acción aplicada:**  
Se creó la carpeta:

```text
branches/
```

Incluye:
- `branch_summary_sprint7.csv`;
- fichas `branch_*.md` para los branches con mayor volumen;
- métricas por branch en `results/branch_metrics_sprint7.csv`.

## Observación 4: Revisar variables creadas / feature engineering

**Acción aplicada:**  
Se documentaron las variables creadas en:

```text
docs/feature_engineering_sprint7.md
```

Se agregaron variables:
- temporales;
- operativas;
- branch;
- riesgo histórico por branch;
- riesgo histórico por causa.

Las variables históricas se calculan solo sobre el training set de cada fold, para evitar leakage.

## Observación 5: Mostrar diagnósticos

**Acción aplicada:**  
Se agregaron diagnósticos solicitados en clase:

- Ablation study: `results/ablation_study_sprint7.csv`
- Importancia de variables: `results/feature_importance_random_forest_sprint7.csv`
- Curva Precision-Recall: `results/fig_precision_recall_sprint7.png`
- Curva de calibración: `results/fig_calibration_sprint7.png`
- Learning curve: `results/fig_learning_curve_sprint7.png`

## Frase para exposición

> Profesor, corregí el enfoque anterior. Ya no presento solo una corrida ni una comparación simple por recall. Ahora tengo diagnóstico de calidad de datos, validación temporal por folds, análisis por branch, ablation study, importancia de variables, curva de calibración y learning curve. El baseline mantiene recall alto, pero Random Forest mejora el F1 y el Average Precision, por lo que es más útil como herramienta de priorización para el NOC.
