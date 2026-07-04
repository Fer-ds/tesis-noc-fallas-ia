# Patch Sprint 9 - Error slicing y mitigación

Este paquete agrega el avance solicitado en la clase de análisis de errores:

- Descubrimiento de 2-5 slices problemáticos.
- Métrica por slice con IC 95% y tamaño `n`.
- Causa probable con evidencia.
- Plan de mitigación.

## Archivos principales

- `docs/sprint9_error_slicing_report.md`: reporte académico del análisis.
- `docs/demo_storytelling_sprint9_error_slicing.md`: guion corto para explicar en clase.
- `docs/preguntas_profesor_sprint9_error_slicing_qna.md`: preguntas y respuestas probables.
- `results/slice_metrics_problematic_sprint9.csv`: tabla principal de slices problemáticos.
- `results/slice_root_cause_mitigation_sprint9.csv`: causa probable y mitigación por slice.
- `results/slice_metrics_all_candidates_sprint9.csv`: todos los slices candidatos evaluados.
- `results/fig_problematic_slices_f1_ci_sprint9.png`: F1 con IC 95%.
- `results/fig_problematic_slices_fp_fn_sprint9.png`: perfil FP/FN.
- `results/fig_monthly_recall_shift_sprint9.png`: evidencia temporal del slice mes 6.
- `src/run_sprint9_error_slicing.py`: script reproducible del análisis.

## Nota de privacidad

No se incluye data cruda ni predicciones fila a fila. Los archivos compartidos son agregados por slice.
