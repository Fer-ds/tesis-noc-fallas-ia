# Manifiesto Sprint 10

## Código
- `src/run_sprint10_validation_latency.py`: entrenamiento, evaluación, bootstrap, auditoría, benchmark, figuras y manifiesto.
- `src/inference_contract_sprint10.py`: validación de entradas y servicio caliente/frío.
- `src/run_stakeholder_scenarios_sprint10.py`: genera salidas A/B para el facilitador.
- `src/aggregate_stakeholder_feedback_sprint10.py`: valida y resume respuestas reales.
- `tests/test_inference_contract_sprint10.py`: 8 pruebas unitarias.

## Datos reproducibles
- `data/processed/incidents_noc_tx_ip_clean_sprint7.csv`.
- `data/processed/incidents_noc_tx_ip_hpo_sprint7.csv` solo para auditoría de la variable de duración.

## Artefactos y logs
- Artefacto joblib, model card y manifiesto de hardware/versiones.
- Predicciones del holdout, muestras de latencia, pruebas inválidas y eventos JSONL.

## Resultados
- Comparación baseline/actual con IC95 bootstrap.
- Curva de sensibilidad de umbral.
- Latencia p50/p95/p99 y throughput.
- Optimizaciones y auditoría de fuga.
- Estado explícito de percepción: pendiente.

## Figuras
- Baseline vs actual.
- Curva Precision-Recall.
- Trade-off de umbral.
- Latencia p50/p95.
- Throughput por batch.
- Evidencia de duración vs etiqueta.

## Sprint 9
También se incorporan en raíz los documentos y figuras del análisis de errores entregado en el RAR `03-07-02`.
