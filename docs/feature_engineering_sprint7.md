# Feature engineering Sprint 7

## Principio aplicado

Las variables creadas deben estar disponibles antes o al inicio de la atención del incidente.  
No se deben usar variables que se conocen recién al cierre del ticket, porque eso generaría leakage.

## Variables usadas

### 1. Variables temporales

- `year`
- `quarter`
- `month`
- `week_of_year`
- `day_of_week`
- `hour`
- `is_weekend`
- `is_night`

Estas variables ayudan a capturar patrones operativos por calendario, turnos o ventanas de mantenimiento.

### 2. Variables operativas

- `priority`
- `type_of_incident`
- `trouble_type`
- `incident_type`
- `network_id`
- `reason_group`
- `sla_threshold_hours`

Estas variables representan condiciones conocidas por el NOC durante la gestión inicial del incidente.

### 3. Variables por branch

- `branch_id`
- `branch_over_ola_rate_train`
- `branch_incident_count_train`

Estas variables permiten incorporar comportamiento histórico por branch.  
Para evitar leakage, se calculan solo con el conjunto de entrenamiento de cada fold.

### 4. Variables por causa

- `reason_over_ola_rate_train`

Representa la tasa histórica de Over OLA por grupo de causa, calculada solo con training.

## Variables excluidas por riesgo de leakage

No se usan como features de entrenamiento:

- duración final del incidente;
- fecha/hora de cierre;
- acción correctiva final;
- descripción de cierre;
- estado final del ticket;
- coordenadas o rutas sensibles;
- ticket real o identificadores internos.

## Evidencia de utilidad

El ablation study muestra que incorporar branch y variables históricas mejora el rendimiento del modelo:

```text
results/ablation_study_sprint7.csv
```

Lectura esperada:

- Sin branch: menor F1.
- Con branch: mejora el desempeño.
- Con branch + variables históricas calculadas solo en training: mejor equilibrio.
