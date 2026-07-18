# Contratos I/O Sprint 11

## Semántica obligatoria

- `y_true = 1`: el incidente realmente incumple/supera el OLA.
- `predicted_positive = true`: el prototipo marca un candidato de alerta.
- Una alerta no constituye por sí sola la verdad real.

## Entrada

El esquema fuente es `contracts/predict_request_schema_sprint11.json`. Solo incluye información disponible en apertura. El lote admite de 1 a 64 registros. Las categorías nuevas se aceptan; nulos categóricos se normalizan como `MISSING`. Campos numéricos fuera de rango se rechazan.

## Salida

El esquema fuente es `contracts/predict_response_schema_sprint11.json`. Devuelve score, candidato de alerta, banda de ranking, umbral, latencia, versión y hash del modelo. `shadow_ranking` es el valor seguro predeterminado.

## Errores

`contracts/error_response_schema_sprint11.json` define `code`, `message`, `hint` y detalles por campo. Errores de entrada son equivalentes a 4xx; errores inesperados son internos y deben contabilizarse por separado.
