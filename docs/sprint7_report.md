# Reporte Sprint 7 - Corrección y mejora del repositorio

## 1. Contexto

El Sprint 7 responde a las observaciones del profesor sobre la calidad de datos, la comparación contra baseline, el análisis por branch y la necesidad de diagnósticos técnicos.

## 2. Cambios principales frente al Sprint 6

| Sprint 6 | Sprint 7 corregido |
|---|---|
| Dataset TX/IP parcial | Dataset TX/IP integrado: TX + IP |
| Comparación simple | Validación temporal de 3 folds |
| Baseline vs 2 modelos | Baseline vs Logistic Regression vs Random Forest con resumen por folds |
| Sin análisis por branch | Carpeta `branches/` y métricas por branch |
| Sin diagnóstico formal de calidad | `data_quality_report_sprint7.csv` |
| Sin ablation study | `ablation_study_sprint7.csv` |
| Sin importancia de variables | `feature_importance_random_forest_sprint7.csv` |
| Curva PR básica | Curva PR + calibración + learning curve |

## 3. Resultado técnico

Random Forest es adoptado como variante principal porque mejora el F1 y Average Precision respecto al baseline, aunque el baseline mantenga recall más alto.

La decisión no se basa en una sola métrica. Se analiza:

- precision;
- recall;
- F1;
- average precision;
- Brier score;
- latencia;
- estabilidad por folds.

## 4. Hallazgos

1. La data tiene valor, pero requiere control de calidad.
2. Existen inconsistencias entre duración/umbral/KPI que deben documentarse.
3. El análisis por branch es necesario porque el comportamiento no es homogéneo.
4. Las variables históricas por branch mejoran el modelo cuando se calculan solo con training.
5. El baseline es útil como referencia, pero no como solución final.

## 5. Próximos pasos

- Revisar manualmente inconsistencias críticas de KPI/duración.
- Calibrar probabilidades del Random Forest.
- Evaluar variables adicionales de alarmas actuales.
- Analizar drift por mes y por branch.
- Incorporar SHAP si el tiempo del sprint lo permite.
