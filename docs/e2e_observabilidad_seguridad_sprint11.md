# E2E, observabilidad, pruebas y seguridad - Sprint 11

## E2E

```bash
make setup
make schemas
make test
make e2e
```

El E2E usa dos registros de ejemplo, ejecuta el CLI en un subproceso, valida la respuesta Pydantic, verifica hash de modelo, modo seguro y golden test. La evidencia se guarda en `results/e2e_summary_sprint11.json` y `logs/e2e_sprint11.log`.

## Observabilidad

Cada invocación genera un evento JSONL y una fila CSV. No se escriben datos crudos del incidente; solo metadatos operativos. Para una API futura se añadirá `/healthz`, métricas Prometheus y trazas de red.

## Pruebas

- smoke válido e inválido;
- categorías desconocidas;
- límites de rangos y lotes;
- ausencia de variables de fuga;
- golden prediction;
- reproducción de matrices de confusión.

## Seguridad

`.env.example` documenta configuración sin credenciales. Se limita payload y batch, se verifica hash del modelo y se conserva BAU como fallback. El artefacto no se descarga desde una URL arbitraria y los datos de demostración están anonimizados.


Antes de hacer commit, verificar que el `.gitignore` del repositorio contenga `.env` y `.env.*`, manteniendo únicamente `!.env.example` como plantilla versionada.
