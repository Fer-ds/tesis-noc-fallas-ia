# Patch Sprint 8 - MLOps ligero y demo 10-12 min

Este paquete agrega documentación y artefactos para defender el avance del Sprint 8:

- Demo 10-12 min con storytelling técnico.
- Preguntas probables del profesor y respuestas.
- Tablero de corridas MLOps ligero.
- Análisis de overfitting por gap train/validación.
- Ablaciones controladas.
- Manifest de reproducibilidad.

## Carpetas
- `config/`: configuración reproducible del demo.
- `docs/`: guion, Q&A y reporte.
- `logs/`: runs y métricas por fold.
- `results/`: tablas y figuras.
- `artifacts/`: modelo y manifest.
- `src/`: script reproducible.
- `notebooks/`: notebook resumen.

## Comando de reproducción
```bash
python src/run_sprint8_mlops_demo.py
```

## Nota de privacidad
No se suben Excel crudos ni identificadores sensibles. Se trabaja con datos procesados/anonimizados del Sprint 7.
