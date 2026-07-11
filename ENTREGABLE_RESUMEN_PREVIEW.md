# Resumen del entregable - Seminario de Tesis 2

**Título:** Aplicación de modelos de inteligencia artificial para la detección y predicción proactiva de fallas físicas en infraestructuras de red de telecomunicaciones en entornos NOC.

**Autor:** Fernando Joel Blaz Aleman  
**Programa:** Maestría en Ciencias con mención en Inteligencia Artificial  
**Periodo documentado:** Sprint 6, Sprint 7 y Sprint 8

## 1. Problema de investigación

El trabajo aborda la gestión reactiva de alarmas e incidentes en un Centro de Operaciones de Red. El objetivo es apoyar la priorización temprana de incidentes NOC TX/IP que presentan riesgo de superar compromisos operativos asociados a OLA/SLA.

## 2. Objetivo general

Desarrollar y validar un modelo de inteligencia artificial para la detección y predicción proactiva de fallas físicas en infraestructuras de red de telecomunicaciones en entornos NOC, mediante un pipeline experimental reproducible basado en datos operativos históricos y prácticas de MLOps ligero.

## 3. Datos y variable objetivo

La variable objetivo del avance experimental es `label_over_ola`, que clasifica cada incidente como **Over OLA** u **On Time**.

| Indicador | Valor |
|---|---:|
| Registros válidos para modelado | 10,819 |
| Casos Over OLA | 3,505 |
| Casos On Time | 7,314 |
| Tasa positiva aproximada | 32.4% |
| Branches operativos anonimizados | 44 |
| Rango temporal | 2022-08-14 a 2026-04-24 |
| Alarmas actuales limpias complementarias | 4,030 |

## 4. Avance por sprints

| Sprint | Avance principal |
|---|---|
| Sprint 6 | Baseline, depuración, análisis de branch operativo y ordenamiento del repositorio. |
| Sprint 7 | Búsqueda de hiperparámetros con Random Search y búsqueda Bayesiana; logs, top-k y artefacto ganador. |
| Sprint 8 | MLOps ligero, tablero de corridas, análisis de sobreajuste, ablaciones y reproducibilidad. |

## 5. Protocolo experimental

| Elemento | Configuración |
|---|---|
| Validación | `TimeSeriesSplit(n_splits=3)` |
| Semilla | 42 |
| Métrica principal | F1 promedio sobre `label_over_ola` |
| Modelo optimizado | `GradientBoostingClassifier` |
| Métodos de búsqueda | Random Search y búsqueda Bayesiana |
| Presupuesto HPO | 12 trials Random + 12 trials Bayes = 24 trials |
| Control de costo | Pruning y early stopping |
| Evidencia | logs, resultados, artefactos, configuración y notebooks |

## 6. Resultado preliminar del Sprint 7

| Elemento | Resultado |
|---|---|
| Modelo ganador | `GradientBoostingClassifier` |
| Método ganador | Random Search |
| Trial ganador | 8 |
| F1 promedio | 0.4986 |
| Precision | 0.3333 |
| Recall | 1.0000 |
| Average Precision | 0.4395 |
| Balanced Accuracy | 0.5000 |

La lectura técnica es que el modelo prioriza la detección de casos **Over OLA**. La mejora pendiente se concentra en calibración de probabilidades, ajuste del threshold y reducción de falsos positivos.

## 7. Evidencia Sprint 8

| Componente | Implementación en el repositorio |
|---|---|
| Configuración reproducible | `config/mlops_demo_sprint8_config.json` |
| Tablero de corridas | `results/experiment_dashboard_sprint8.csv` |
| Logs y métricas por fold | `logs/mlops_runs_sprint8.csv` y `logs/overfitting_by_fold_sprint8.csv` |
| Control de sobreajuste | `results/overfitting_gap_sprint8.csv` y `fig_overfitting_gap_sprint8.png` |
| Ablaciones | `results/ablation_summary_sprint8.csv` y `fig_ablation_impact_sprint8.png` |
| Artefactos | `artifacts/model_card_sprint8.md` y `reproducibility_manifest_sprint8.json` |
| Script reproducible | `src/run_sprint8_mlops_demo.py` |

## 8. Conclusión preliminar

El avance pasó de una propuesta conceptual a un pipeline experimental con datos procesados, validación temporal, HPO, control de sobreajuste, ablaciones y trazabilidad. El aporte principal del Sprint 8 es que el resultado ya no queda como una métrica aislada, sino como un flujo reproducible y defendible en repositorio.
