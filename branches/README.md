# Análisis por Branch - Sprint 7

Esta carpeta organiza la lectura operativa por branch, según la observación del profesor. No reemplaza el análisis global; lo complementa para detectar diferencias entre sedes/branches.

## Archivos

- `branch_summary_sprint7.csv`: resumen de incidentes por branch.
- `branch_*.md`: fichas de los branches con mayor volumen.

## Top 10 branches por volumen

| branch     | branch_id   |   n_incidents |   over_ola |   over_ola_rate | top_reason   |
|:-----------|:------------|--------------:|-----------:|----------------:|:-------------|
| PIU        | branch_035  |           897 |        259 |          0.2887 | fiber_cable  |
| SAN        | branch_038  |           844 |        326 |          0.3863 | fiber_cable  |
| LIMA 1     | branch_026  |           748 |        295 |          0.3944 | fiber_cable  |
| TELEFONICA | branch_041  |           690 |        202 |          0.2928 | fiber_cable  |
| LIMA 4     | branch_029  |           589 |        219 |          0.3718 | fiber_cable  |
| HUN        | branch_019  |           552 |        200 |          0.3623 | fiber_cable  |
| LIMA 8     | branch_032  |           374 |        138 |          0.369  | fiber_cable  |
| CAJ        | branch_011  |           365 |         98 |          0.2685 | fiber_cable  |
| ARE        | branch_004  |           354 |        130 |          0.3672 | fiber_cable  |
| LIMA 2     | branch_027  |           350 |        144 |          0.4114 | fiber_cable  |

## Criterio de uso

Los branches con mayor volumen y mayor tasa Over OLA deben revisarse primero para validar si existen patrones operativos recurrentes, problemas de registro o necesidades de features específicas por sede.
