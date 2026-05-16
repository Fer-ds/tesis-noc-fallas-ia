# Reporte breve - Entrega Semana 5

## 1. Avance realizado

Se creó la estructura inicial del repositorio de tesis y se incorporó un dataset anonimizado de incidentes NOC TX/IP para ejecutar los primeros experimentos comparables.

## 2. Dataset

La base procesada contiene **10,819 registros útiles**.  
Por confidencialidad, no se publica el Excel original. Se generó una versión anonimizada en CSV, eliminando tickets, coordenadas, nombres y códigos reales.

## 3. Pipeline experimental

El pipeline considera:

1. carga del dataset;
2. separación de variables predictoras y target;
3. split holdout estratificado;
4. transformación de variables categóricas mediante One Hot Encoding;
5. entrenamiento de modelos;
6. evaluación con Accuracy, Precision, Recall, F1 y Average Precision;
7. generación de curva Precision-Recall.

## 4. Experimentos A/B

| Experimento | Descripción |
|---|---|
| Baseline | Regresión logística con features operativas básicas. |
| Var1 | Random Forest con features operativas, temporales y ubicación anonimizada. |
| Var2 | Random Forest balanceado para mejorar recall en clase Over Time. |

## 5. Resultados

| experimento   | modelo                 |   accuracy |   precision |   recall |     f1 |   average_precision |   tiempo_entrenamiento_seg |
|:--------------|:-----------------------|-----------:|------------:|---------:|-------:|--------------------:|---------------------------:|
| Baseline      | LogisticRegression     |     0.6839 |      0.5436 |   0.1512 | 0.2366 |              0.4392 |                       0.07 |
| Var1          | RandomForestClassifier |     0.6867 |      0.6075 |   0.0927 | 0.1609 |              0.502  |                       0.73 |
| Var2          | RandomForestClassifier |     0.6608 |      0.4807 |   0.5849 | 0.5277 |              0.5123 |                       0.65 |

## 6. Métrica principal

La métrica principal seleccionada fue **Recall** debido a que el objetivo operativo es detectar la mayor cantidad posible de incidentes que puedan exceder el KPI de atención.

## 7. Validación

Se aplicó validación **holdout estratificada**, manteniendo proporciones entre incidentes On Time y Over Time.

## 8. Control de leakage

No se utilizaron variables que revelen directamente el resultado, tales como `kpi`, `duration_hours`, `status`, `label_critical` o `incident_id`.

## 9. Conclusión preliminar

La variante Var2 mejora significativamente el recall frente al baseline, lo cual es relevante en el contexto NOC porque permite identificar más incidentes con riesgo de caer en Over Time. Sin embargo, se requiere seguir ajustando features y validación temporal para acercar el modelo a un escenario operativo real.
