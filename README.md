# Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC

Repositorio académico de **Seminario de Tesis 2**.  
El objetivo es construir un pipeline reproducible para preparar datos operativos NOC, anonimizar información sensible, analizar el comportamiento por **branch** y comparar modelos de inteligencia artificial orientados a priorizar incidentes con riesgo de superar el OLA/SLA operativo.

## Estado del repositorio

Esta versión corresponde a la **corrección del Sprint 7**, realizada a partir de las últimas observaciones:

1. La data anterior no estaba lo suficientemente depurada ni diagnosticada.
2. No basta con que una regla manual tenga mayor recall; se debe comparar con métricas completas.
3. El repositorio debe estar ordenado por branch.
4. Se debe justificar mejor el feature engineering.
5. Se deben mostrar diagnósticos: ablation study, importancia de las variables, curvas de aprendizaje/calibración y control de leakage.

## 1. Fuentes de datos

Los Excel originales no se publican por confidencialidad operativa.

| Fuente | Archivo procesado publicado | Uso |
|---|---|---|
| Incidentes históricos TX/IP | `data/processed/incidents_noc_tx_ip_clean_sprint7.csv` | Modelamiento supervisado |
| Alarmas actuales | `data/processed/current_alarms_clean_sprint7.csv` | Priorización preliminar y análisis complementario |
| Resumen por branch | `data/processed/branch_summary_sprint7.csv` | Análisis por branch |
| Resumen técnico | `data/processed/dataset_summary_sprint7.json` | Evidencia de filas, privacidad y target |

## 2. Variable objetivo

La variable objetivo es:

```text
label_over_ola = 1  -> incidente Over Time / fuera del OLA operativo
label_over_ola = 0  -> incidente On Time / dentro del OLA operativo
```

En esta versión se usa el campo KPI operativo como etiqueta oficial.  
También se valida la consistencia contra duración y umbral OLA, dejando evidencia en:

```text
results/data_quality_report_sprint7.csv
```

## 3. Feature engineering

Se incorporaron variables creadas sin usar información futura:

| Grupo | Variables |
|---|---|
| Temporales | `year`, `quarter`, `month`, `week_of_year`, `day_of_week`, `hour`, `is_weekend`, `is_night` |
| Operativas | `priority`, `type_of_incident`, `trouble_type`, `incident_type`, `network_id`, `reason_group` |
| Branch | `branch_id`, `branch_over_ola_rate_train`, `branch_incident_count_train` |
| Riesgo histórico | `reason_over_ola_rate_train` |
| SLA/OLA | `sla_threshold_hours` |

Las variables históricas por branch y por causa se calculan **solo con el training set** en cada fold. Esto evita leakage.

## 4. Validación y comparación

Se reemplaza la comparación simple por una validación temporal de 3 folds:

```text
Baseline vs Logistic Regression vs Random Forest
```

Archivos principales:

```text
results/model_comparison_by_fold_sprint7.csv
results/model_comparison_summary_sprint7.csv
results/ablation_study_sprint7.csv
```

Resumen de resultados promedio por fold:

| Modelo | Precision media | Recall medio | F1 medio | Average Precision |
|---|---:|---:|---:|---:|
| Baseline regla operacional | 0.3203 | 0.9594 | 0.4802 | 0.3589 |
| Logistic Regression | 0.3754 | 0.8296 | 0.5162 | 0.4502 |
| Random Forest | 0.4014 | 0.7967 | 0.5313 | 0.4561 |

**Lectura técnica:**  
El baseline conserva un recall alto, pero tiene baja precisión y menor F1. Random Forest mejora el equilibrio entre detectar casos Over OLA y reducir falsas alertas.

## 5. Diagnósticos agregados

| Diagnóstico | Archivo |
|---|---|
| Data quality | `results/data_quality_report_sprint7.csv` |
| Ablation study | `results/ablation_study_sprint7.csv` |
| Importancia de variables | `results/feature_importance_random_forest_sprint7.csv` |
| Curva Precision-Recall | `results/fig_precision_recall_sprint7.png` |
| Calibración | `results/fig_calibration_sprint7.png` |
| Learning curve | `results/fig_learning_curve_sprint7.png` |
| Métricas por branch | `results/branch_metrics_sprint7.csv` |
| Tasa Over OLA por branch | `results/fig_branch_over_ola_rate_sprint7.png` |

## 6. Análisis por branch

La carpeta `branches/` contiene el resumen por branch y fichas para los branches con mayor volumen.

```text
branches/
├── README.md
├── branch_summary_sprint7.csv
└── branch_*.md
```

Esto permite explicar que el análisis ya no se revisa solamente de manera global, sino también por sede/branch, como solicitó el profesor.

## 7. Estructura del repositorio

```text
.
├── data/
│   ├── raw/                         # No subir Excel crudos
│   └── processed/
├── docs/
│   ├── correcciones_observaciones_profesor_sprint7.md
│   ├── data_quality_plan_sprint7.md
│   ├── feature_engineering_sprint7.md
│   └── sprint7_report.md
├── notebooks/
│   ├── 00_data_quality_branch_eda_sprint7.ipynb
│   └── 01_model_diagnostics_sprint7.ipynb
├── results/
├── branches/
├── src/
│   ├── prepare_datasets_sprint7.py
│   └── train_sprint7_diagnostics.py
├── logs/
├── requirements.txt
└── README.md
```

## 8. Reproducibilidad

Desde la raíz del repositorio:

```bash
pip install -r requirements.txt
python src/train_sprint7_diagnostics.py
```

El script usa los datasets ya procesados de `data/processed/` y genera los archivos de `results/`.

## 9. Nota de privacidad

Este repositorio no debe contener tickets reales, nombres de responsables, coordenadas, rutas, enlaces reales, códigos internos completos ni descripciones operativas sensibles.  
Los archivos publicados son versiones procesadas y anonimizadas.
