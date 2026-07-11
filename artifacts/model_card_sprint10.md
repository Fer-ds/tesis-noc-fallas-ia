# Model card - sprint10-logreg-leakage-safe-v1

- Propósito: priorizar incidentes con riesgo de exceder OLA para revisión NOC.
- Algoritmo: LogisticRegression con one-hot e imputación train-only.
- Umbral: 0.245, elegido solo en calibración.
- Dataset hash SHA-256: `3323649cd76c89d1c20ee65ac9e04400eaae8b9dd11a99efb5105669bd527024`.
- Features permitidas: domain, area, priority, type_of_incident, trouble_type, incident_type, network_id, reason_group, branch_id, year, quarter, month, week_of_year, day_of_week, hour, is_weekend, is_night, sla_threshold_hours.
- Features bloqueadas: date_end, duration_hours, duration_hours_evidence, end_time, label_source, resolution_time, time_to_resolution.
- Holdout: F1=0.503, precision=0.346, recall=0.925, AP=0.435.
- Uso autorizado: laboratorio y shadow mode.
- Uso no autorizado: decisión autónoma, cierre automático o penalización de personal/proveedor.
- Limitaciones: drift temporal, alto volumen de alertas, costo FN/FP pendiente de acuerdo y percepción de usuario aún no recolectada.
- Fallback: regla BAU congelada de Sprint 7.
