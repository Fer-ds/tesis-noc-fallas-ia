# Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC

Repositorio académico de **Seminario de Tesis 2**. El objetivo es construir un pipeline reproducible para preparar datos operativos NOC, anonimizar información sensible y comparar modelos de inteligencia artificial orientados a detectar incidentes con riesgo de superar el OLA/SLA operativo.

## 1. Contexto del proyecto

El NOC recibe incidentes y alarmas de diferentes dominios tecnológicos, principalmente transmisión e IP. El problema investigado es que muchos eventos críticos se gestionan de forma reactiva: primero se registra la caída o degradación, luego se escala y finalmente se atiende. Esta tesis busca avanzar hacia una detección más proactiva, usando patrones históricos de incidentes TX/IP y un nuevo snapshot de alarmas actuales.

**Objetivo técnico del sprint 6:** mejorar la claridad del repositorio, integrar una segunda fuente de datos de alarmas actuales y comparar una línea base contra dos variantes A/B.

## 2. Fuentes de datos usadas

Los archivos Excel originales **no se suben al repositorio** por confidencialidad. En su lugar, se publican datasets procesados y anonimizados.

| Fuente | Archivo procesado publicado | Uso en el sprint |
|---|---|---|
| Incidentes históricos TX/IP | `data/processed/incidents_noc_tx_ip_anon_sprint6.csv` | Entrenamiento y validación de modelos |
| Alarmas actuales | `data/processed/current_alarms_anon_sprint6.csv` | Nueva fuente para análisis y priorización preliminar |
| Resumen técnico | `data/processed/dataset_summary_sprint6.json` | Evidencia de filas, privacidad y variable objetivo |

## 3. Variable objetivo y métrica central

La variable objetivo principal es:

```text
label_over_ola = 1 si duration_hours > sla_threshold_hours
label_over_ola = 0 si duration_hours <= sla_threshold_hours
```

La métrica central elegida es **Recall Over OLA**, porque para una operación NOC es más importante detectar la mayor cantidad posible de incidentes que podrían incumplir el OLA, incluso si esto implica revisar algunos falsos positivos.

## 4. Estructura del repositorio

```text
.
├── data/
│   ├── raw/                     # No subir excels originales; solo placeholder
│   └── processed/               # Datasets anonimizados para GitHub
├── docs/
│   ├── data_dictionary_sprint6.md
│   ├── sprint6_report.md
│   └── privacy_and_anonymization.md
├── notebooks/
│   └── 01_sprint6_ab_experiments.ipynb
├── results/
│   ├── metrics_ab_sprint6.csv
│   ├── pr_curve_sprint6.png
│   └── current_alarms_top_risk_sample.csv
├── logs/
│   └── sprint6_run.log
├── src/
│   ├── prepare_datasets.py
│   └── train_sprint6_ab.py
├── requirements.txt
└── README.md
```

## 5. Experimentos A/B Sprint 6

| Variante | Cambio realizado | Propósito |
|---|---|---|
| Baseline | Regla operacional por prioridad, tipo de incidente, trouble type y SLA corto | Tener referencia simple y explicable |
| Var1 | Logistic Regression con One-Hot Encoding, variables temporales, SLA y balanceo de clases | Modelo interpretable y rápido |
| Var2 | Random Forest con branch anonimizado y umbral 0.40 | Priorizar recall para eventos Over OLA |

Resultados reproducibles en `results/metrics_ab_sprint6.csv`.

## 6. Resultado comparativo principal

La variante con mejor Recall Over OLA en esta corrida fue **Baseline (Regla operacional)**, con:

- Recall Over OLA: **1.0**
- Precision Over OLA: **0.1922**
- F1 Over OLA: **0.3224**
- Average Precision: **0.185**

El gráfico `results/pr_curve_sprint6.png` muestra la curva Precision-Recall de la variante seleccionada.

## 7. Reproducibilidad

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python src/prepare_datasets.py
python src/train_sprint6_ab.py
```

El split usado es temporal 80/20, con seed fijo 42. Esto evita mezclar eventos futuros dentro del entrenamiento y reduce el riesgo de leakage.

## 8. Nota de privacidad

Este repositorio no debe contener tickets reales, nombres de responsables, coordenadas, rutas, enlaces reales, códigos internos completos ni descripciones textuales operativas sensibles. Los archivos publicados son versiones procesadas y anonimizadas.
