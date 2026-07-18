# Patch — matriz de confusión y aclaración de recall

Copia el contenido de este ZIP sobre la raíz de la rama de Sprint 10.

## Qué incorpora

- Matriz de confusión del baseline BAU.
- Matriz del modelo actual con umbral 0.245.
- Matriz exploratoria con umbral 0.200.
- CSV comparativo con TP, FP, FN, TN, recall, FNR, precisión, F1 y tasa de alertas.
- Nota metodológica sobre la clase positiva y el significado de una alerta.
- Script reproducible para regenerar las figuras.

## Comando reproducible

```bash
python src/generate_confusion_matrices_sprint10.py
```

## Interpretación principal

`y_true = 1` significa incumplimiento real del OLA.
`y_pred = 1` significa alerta emitida.

Con umbral 0.245, el modelo reduce falsas alarmas, pero aumenta los falsos
negativos; por ello no se recomienda como reemplazo autónomo del baseline.
El umbral 0.200 es un candidato posterior al feedback y debe revalidarse con
un periodo temporal nuevo o en shadow mode.
