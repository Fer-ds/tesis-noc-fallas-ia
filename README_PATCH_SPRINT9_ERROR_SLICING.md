# Patch Sprint 9 - Error slicing y plan de mitigación

Este patch agrega el documento de avance del Sprint 9, enfocado en análisis de errores por slices para el proyecto de detección proactiva de incidentes NOC TX/IP con riesgo de superar OLA/SLA.

## Contenido

- `docs/sprint9_error_slicing_report.md`: reporte principal del análisis de slices.
- `results/problematic_slices_sprint9.csv`: tabla resumen de slices problemáticos.
- `results/slice_mitigation_plan_sprint9.csv`: causa probable, evidencia y mitigación por slice.
- `results/fig_problematic_slices_f1_ci_sprint9.png`: F1 por slice con intervalo de confianza.
- `results/fig_problematic_slices_fp_fn_sprint9.png`: falsos positivos y falsos negativos por slice.
- `results/fig_monthly_recall_shift_sprint9.png`: comportamiento temporal mensual.

## Relación con Sprint 8

Sprint 8 dejó implementado un pipeline con validación temporal, MLOps ligero, control de sobreajuste, ablaciones y reproducibilidad. Sprint 9 complementa ese avance identificando subpoblaciones donde el modelo presenta menor desempeño y proponiendo un plan de mitigación basado en evidencia.

## Ubicación recomendada

Subir el contenido a la raíz del repositorio, fusionando las carpetas con las ya existentes:

```text

docs/       -> docs/ del repo
results/    -> results/ del repo
```

No subir el archivo `.zip` como evidencia final. Subir las carpetas y archivos internos.
