# Patch Sprint 10 - Baseline vs actual, latencia y stakeholder

## Qué agrega
Este patch integra la evidencia faltante posterior a Sprint 8:

1. Entrega Sprint 9 de análisis de errores y slices.
2. Comparación leakage-safe entre baseline BAU congelado y modelo actual.
3. Auditoría explícita de `duration_hours_evidence` como target leakage.
4. Latencia p50/p95/p99, throughput, errores y optimizaciones.
5. Artefacto de inferencia, contrato de entradas y pruebas unitarias.
6. Protocolo A/B con stakeholder, escenarios, plantilla y agregador.
7. Notebook ejecutado, logs, tablas y figuras.
8. `README.md` de portada actualizado para la rama Sprint 10.

## Resultado principal del holdout cronológico

| Métrica | Baseline BAU | Actual |
|---|---:|---:|
| F1 | 0.492 | 0.503 |
| Precisión | 0.329 | 0.346 |
| Recall | 0.973 | 0.925 |
| Average Precision | 0.356 | 0.435 |
| Brier | 0.428 | 0.221 |
| FP | 1420 | 1254 |
| FN | 19 | 54 |
| Costo FP + 3*FN | 1477 | 1416 |

El modelo actual reduce FP en aproximadamente 11.7% y el costo ponderado en 4.1%, pero pierde alrededor de 4.9 puntos porcentuales de recall. No se presenta como victoria absoluta: la decisión recomendada es **shadow mode**.

## Latencia observada en el entorno de prueba
- Modelo caliente, batch 1: p50 ~7.9 ms y p95 ~9.9 ms.
- Throughput batch 1: ~124 req/s.
- Micro-batch 16: ~2,300 req/s.
- Errores internos observados: 0%.
- SLO de laboratorio: p95 <150 ms, error interno <0.5%, throughput >=100 req/s.

Los números exactos y el hardware están en:
- `results/latency_summary_sprint10.csv`
- `artifacts/reproducibility_manifest_sprint10.json`

## Advertencia metodológica
El artefacto Sprint 8 incluía `duration_hours_evidence`, variable que representa duración final y está vinculada a la construcción de `label_over_ola`. No está disponible al abrir el incidente; por ello se bloquea en Sprint 10. Las métricas históricas se conservan como antecedente, no como estimación válida para producción.

## Reproducción

```bash
python -m pip install -r requirements-sprint10.txt
python src/run_sprint10_validation_latency.py
python -m unittest discover -s tests -v
python src/run_stakeholder_scenarios_sprint10.py
```

## Prueba con stakeholder
No se inventaron respuestas. Completar:
- `templates/stakeholder_responses_template_sprint10.csv`

Y ejecutar:

```bash
python src/aggregate_stakeholder_feedback_sprint10.py \
  --input templates/stakeholder_responses_template_sprint10.csv
```

## Evidencia principal
- `docs/sprint10_baseline_actual_latency_report.md`
- `docs/Informe_Sprint10_Comparativo_Latencia_Fernando_Blaz_Aleman.docx` y `.pdf`
- `docs/stakeholder_validation_protocol_sprint10.md`
- `docs/Formulario_Stakeholder_Sprint10.docx` y `.pdf`
- `notebooks/05_baseline_actual_latency_sprint10.ipynb`
- `results/baseline_vs_actual_sprint10.csv`
- `results/latency_summary_sprint10.csv`
- `results/optimization_summary_sprint10.csv`
- `results/stakeholder_scenario_outputs_sprint10.csv`
- `logs/latency_samples_sprint10.csv`
- `logs/invalid_input_tests_sprint10.csv`
- `results/*.png`
- `artifacts/actual_logreg_sprint10.joblib`

## Decisión de despliegue
- Laboratorio: GO.
- Shadow mode: GO condicionado a logging y revisión de FN.
- Canary/producción: NO-GO hasta recolectar percepción real, acordar costo FN/FP y definir rollback.
