# Protocolo de validación con stakeholder - Sprint 10

## Propósito
Comparar la regla BAU (variante A) y el modelo actual leakage-safe (variante B) en utilidad, claridad, confianza, éxito y tiempo de tarea. La prueba no autoriza decisiones automáticas: se ejecuta en laboratorio o shadow mode.

## Participantes y mínimo defendible
- Perfil: analista, supervisor o responsable NOC TX/IP.
- Mínimo exploratorio: 3 participantes. Deseable: 5-8.
- Registrar rol y años de experiencia; no registrar nombres, correos ni tickets reales.
- No usar este instrumento para evaluar desempeño laboral de una persona.

## Diseño
A/B controlado y contrabalanceado. Para la mitad de participantes presentar A-B; para la otra mitad B-A. El facilitador no debe decir qué variante es “nueva”. Se usan los tres casos de `templates/stakeholder_scenarios_sprint10.csv`.

## Guion (20-25 minutos)
1. **Contexto, 2 min.** “Buscamos priorizar revisión de incidentes con riesgo de exceder OLA, sin reemplazar el criterio del analista”.
2. **Entrenamiento, 2 min.** Explicar campos, sin revelar hipótesis.
3. **Tareas, 10-12 min.** Para cada escenario y variante: decidir si priorizar, explicar por qué y señalar qué información falta. Aplicar think-aloud.
4. **Feedback, 5-7 min.** Puntuar utilidad, claridad y confianza de 1 a 5; indicar si usaría la recomendación y en qué casos nunca la usaría.
5. **Cierre, 2 min.** Confirmar el principal riesgo y el criterio de aceptación.

## Definiciones de medición
- `task_success`: 1 si el participante completa la decisión y puede justificarla; 0 si abandona o no entiende la salida.
- `task_time_seconds`: desde la presentación del caso hasta la decisión verbal.
- `utility_1_5`: cuánto ayuda a decidir.
- `clarity_1_5`: cuánto se entiende la salida y su siguiente acción.
- `confidence_1_5`: confianza para usarla como apoyo, no como decisión autónoma.
- `critical_risk`: 1 cuando el comentario identifica daño potencial sin mitigación.

## Criterios propuestos
Se recomienda continuar a canary únicamente si:
- mediana de utilidad y claridad de B >= 4/5;
- éxito de tarea de B >= 80%;
- B no aumenta el tiempo mediano más de 15% frente a A;
- no existe riesgo crítico abierto;
- el trade-off técnico FN/FP fue aceptado por el responsable NOC.

## Registro
Usar una fila por participante, escenario y variante en `templates/stakeholder_responses_template_sprint10.csv`. Después ejecutar:

```bash
python src/aggregate_stakeholder_feedback_sprint10.py \
  --input templates/stakeholder_responses_template_sprint10.csv
```

El script rechaza escalas fuera de rango, variantes distintas de A/B y tiempos negativos. Sin respuestas reales, reporta “pendiente” y no fabrica promedios.

## Preguntas de cierre
1. ¿Qué parte de la recomendación le resultó más útil?
2. ¿Qué término o dato fue ambiguo?
3. ¿En qué caso nunca usaría esta recomendación?
4. ¿Prefiere mayor recall aunque aumenten alertas, o menos alertas aunque se pierdan casos? ¿Por qué?
5. ¿Qué evidencia necesitaría para autorizar shadow/canary?

## Riesgos y mitigación
- Sesgo por orden: contrabalancear A-B/B-A.
- Sesgo del facilitador: guion fijo y preguntas neutrales.
- Muestra pequeña: reportar medianas y cada respuesta, no generalizar a toda la organización.
- Datos sensibles: usar escenarios anonimizados; no grabar identificadores reales.
- Confusión “score = probabilidad”: presentar “puntaje de riesgo”, pues el score aún no se declara probabilidad calibrada.
