# Modelos de IA para detección proactiva de fallas físicas en entornos NOC

Repositorio inicial para el trabajo de Seminario de Tesis 2.

## Tema

**Modelos de inteligencia artificial para la detección proactiva de fallas físicas en infraestructura de red de telecomunicaciones en entornos NOC.**

## Objetivo

Desarrollar y validar un pipeline experimental inicial para analizar incidentes NOC TX/IP, comparar un modelo base contra variantes y evaluar métricas de clasificación relacionadas con incidentes que exceden el tiempo objetivo de atención.

## Privacidad de datos

El archivo original de incidentes **no se sube a GitHub**.  
Este repositorio contiene únicamente una versión **anonimizada/procesada**:

`data/processed/incidentes_noc_anon_semana5.csv`

Se eliminaron o sustituyeron:

- tickets reales;
- códigos reales de rutas/enlaces;
- nombres de responsables;
- coordenadas;
- detalle interno de solución GNOC;
- identificadores sensibles de operación.

## Estructura

```text
tesis-noc-fallas-ia/
├── data/
│   ├── raw/
│   │   └── README.md
│   ├── processed/
│   │   └── incidentes_noc_anon_semana5.csv
│   └── data_dictionary.md
├── docs/
│   └── reporte_semana5.md
├── logs/
│   └── experimentos_semana5.md
├── notebooks/
│   └── 01_experimentos_semana5.ipynb
├── results/
│   ├── metricas_semana5.csv
│   └── pr_curve_semana5.png
├── src/
├── .gitignore
├── README.md
└── requirements.txt
```

## Dataset procesado

- Registros útiles: **10,819**
- Target principal: `label_over_time`
  - `1`: Over Time
  - `0`: On Time
- Target secundario: `label_critical`
  - `1`: Prioridad crítica
  - `0`: Prioridad mayor/menor

Distribución del target principal:

| Clase | Cantidad |
|---|---:|
| On Time | 7,314 |
| Over Time | 3,505 |

## Experimentos Semana 5

Se ejecutaron tres variantes:

1. **Baseline:** Regresión logística con variables categóricas operativas básicas.
2. **Var1:** Random Forest con variables operativas + temporales + ubicación anonimizada.
3. **Var2:** Random Forest con `class_weight=balanced` para mejorar la detección de la clase Over Time.

## Resultados comparables

| experimento   | modelo                 |   accuracy |   precision |   recall |     f1 |   average_precision |   tiempo_entrenamiento_seg |
|:--------------|:-----------------------|-----------:|------------:|---------:|-------:|--------------------:|---------------------------:|
| Baseline      | LogisticRegression     |     0.6839 |      0.5436 |   0.1512 | 0.2366 |              0.4392 |                       0.07 |
| Var1          | RandomForestClassifier |     0.6867 |      0.6075 |   0.0927 | 0.1609 |              0.502  |                       0.73 |
| Var2          | RandomForestClassifier |     0.6608 |      0.4807 |   0.5849 | 0.5277 |              0.5123 |                       0.65 |

## Criterio de métrica principal

La métrica principal seleccionada fue **Recall**, porque en un entorno NOC es importante detectar la mayor cantidad posible de incidentes con riesgo de exceder el tiempo objetivo. Un falso negativo puede implicar no priorizar un incidente que luego termina fuera de KPI.

## Control de leakage

Para el entrenamiento predictivo de `label_over_time` no se usaron variables que revelen el resultado final, como:

- `kpi`;
- `status`;
- `duration_hours`;
- `label_critical`;
- `incident_id`.

Las transformaciones se ajustaron dentro del pipeline usando solo el conjunto de entrenamiento.

## Validación

Se utilizó validación **holdout estratificada** con 80% entrenamiento y 20% prueba para mantener la proporción entre incidentes On Time y Over Time.

## Cómo ejecutar

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_experimentos_semana5.ipynb
```


## Visualizaciones Semana 5

El repositorio incluye una comparación gráfica de modelos en `results/comparacion_clasificacion_semana5.png`, donde se observan las métricas Accuracy, Recall y F1-score para el baseline y las variantes experimentales.
