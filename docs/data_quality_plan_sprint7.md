# Plan de calidad de datos Sprint 7

## Objetivo

Evitar que el modelo aprenda de datos erróneos, inconsistentes o mal etiquetados.

## Reglas aplicadas

1. Conservar solo registros de 2024 a 2026.
2. Conservar solo registros con KPI válido: `On Time` u `Over Time`.
3. Normalizar categorías en mayúsculas.
4. Eliminar de los datasets públicos campos sensibles.
5. Validar inconsistencias entre duración, umbral OLA y KPI.
6. Reportar nulos en campos críticos.
7. Separar datos procesados de datos crudos.

## Evidencia

El archivo principal de control es:

```text
results/data_quality_report_sprint7.csv
```

## Decisión sobre la etiqueta

Se usa `KPI` como etiqueta oficial, porque representa la clasificación operativa usada en el control del NOC.

```text
On Time    -> label_over_ola = 0
Over Time  -> label_over_ola = 1
```

Las inconsistencias contra duración y umbral se reportan, pero no se corrigen manualmente sin validación operativa.
