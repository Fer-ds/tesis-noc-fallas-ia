# Privacidad y anonimización

Este repositorio usa datos operativos de telecomunicaciones. Por ello, los Excel originales no deben publicarse en GitHub.

## Campos que no se publican

- Tickets reales GNOC/WO.
- Códigos completos de rutas, enlaces o nodos.
- Coordenadas.
- Nombres de responsables, técnicos o usuarios.
- Descripciones largas de seguimiento operativo.
- Información sensible de clientes o proveedores.

## Estrategia aplicada

1. Se conservaron solo variables útiles para el análisis: severidad/prioridad, familia técnica, semana, mes, año, OLA/SLA y etiquetas derivadas.
2. Los activos, redes y branches se reemplazaron por IDs artificiales.
3. Las alarmas actuales se trataron como snapshot operativo anonimizado.
4. La variable objetivo se deriva del cumplimiento OLA/SLA sin exponer tickets reales.

## Regla para GitHub

Subir únicamente archivos de `data/processed/`, `docs/`, `results/`, `logs/`, `notebooks/` y `src/`. No subir los Excel originales en `data/raw/`.
