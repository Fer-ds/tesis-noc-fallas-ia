# Diccionario de datos Sprint 6

## Dataset de incidentes: `data/processed/incidents_noc_tx_ip_anon_sprint6.csv`

| Variable | Descripción |
|---|---|
| `incident_id` | Identificador artificial del incidente. No corresponde a ticket real. |
| `data_source` | Origen procesado del registro. |
| `area` | Área operativa normalizada. |
| `year` | Año del evento. |
| `quarter` | Trimestre numérico. |
| `month` | Mes numérico. |
| `week_of_year` | Semana operativa/ISO aproximada. |
| `priority` | Prioridad normalizada del incidente. |
| `type_of_incident` | Familia técnica general. |
| `trouble_type` | Tipo de problema reportado. |
| `incident_type` | Clasificación operativa general. |
| `network_id` | Red anonimizada. |
| `branch_id` | Branch/zona anonimizada. |
| `status` | Estado operativo normalizado. |
| `sla_threshold_hours` | Umbral OLA/SLA usado para evaluar cumplimiento. |
| `duration_hours` | Duración total del incidente en horas. No debe usarse como feature predictiva para evitar leakage. |
| `reason_group` | Causa agrupada de forma general. |
| `label_over_ola` | Variable objetivo: 1 si excede OLA/SLA, 0 si cumple. |

## Dataset de alarmas actuales: `data/processed/current_alarms_anon_sprint6.csv`

| Variable | Descripción |
|---|---|
| `alarm_record_id` | Identificador artificial de la alarma. |
| `data_source` | Fuente procesada. |
| `snapshot_time` | Fecha/hora del snapshot exportado. |
| `severity` | Severidad de la alarma. |
| `alarm_source_id` | Activo/equipo anonimizado con hash. |
| `alarm_source_type` | Prefijo técnico general del activo. |
| `alarm_name` | Nombre de alarma normalizado. |
| `first_occurred_at` | Primera ocurrencia. |
| `last_occurred_at` | Última ocurrencia. |
| `alarm_age_hours` | Antigüedad de la alarma al momento del snapshot. |
| `occurrence_times` | Cantidad de ocurrencias. |
| `down_reason` | Razón técnica extraída de forma general. |
| `port_oper_status` | Estado operativo del puerto, si aplica. |
| `port_admin_status` | Estado administrativo del puerto, si aplica. |
| `clearance_status` | Estado de limpieza/cierre. |
| `acknowledgment_status` | Estado de reconocimiento. |
| `maintenance_status` | Estado de mantenimiento. |
| `candidate_risk_score` | Puntaje preliminar explicable para priorizar revisión. |
| `reason_group_candidate` | Causa candidata agrupada. |

## Nota de privacidad
Los campos sensibles fueron eliminados o sustituidos por identificadores artificiales: tickets, rutas, enlaces, nombres de personas, coordenadas y textos operativos largos.
