Sprint 6 run log
Fecha de ejecución: 2026-05-23 01:02:21
Fuente 1: incidentes TX/IP histórico anonimizado
Fuente 2: snapshot de alarmas actuales anonimizado
Filas incidentes procesadas: 4215
Filas alarmas actuales procesadas: 4029
Split validación: temporal 80/20; seed fijo=42
Target: label_over_ola = duration_hours > sla_threshold_hours
Métrica central: Recall Over OLA, porque el costo de no detectar a tiempo un incidente riesgoso es mayor que revisar falsos positivos.
Variante adoptada sugerida: Var2, si su recall supera baseline/Var1 con costo de entrenamiento todavía viable para repositorio académico.
