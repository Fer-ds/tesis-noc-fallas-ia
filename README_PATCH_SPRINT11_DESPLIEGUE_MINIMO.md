# Sprint 11 - Empaquetado y despliegue mínimo

Este patch convierte el avance de Sprint 10 en un prototipo CLI reproducible y seguro para laboratorio. Incluye el plan de despliegue en Markdown, Word y PDF, arquitectura, contratos Pydantic/JSON, lockfile, Makefile, prueba E2E, observabilidad, smoke/golden tests, configuración y rollback.

## Integración

Descomprima el ZIP y copie su contenido sobre la raíz de la rama actual. Las carpetas se fusionan; `README.md` se actualiza.

```bash
python -m pip install -r requirements-sprint11.lock.txt
python src/generate_contract_schemas_sprint11.py
python -m unittest discover -s tests -p "test_*sprint11.py" -v
python src/run_e2e_sprint11.py
```

## Decisión operativa

- Positivo real: incidente que incumple el OLA.
- Alerta: predicción positiva.
- Umbral 0.245: no-go como reemplazo autónomo por caída de recall.
- Umbral 0.20: candidato recall-first, sujeto a revalidación temporal.
- Modo predeterminado: `shadow_ranking` con rollback a BAU.
