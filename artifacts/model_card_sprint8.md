# Model Card - Sprint 8 Demo

**Proyecto:** Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC.  
**Modelo base:** GradientBoostingClassifier + OrdinalEncoder + SimpleImputer.  
**Target:** `label_over_ola` (Over OLA vs On Time).  
**Origen del ganador:** Sprint 7 HPO, Trial 8 con Random Search.  

## Data usada
- Incidentes históricos válidos para modelado: 10,819
- Positivos Over OLA: 3,505
- Negativos On Time: 7,314
- Tasa positiva: 32.40%
- Branches anonimizados: 44
- Rango fechas incidentes: 2022-08-14 a 2026-04-24

## Parámetros ganadores Sprint 7
```json
{
  "n_estimators": 60,
  "learning_rate": 0.0782682880932311,
  "max_depth": 2,
  "min_samples_leaf": 59,
  "subsample": 0.9232551608576888,
  "max_features": "log2",
  "ccp_alpha": 0.0001269862282811,
  "tol": 0.0001903680214831,
  "n_iter_no_change": 8,
  "validation_fraction": 0.15,
  "decision_threshold": 0.2303932323558283
}
```

## Uso en demo
Este artefacto se usa para demostrar trazabilidad, reproducibilidad y control de overfitting. No se suben datos crudos ni identificadores sensibles.
