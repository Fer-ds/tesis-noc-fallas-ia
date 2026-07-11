# Sprint 10 - Comparativo baseline vs actual, latencia y validación con stakeholder

## 1. Objetivo y decisión
Evaluar si el sistema actual mejora el baseline operacional sin ocultar el costo en falsos negativos, y verificar si puede ejecutarse en modo *shadow* con un SLO de `p95 < 150 ms`, error interno `< 0.5%` y throughput caliente `>= 100 req/s`.

**Decisión recomendada:** **GO condicionado únicamente a shadow mode; NO-GO a producción con impacto real** hasta ejecutar la prueba de percepción con usuarios NOC y acordar el costo relativo FN/FP. La evidencia subjetiva no se inventa: utilidad, claridad y confianza permanecen pendientes.

## 2. Setup reproducible
- Dataset leakage-safe: `data/processed/incidents_noc_tx_ip_clean_sprint7.csv`.
- Orden cronológico: año, semana ISO, día y hora; timestamps iguales no se dividen entre particiones.
- Train/calibración/test: 7566/1079/2161 registros.
- Baseline: regla BAU congelada de Sprint 7, umbral 0.50.
- Actual: LogisticRegression one-hot, `C=1.0`, `class_weight=none`, umbral congelado `0.245`.
- Selección: costo `FP + 3*FN` con recall de calibración >= 0.85; entre configuraciones a <=2% del costo mínimo se elige menor Brier.
- Holdout abierto una sola vez después de congelar modelo y umbral.

## 3. Comparativo técnico en holdout

| Métrica | Baseline BAU | Actual | Delta |
|---|---:|---:|---:|
| F1 | 0.492 | 0.503 | +0.011 |
| Precisión | 0.329 | 0.346 | +0.016 |
| Recall | 0.973 | 0.925 | -0.049 |
| Average Precision | 0.356 | 0.435 | +0.079 |
| Brier (menor mejor) | 0.428 | 0.221 | -0.206 |
| FP | 1420 | 1254 | -166 |
| FN | 19 | 54 | +35 |
| Costo FP+3FN | 1477 | 1416 | -61 |
| Casos alertados | 98.0% | 88.7% | -9.3% |

El actual reduce los falsos positivos en **11.7%** y el costo ponderado en **4.1%**, pero pierde **4.9 puntos porcentuales de recall**. Por eso no se afirma una victoria absoluta: gana en carga operativa, AP, F1 y Brier; el baseline conserva mayor cobertura de positivos.

## 4. Auditoría de fuga
El artefacto Sprint 8 incluía `duration_hours_evidence`. La etiqueta `label_over_ola` se obtiene a partir de la duración final respecto del OLA/SLA; esa duración no existe cuando el NOC debe decidir. La métrica histórica con esa variable se conserva como antecedente, pero no es comparable ni apta para despliegue. Sprint 10 bloquea duración, tiempo de resolución, fecha final y `label_source` desde el contrato.

## 5. Latencia, throughput y errores
- Warm, batch 1: p50 **7.917 ms**, p95 **9.919 ms**, throughput **123.8 req/s**.
- Mayor throughput observado: batch 64, **8737.8 req/s**, p95 de lote **7.904 ms**.
- Error interno observado en pruebas válidas/robustez: **0.00%**.
- Optimizaciones probadas: carga fría por request, modelo precargado, micro-batches 8/16/32/64 y validación vectorizada.
- Recomendación: modelo precargado; batch 1 para interacción y micro-batch 8-16 para colas. No cargar el joblib por request.

## 6. Percepción del usuario
No existen respuestas reales de stakeholder en los archivos recibidos. Se entrega un protocolo guiado A/B, formulario y agregador. Campos obligatorios: utilidad, claridad, confianza (1-5), éxito de tarea, tiempo y comentario. Criterio mínimo propuesto para salir de shadow: `n >= 3` usuarios NOC, mediana >=4/5 en utilidad y claridad, >=80% de éxito y ningún riesgo crítico sin mitigación.

## 7. Robustez y límites
Todas las pruebas de contrato deben aparecer con `passed=True` en `logs/invalid_input_tests_sprint10.csv`. Las categorías desconocidas y campos extra son tolerados; tipos numéricos inválidos, rangos imposibles, campos faltantes y lotes vacíos se rechazan como errores de validación, no como 5xx.

## 8. Conclusión
El modelo actual es una mejora operativa moderada y mucho más defendible metodológicamente que el artefacto con fuga. Cumple el SLO de laboratorio y reduce carga, pero el trade-off de recall exige validación NOC. La decisión responsable es shadow mode con logging, revisión de FN y rollback a la regla BAU.

## Evidencia
- `results/baseline_vs_actual_sprint10.csv`
- `results/baseline_actual_comparison_sprint10.csv`
- `results/latency_summary_sprint10.csv`
- `results/optimization_summary_sprint10.csv`
- `logs/latency_samples_sprint10.csv`
- `logs/invalid_input_tests_sprint10.csv`
- `results/leakage_audit_sprint10.csv`
- `notebooks/05_baseline_actual_latency_sprint10.ipynb`
