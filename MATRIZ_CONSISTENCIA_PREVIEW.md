# Matriz de consistencia - Sprint 8

**Proyecto:** Modelos de inteligencia artificial para la detección proactiva de fallas físicas en infraestructura de red de telecomunicaciones en entornos NOC.

## Planteamiento general

| Elemento | Descripción |
|---|---|
| Problema / pregunta general | ¿En qué medida un pipeline reproducible de IA, entrenado con incidentes históricos NOC TX/IP, permite detectar proactivamente incidentes con riesgo de incumplir OLA (Over OLA) y sostener su desempeño bajo validación temporal? |
| Objetivo general | Desarrollar, optimizar y validar un pipeline de IA para clasificar incidentes NOC TX/IP como Over OLA u On Time, utilizando variables operativas y temporales, validación temporal y MLOps ligero para asegurar trazabilidad y control de sobreajuste. |
| Hipótesis general | Un pipeline de IA con variables operativas y temporales, evaluado con validación temporal y trazabilidad MLOps, permite detectar incidentes con riesgo de Over OLA con desempeño medible en F1, precision y recall, y con control explícito del gap train-validación. |
| Base Sprint 8 | 10,819 incidentes válidos; 3,505 Over OLA; 7,314 On Time; tasa positiva 32.4%; 44 branches anonimizados; rango 2022-08-14 a 2026-04-24. Target: `label_over_ola`. Validación: `TimeSeriesSplit(n_splits=3)`, seed 42. Métrica principal: F1 de validación temporal. |

## Matriz por objetivos específicos

| Objetivo específico | Hipótesis específica | Variable independiente (VI) | Variable dependiente (VD) | Variables de control | Indicadores / escala | Evidencia Sprint 8 |
|---|---|---|---|---|---|---|
| OE1. Evaluar el desempeño predictivo del pipeline de IA para clasificar incidentes NOC como Over OLA u On Time. | H1. Las configuraciones de IA con todas las variables operativas y temporales obtienen mejor desempeño de validación temporal que configuraciones parciales o no optimizadas. | Condición experimental del modelo/pipeline: tipo de modelo, configuración de hiperparámetros y threshold de decisión. | Desempeño predictivo para la clase crítica Over OLA. | Mismo dataset anonimizado, mismo target `label_over_ola`, misma partición temporal, mismo seed 42, mismo preprocesamiento base y mismas métricas. | F1 de validación temporal, precision, recall, average precision, balanced accuracy y Brier. Escala 0-1. | Dashboard de corridas Sprint 8. RF all features F1_val aprox. 0.6096; GBC HPO all features F1_val aprox. 0.5796. Modelo Sprint 7: `GradientBoostingClassifier` + `OrdinalEncoder` + `SimpleImputer`, Trial 8 Random Search. |
| OE2. Determinar qué grupos de variables mueven la métrica mediante ablaciones controladas. | H2. El uso conjunto de variables operativas y temporales aporta más información que usar solo variables temporales o solo núcleo operativo sin tiempo; retirar `branch_id` o `reason_group` produce variaciones menores frente a retirar grupos completos. | Set de variables usado en cada corrida: todas las features; sin `branch_id`; sin `reason_group`; solo temporales; operativas sin tiempo. | Cambio en desempeño por ablación. | Mismo modelo para las ablaciones controladas, mismo split temporal, mismo seed, misma métrica y mismo threshold del HPO para variantes GradientBoosting. | Delta F1 vs all features, delta average precision y número de features. Comparación principal: `F1_val_mean` y `delta_f1_vs_all_features`. | `ablation_summary_sprint8.csv`. GBC all features F1_val aprox. 0.5796; sin reason_group aprox. 0.5780; sin branch_id aprox. 0.5780; operativas sin tiempo aprox. 0.4943; solo temporales aprox. 0.4896. |
| OE3. Controlar el riesgo de sobreajuste y dejar el experimento trazable para defensa y reproducción. | H3. El pipeline con validación temporal, regularización, early stopping/pruning y registro MLOps mantiene un gap train-validación controlado y permite reproducir las corridas sin exponer datos sensibles. | Mecanismo de control experimental: `TimeSeriesSplit`, early stopping, pruning/`ccp_alpha`, threshold documentado y artefactos MLOps. | Gap de sobreajuste y trazabilidad del experimento. | Datos anonimizados, exclusión de TT/WO/coordenadas/link name/tracking incident, mismo repositorio y mismas carpetas de evidencia. | Gap = `F1_train_mean - F1_val_mean`; existencia de logs, manifest, modelo joblib, dashboard, `ablation_summary` y overfitting report. | `overfitting_gap_sprint8.csv`, `mlops_runs_sprint8.csv`, model card y README patch. GBC HPO gap aprox. 0.0394; RF baseline gap aprox. 0.1316. |

## Plan de generalización fuera de muestra / Plan B

| Escenario | Acción propuesta | Indicador / evidencia |
|---|---|---|
| Holdout temporal externo | Congelar el pipeline e hiperparámetros ganadores y reservar una ventana posterior de incidentes NOC como prueba fuera de muestra. No hacer fit global con datos externos. | Tabla CV temporal vs holdout externo con F1, precision, recall, average precision, Brier, curva PR y calibración. |
| Si no hay datos externos suficientes | Aplicar Plan B con backtesting temporal, Group/LOGO por branch operativo y pruebas de robustez con missingness/ruido controlado. | Tabla por ventana/grupo, delta de métrica, top variables con shift y breve explicación de degradación. |
| Shadow mode operativo | Ejecutar el modelo en sombra sobre logs o alarmas recientes sin afectar decisiones de operación. | Predicciones registradas, tasa de alertas, falsos positivos estimados y plan de ajuste de threshold/calibración. |
