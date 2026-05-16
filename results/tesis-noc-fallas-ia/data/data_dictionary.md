# Diccionario de datos

Dataset anonimizado para experimentos iniciales de Semana 5.

## Archivo

`data/processed/incidentes_noc_anon_semana5.csv`

## Variables

| Variable | Descripción |
|---|---|
| incident_id | Identificador artificial del incidente. No corresponde a ticket real. |
| year | Año derivado de la fecha de inicio. |
| quarter | Trimestre derivado de la fecha de inicio. |
| month | Mes derivado de la fecha de inicio. |
| week_of_year | Semana ISO derivada de la fecha de inicio. |
| area | Área operativa que registra el incidente, normalizada como categoría. |
| priority | Prioridad del incidente: CRITICAL, MAJOR o MINOR. |
| type_of_incident | Familia general del incidente, por ejemplo FIBRA o MICROWAVE. |
| trouble_type | Tipo de problema reportado. |
| incident_type | Clasificación operativa del incidente. |
| network_id | Red anonimizada. No contiene nombres internos originales. |
| branch_id | Branch o zona operativa anonimizada. |
| route_id | Ruta o enlace anonimizado. No contiene códigos reales. |
| duration_hours | Duración del incidente en horas. Se conserva para análisis descriptivo, no para entrenamiento predictivo de Over Time. |
| status | Estado operativo normalizado. |
| reason_group | Causa agrupada y generalizada. |
| kpi | Resultado KPI: On Time u Over Time. |
| label_over_time | Variable objetivo principal: 1 = Over Time, 0 = On Time. |
| label_critical | Variable objetivo secundaria: 1 = Critical, 0 = Major/Minor. |

## Nota de privacidad

El dataset publicado es una versión anonimizada/procesada. Se eliminaron o sustituyeron identificadores reales de tickets, códigos de rutas/enlaces, nombres de personas, coordenadas, campos de solución interna y referencias operativas sensibles. El archivo original Excel no debe subirse a GitHub.
