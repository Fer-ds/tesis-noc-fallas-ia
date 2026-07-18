# Runbook de rollback - Sprint 11

## Cuándo volver atrás

- el modelo no carga o no coincide el SHA-256;
- error interno ≥0.5%;
- p95 ≥150 ms en el entorno objetivo;
- recall por debajo del contrato acordado;
- falso negativo crítico confirmado;
- exposición de dato sensible;
- feedback de usuario revela riesgo operativo no mitigado.

## Procedimiento

1. Cambiar `NOC_MODEL_ENABLED=false` o `NOC_DECISION_MODE=baseline_only`.
2. Detener cualquier acción automática; conservar solo logs y evidencia.
3. Restablecer la regla `BAU_rule_frozen_vS7` como fuente de decisión.
4. Ejecutar smoke test del fallback y confirmar continuidad del flujo.
5. Registrar versión, hash, hora, causa, casos afectados y responsable.
6. Abrir análisis de causa raíz; corregir y repetir unit, E2E, golden y carga.
7. Reactivar inicialmente en shadow mode; no saltar directamente a canary.
