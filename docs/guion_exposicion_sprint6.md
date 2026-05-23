# Guion de exposición - Sprint 6

## 1. Apertura

Profesor, para el Sprint 6 mejoré el repositorio de tesis y agregué una segunda fuente de datos: alarmas actuales de red. El objetivo sigue siendo aplicar modelos de inteligencia artificial para priorizar incidentes NOC con riesgo de superar el tiempo operativo esperado, que en este proyecto estoy llamando Over OLA.

## 2. Qué se mejoró en el repositorio

El repositorio ahora tiene una estructura más clara: documentación, datos procesados, notebooks, scripts, logs y resultados. También se agregó un notebook EDA para visualizar los datos y un reporte Sprint 6 que resume contexto, baseline, experimentos A/B, resultados, validación, decisión técnica y próximos pasos.

## 3. Dataset

Se trabajó con dos fuentes. La primera corresponde a incidentes históricos TX/IP del NOC. La segunda corresponde a alarmas actuales de red. Por confidencialidad no se suben archivos crudos, sino versiones procesadas y anonimizadas, eliminando tickets reales, enlaces, nombres, coordenadas e identificadores internos.

## 4. Análisis exploratorio

En el notebook EDA se muestran distribuciones de incidentes, casos On Time vs Over OLA, causas agrupadas, duración de incidentes, severidad de alarmas y score candidato de riesgo. Esto permite evidenciar que ya no solo estoy subiendo archivos, sino analizando el comportamiento operativo de los datos.

## 5. Modelos y comparación

Comparé un baseline con dos variantes: Logistic Regression y Random Forest. El baseline sirve como punto de comparación inicial. Logistic Regression mejora la precisión, pero Random Forest logra el mejor equilibrio general entre recall, precisión y F1 para detectar casos Over OLA.

## 6. Curva Precision-Recall

La curva Precision-Recall muestra cómo cambia el modelo según el umbral de decisión. Si busco detectar más casos, aumenta el recall, pero puede bajar la precisión porque se generan más falsos positivos. En un NOC, este equilibrio es importante porque no quiero perder incidentes críticos, pero tampoco saturar al operador con alertas innecesarias.

## 7. Decisión técnica

La variante adoptada en este sprint es Random Forest. No reemplaza al operador NOC; funciona como una herramienta de priorización para enfocar la atención en incidentes y alarmas con mayor riesgo operativo.

## 8. Próximos pasos

Para el siguiente sprint se debe mejorar el tratamiento temporal, validar mejor el modelo con splits temporales, analizar posibles sesgos por tipo de incidente o dominio tecnológico, revisar drift operativo y agregar explicabilidad de variables importantes.
