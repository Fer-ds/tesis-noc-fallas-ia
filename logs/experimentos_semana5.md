# Log de experimentos - Semana 5

## Fecha de ejecución

Generado para la entrega de Semana 5.

## Dataset

Archivo usado:

`data/processed/incidentes_noc_anon_semana5.csv`

Total de registros útiles: **10,819**

El dataset fue anonimizado antes de preparar los experimentos. No se incluye el Excel original ni campos sensibles.

## Target principal

`label_over_time`

- `1`: incidente Over Time
- `0`: incidente On Time

## Split

- Método: holdout estratificado
- Entrenamiento: 8,655 registros
- Prueba: 2,164 registros
- Random state: 42

## Experimento 1: Baseline

Modelo: Logistic Regression  
Features:

- area
- priority
- type_of_incident
- trouble_type
- incident_type
- network_id

Objetivo: establecer una línea base simple.

## Experimento 2: Var1

Modelo: Random Forest  
Cambio respecto al baseline: se añadieron variables temporales y de ubicación anonimizada.

Features añadidas:

- year
- quarter
- month
- week_of_year
- branch_id
- route_id
- reason_group

## Experimento 3: Var2

Modelo: Random Forest con `class_weight=balanced`  
Cambio respecto a Var1: ajuste por desbalance de clases para mejorar el recall de incidentes Over Time.

## Resultados

| experimento   | modelo                 |   accuracy |   precision |   recall |     f1 |   average_precision |   tiempo_entrenamiento_seg |
|:--------------|:-----------------------|-----------:|------------:|---------:|-------:|--------------------:|---------------------------:|
| Baseline      | LogisticRegression     |     0.6839 |      0.5436 |   0.1512 | 0.2366 |              0.4392 |                       0.07 |
| Var1          | RandomForestClassifier |     0.6867 |      0.6075 |   0.0927 | 0.1609 |              0.502  |                       0.73 |
| Var2          | RandomForestClassifier |     0.6608 |      0.4807 |   0.5849 | 0.5277 |              0.5123 |                       0.65 |

## Gráfico generado

`results/pr_curve_semana5.png`

## Confirmación de cero leakage

No se usaron como predictores las variables `kpi`, `duration_hours`, `status`, `label_critical` ni `incident_id`.

`duration_hours` se conserva en el dataset solo para análisis descriptivo posterior, no para entrenamiento del target `label_over_time`.

## Próximo paso

Revisar el impacto de features históricas calculadas solo con entrenamiento, por ejemplo frecuencia histórica por branch/ruta/tipo de incidente, evitando usar información futura.
