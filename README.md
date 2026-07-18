# Seminario de Tesis 2 - Sprint 11
## Empaquetado y despliegue mínimo del prototipo NOC

El repositorio documenta un prototipo reproducible para priorizar incidentes NOC TX/IP con riesgo de incumplir el OLA. Sprint 11 añade una interfaz CLI/batch, contratos Pydantic/JSON, entorno fijado, Makefile, E2E, observabilidad, smoke/golden tests, seguridad, roadmap a Docker/API y rollback.

## Decisión segura

- **Clase positiva real:** incidente que efectivamente incumple el OLA.
- **Predicción positiva:** candidato de alerta.
- **Modo por defecto:** `shadow_ranking`; el modelo no suprime alertas BAU.
- **Fallback:** `BAU_rule_frozen_vS7`.

## Matriz de confusión

| Sistema | TN | FP | FN | TP | Recall |
|---|---:|---:|---:|---:|---:|
| Baseline BAU 0.50 | 25 | 1420 | 19 | 697 | 97.35% |
| Modelo 0.245 | 191 | 1254 | 54 | 662 | 92.46% |
| Candidato recall-first 0.20 | 68 | 1377 | 18 | 698 | 97.49% |

El umbral 0.245 no se propone como reemplazo autónomo. El 0.20 es un candidato posterior al feedback y debe confirmarse en una ventana temporal nueva. Mientras tanto, el valor del modelo es ordenar/priorizar en shadow mode.

## Ejecución

```bash
python -m pip install -r requirements-sprint11.lock.txt
make schemas
make test
make e2e
```

## Acceso rápido

- [Plan de despliegue en Markdown](docs/plan_despliegue_minimo_sprint11.md)
- [Plan de despliegue en Word](docs/Plan_Despliegue_Minimo_Sprint11_Fernando_Blaz_Aleman.docx)
- [Plan de despliegue en PDF](docs/Plan_Despliegue_Minimo_Sprint11_Fernando_Blaz_Aleman.pdf)
- [Contratos I/O](docs/contratos_io_sprint11.md)
- [E2E, observabilidad y seguridad](docs/e2e_observabilidad_seguridad_sprint11.md)
- [Runbook de rollback](docs/rollback_runbook_sprint11.md)
- [Arquitectura candidata](results/architecture_candidate_sprint11.png)
- [Esquema de entrada](contracts/predict_request_schema_sprint11.json)
- [E2E summary](results/e2e_summary_sprint11.json)
- [Matrices de confusión](results/comparativo_matrices_confusion_sprint10.csv)

## Resultados técnicos heredados de Sprint 10

Modelo precargado, batch 1: p50 7.92 ms, p95 9.92 ms, 123.8 req/s y 0 errores internos observados. Estas cifras corresponden a una prueba local secuencial; no equivalen a requests simultáneos. La concurrencia será validada en la etapa API mediante escalones 10→100 req/s.

## Estado de despliegue

- Laboratorio CLI: **GO**.
- Shadow ranking: **GO condicionado**.
- API/canary/producción: **NO-GO** hasta prueba concurrente, validación del stakeholder y contrato de recall/FN.
