# Seminario de Tesis 2 — Sprint 10
## Comparativo baseline vs modelo actual, latencia y validación con stakeholder

Esta rama reúne la evidencia técnica y operativa del Sprint 10 del proyecto de tesis para la detección proactiva de incidentes NOC TX/IP con riesgo de superar el OLA.

La entrega incorpora:

- Comparación reproducible entre el baseline BAU congelado y el modelo actual.
- Métricas técnicas con intervalo de confianza bootstrap.
- Latencia p50, p95 y p99, throughput y ratio de errores.
- Pruebas de precarga, warmup y micro-batching.
- Pruebas de entradas inválidas, casos límite y contrato de inferencia.
- Notebook ejecutado, scripts, logs, tablas y figuras.
- Protocolo A/B y formulario para validación con stakeholder.
- Auditoría de fuga de información asociada a `duration_hours_evidence`.
- Evidencia del análisis de errores y slices realizado en Sprint 9.

## Acceso rápido a la entrega actual

- [Informe técnico en PDF](docs/Informe_Sprint10_Comparativo_Latencia_Fernando_Blaz_Aleman.pdf)
- [Informe técnico en Word](docs/Informe_Sprint10_Comparativo_Latencia_Fernando_Blaz_Aleman.docx)
- [Reporte técnico en Markdown](docs/sprint10_baseline_actual_latency_report.md)
- [Notebook ejecutado](notebooks/05_baseline_actual_latency_sprint10.ipynb)
- [Comparativo baseline vs actual](results/baseline_vs_actual_sprint10.csv)
- [Resumen de latencia](results/latency_summary_sprint10.csv)
- [Resumen de optimizaciones](results/optimization_summary_sprint10.csv)
- [Protocolo de validación con stakeholder](docs/stakeholder_validation_protocol_sprint10.md)
- [Formulario de stakeholder en PDF](docs/Formulario_Stakeholder_Sprint10.pdf)
- [Manifiesto completo de la entrega](MANIFEST_SPRINT10_VALIDACION_LATENCIA.md)

## Resultados principales

| Indicador | Baseline BAU | Modelo actual |
|---|---:|---:|
| F1 | 0.492 | 0.503 |
| Precisión | 0.329 | 0.346 |
| Recall | 0.973 | 0.925 |
| Average Precision | 0.356 | 0.435 |
| Brier, menor es mejor | 0.428 | 0.221 |
| Falsos positivos | 1,420 | 1,254 |
| Falsos negativos | 19 | 54 |
| Costo `FP + 3·FN` | 1,477 | 1,416 |

El modelo actual reduce falsos positivos y mejora la calidad del ranking y la calibración, aunque disminuye el recall. Por ello, la recomendación es avanzar a **shadow mode**, sin impacto todavía en decisiones reales, y revisar especialmente los falsos negativos.

## Latencia y capacidad observadas

| Modalidad | p50 | p95 | Throughput |
|---|---:|---:|---:|
| Modelo precargado, batch 1 | 7.92 ms | 9.92 ms | 123.8 req/s |
| Micro-batch 8 | 7.14 ms por lote | 7.76 ms por lote | 1,115 req/s |
| Micro-batch 16 | 6.85 ms por lote | 7.35 ms por lote | 2,302 req/s |

Durante el benchmark se observaron 0 errores internos. Los resultados completos, el entorno y las versiones están documentados en `results/`, `logs/` y `artifacts/reproducibility_manifest_sprint10.json`.

## Reproducción

```bash
python -m pip install -r requirements-sprint10.txt
python src/run_sprint10_validation_latency.py
python -m unittest discover -s tests -v
python src/run_stakeholder_scenarios_sprint10.py
```

Para consolidar respuestas reales del stakeholder:

```bash
python src/aggregate_stakeholder_feedback_sprint10.py \
  --input templates/stakeholder_responses_template_sprint10.csv
```

No se fabricaron resultados de percepción. La utilidad, claridad y confianza permanecen pendientes hasta ejecutar la prueba con usuarios o stakeholders.

## Decisión de despliegue

- **Laboratorio:** GO.
- **Shadow mode:** GO condicionado a logging y revisión de falsos negativos.
- **Canary o producción:** NO-GO hasta recolectar percepción real, acordar el costo relativo de FP/FN y definir rollback.

## Antecedente: entrega hasta Sprint 8

- [Entregable completo en PDF](Entregable_Seminario_Tesis2_Blaz_Aleman_FINAL_con_matriz_consistencia.pdf)
- [Matriz de consistencia en PDF](Matriz_consistencia_Seminario_Tesis2_IA_Sprint8.pdf)
- [Resumen del entregable en Markdown](ENTREGABLE_RESUMEN_PREVIEW.md)
- [Matriz de consistencia en Markdown](MATRIZ_CONSISTENCIA_PREVIEW.md)
