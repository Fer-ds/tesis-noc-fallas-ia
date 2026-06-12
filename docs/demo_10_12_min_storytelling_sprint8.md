# Demo 10-12 min - Sprint 8: storytelling técnico

## 0. Apertura (20-30 segundos)
Buenos días. En esta demo voy a presentar el avance de mi trabajo de investigación: **Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC**. El objetivo es anticipar incidentes que podrían terminar como **Over OLA**, usando datos históricos de incidentes NOC TX/IP y una línea de trabajo reproducible en GitHub.

---

## 1. Problema y métrica (1 min)
El problema operativo es que en redes de telecomunicaciones no basta con reaccionar cuando el incidente ya venció el OLA. La meta es detectar patrones de riesgo antes de que el evento escale.

La variable objetivo es `label_over_ola`, que clasifica el incidente como **Over OLA** o **On Time**. Para evaluar el modelo uso principalmente **F1**, porque necesito balancear precision y recall. En este contexto no conviene usar solo accuracy, porque podría ocultar fallas en la clase crítica.

Data usada:
- 10,819 incidentes válidos para modelado.
- 3,505 casos Over OLA.
- 7,314 casos On Time.
- 44 branches operativos anonimizados.
- Rango temporal: 2022-08-14 a 2026-04-24.

---

## 2. Protocolo experimental (2 min)
Para que la comparación sea justa, mantuve el mismo seed, la misma métrica y el mismo esquema de validación. Usé **TimeSeriesSplit con 3 folds**, porque los incidentes tienen orden temporal. No debo entrenar con información futura para validar eventos pasados.

En Sprint 7 se compararon dos métodos de búsqueda de hiperparámetros: **Random Search** y **búsqueda Bayesiana**. Ambos buscaron hiperparámetros del mismo modelo: `GradientBoostingClassifier`.

El presupuesto fue:
- 12 trials Random Search.
- 12 trials Bayesianos.
- 24 trials en total.
- Early stopping con `n_iter_no_change` y `tol`.
- Pruning mediante `ccp_alpha` y regla de corte para trials de bajo rendimiento.

Es importante aclarar: Random y Bayes no son modelos. Son estrategias para buscar la mejor configuración del modelo.

---

## 3. Resultados principales (3-4 min)
El modelo ganador fue:

- **Modelo:** GradientBoostingClassifier.
- **Método ganador:** Random Search.
- **Trial ganador:** 8.
- **F1 promedio:** 0.4986.
- **Precision:** 0.3333.
- **Recall:** 1.0000.
- **Average Precision:** 0.4395.

Los hiperparámetros ganadores fueron:
- `n_estimators=60`: cantidad de árboles.
- `learning_rate=0.0783`: velocidad de aprendizaje.
- `max_depth=2`: complejidad máxima del árbol.
- `min_samples_leaf=59`: regularización por tamaño mínimo de hoja.
- `subsample=0.9233`: porcentaje de datos usados por iteración.
- `max_features=log2`: selección de variables por división.
- `ccp_alpha=0.000127`: poda del árbol.
- `n_iter_no_change=8` y `tol=0.000190`: early stopping.
- `decision_threshold=0.2304`: umbral final para clasificar Over OLA.

Para demostrarlo abro tres evidencias:
1. `artifacts/best_config_sprint7_hpo.json`: configuración ganadora.
2. `results/hpo_topk_sprint7.csv`: ranking top-k de configuraciones.
3. `logs/hpo_runs_sprint7.csv`: historial de trials.

En Sprint 8 agregué una capa de MLOps ligero: tablero de corridas, análisis de overfitting y ablaciones.

---

## 4. Ablaciones: qué cambio movió la aguja (2 min)
Una ablación significa cambiar solo una parte del pipeline y mantener todo lo demás igual. En mi caso, comparé el modelo completo contra variantes donde retiro grupos de variables.

Los experimentos controlados están en `results/ablation_summary_sprint8.csv`. La idea es responder qué variables aportan o perjudican bajo el mismo split, seed, modelo y métrica.

Lo explico así:
- Con todas las variables tengo la referencia principal.
- Sin `branch_id`, evalúo si la segmentación operativa aporta información.
- Sin `reason_group`, evalúo el peso de la causa/reason group.
- Con variables temporales solamente, mido si el patrón horario o calendario basta.
- Con variables operativas sin tiempo, mido el aporte de la información de operación.

Esto permite interpretar el modelo de forma más defendible, no solo como caja negra.

---

## 5. Riesgos y plan (1-2 min)
Riesgos identificados:
1. **Precision moderada/baja:** el modelo detecta muchos Over OLA, pero puede generar falsos positivos.
2. **Desbalance de clases:** la clase Over OLA representa aprox. 32.4%.
3. **Riesgo de leakage temporal:** se mitiga usando TimeSeriesSplit.
4. **Variabilidad por branch:** algunos branches pueden comportarse diferente.
5. **Data sensible:** no se suben tickets, coordenadas ni identificadores crudos.

Plan:
- Ajustar threshold según costo operativo de falso positivo vs falso negativo.
- Mejorar calibración del modelo.
- Agregar más señales de alarmas actuales.
- Evaluar métricas por branch operativo.
- Incorporar tracking tipo MLflow si el proyecto pasa a una fase más productiva.

---

## 6. Reproducibilidad (1 min)
Para reproducibilidad, el repositorio guarda configuración, código, logs, resultados y artefactos.

Estructura clave:
- `config/`: presupuesto y configuración.
- `notebooks/`: análisis y demo.
- `src/`: scripts reproducibles.
- `logs/`: corridas y folds.
- `results/`: tablas y figuras.
- `artifacts/`: modelo y configuración ganadora.
- `docs/`: reporte y guion.

Comando de referencia:
```bash
python src/run_sprint8_mlops_demo.py
```

Cierre:
El aporte de este sprint es que el proyecto ya no presenta solo un resultado aislado. Presenta un flujo trazable: problema, métrica, protocolo, resultados, ablaciones, riesgos y reproducibilidad.
