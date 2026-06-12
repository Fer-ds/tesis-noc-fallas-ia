import json, os, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, balanced_accuracy_score, average_precision_score, brier_score_loss, precision_recall_curve
from sklearn.model_selection import TimeSeriesSplit, learning_curve
from sklearn.calibration import calibration_curve
import joblib
warnings.filterwarnings('ignore')

BASE = Path('/mnt/data/semana05_06_extracted/SEMANA 05-06/sprint7_hpo_entregable')
OUT = Path('/mnt/data/sprint8_mlops_demo_update')
for sub in ['config','docs','logs','results','artifacts','src','notebooks']:
    (OUT/sub).mkdir(parents=True, exist_ok=True)

inc = pd.read_csv(BASE/'data/processed/incidents_noc_tx_ip_hpo_sprint7.csv')
inc['date_start'] = pd.to_datetime(inc['date_start'], errors='coerce')
inc = inc.sort_values('date_start').reset_index(drop=True)
y = inc['label_over_ola'].astype(int)
all_features = [c for c in inc.columns if c not in ['label_over_ola','date_start']]
cat_cols_all = inc[all_features].select_dtypes(include=['object']).columns.tolist()
num_cols_all = [c for c in all_features if c not in cat_cols_all]

best_params = json.loads((BASE/'artifacts/best_config_sprint7_hpo.json').read_text())['params']
threshold = best_params.pop('decision_threshold')
# keep copy after pop
best_params_model = dict(best_params)

# sklearn 1.8 compatible with encoded_missing_value

def make_pipe(features, model_params=None, model_type='gb'):
    Xtmp = inc[features]
    cats = Xtmp.select_dtypes(include=['object']).columns.tolist()
    nums = [c for c in features if c not in cats]
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='MISSING')),
        ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
    ])
    num_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median'))
    ])
    pre = ColumnTransformer([
        ('cat', cat_pipe, cats),
        ('num', num_pipe, nums)
    ], remainder='drop')
    if model_type == 'gb':
        params = dict(random_state=42)
        if model_params:
            params.update(model_params)
        clf = GradientBoostingClassifier(**params)
    elif model_type == 'rf':
        clf = RandomForestClassifier(n_estimators=120, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=-1, class_weight='balanced_subsample')
    return Pipeline([('preprocess', pre), ('model', clf)])

best_params_sklearn = {
    'n_estimators': int(best_params_model['n_estimators']),
    'learning_rate': float(best_params_model['learning_rate']),
    'max_depth': int(best_params_model['max_depth']),
    'min_samples_leaf': int(best_params_model['min_samples_leaf']),
    'subsample': float(best_params_model['subsample']),
    'max_features': best_params_model['max_features'],
    'ccp_alpha': float(best_params_model['ccp_alpha']),
    'tol': float(best_params_model['tol']),
    'n_iter_no_change': int(best_params_model['n_iter_no_change']),
    'validation_fraction': 0.15,
}

# feature sets
feature_sets = {
    'S8_01_hpo_best_all_features': all_features,
    'S8_02_ablation_no_branch_id': [c for c in all_features if c != 'branch_id'],
    'S8_03_ablation_no_reason_group': [c for c in all_features if c != 'reason_group'],
    'S8_04_temporal_only': ['year','quarter','month','week_of_year','day_of_week','hour','is_weekend','is_night'],
    'S8_05_operational_core_no_time': ['area_noc','priority','type_of_incident','trouble_type','incident_type','network_type','branch_id','reason_group'],
}

# add a baseline model RandomForest on all features for dashboard, but not central
experiments = []
fold_records = []
tscv = TimeSeriesSplit(n_splits=3)

for exp_id, feats in feature_sets.items():
    t0 = time.time()
    train_mets=[]; val_mets=[]
    for fold, (tr, va) in enumerate(tscv.split(inc), start=1):
        pipe = make_pipe(feats, best_params_sklearn, 'gb')
        Xtr, Xva = inc.loc[tr, feats], inc.loc[va, feats]
        ytr, yva = y.iloc[tr], y.iloc[va]
        pipe.fit(Xtr, ytr)
        for split_name, Xs, ys in [('train', Xtr, ytr), ('val', Xva, yva)]:
            prob = pipe.predict_proba(Xs)[:,1]
            pred = (prob >= threshold).astype(int)
            metrics = {
                'f1': f1_score(ys, pred, zero_division=0),
                'precision': precision_score(ys, pred, zero_division=0),
                'recall': recall_score(ys, pred, zero_division=0),
                'balanced_accuracy': balanced_accuracy_score(ys, pred),
                'average_precision': average_precision_score(ys, prob),
                'brier': brier_score_loss(ys, prob),
                'positive_rate_pred': float(pred.mean()),
                'positive_rate_true': float(ys.mean()),
            }
            fold_records.append({'exp_id':exp_id,'fold':fold,'split':split_name,'n_rows':len(ys),**metrics})
            if split_name=='train': train_mets.append(metrics)
            else: val_mets.append(metrics)
    elapsed = time.time()-t0
    val_f1 = [m['f1'] for m in val_mets]
    train_f1 = [m['f1'] for m in train_mets]
    val_ap = [m['average_precision'] for m in val_mets]
    experiments.append({
        'exp_id': exp_id,
        'model': 'GradientBoostingClassifier',
        'features': '+'.join(feats),
        'n_features_input': len(feats),
        'threshold': threshold,
        'f1_train_mean': float(np.mean(train_f1)),
        'f1_val_mean': float(np.mean(val_f1)),
        'f1_val_std': float(np.std(val_f1, ddof=1)),
        'gap_train_val_f1': float(np.mean(train_f1)-np.mean(val_f1)),
        'average_precision_val_mean': float(np.mean(val_ap)),
        'recall_val_mean': float(np.mean([m['recall'] for m in val_mets])),
        'precision_val_mean': float(np.mean([m['precision'] for m in val_mets])),
        'balanced_accuracy_val_mean': float(np.mean([m['balanced_accuracy'] for m in val_mets])),
        'brier_val_mean': float(np.mean([m['brier'] for m in val_mets])),
        'seconds': round(elapsed,3),
        'notes': 'Ablación controlada: mismo split, seed, métrica y modelo; cambia solo set de features.'
    })

# baseline RandomForest all features
# Keep quick with 3 folds
t0=time.time(); train_mets=[]; val_mets=[]
for fold,(tr,va) in enumerate(tscv.split(inc), start=1):
    pipe = make_pipe(all_features, None, 'rf')
    Xtr,Xva=inc.loc[tr,all_features],inc.loc[va,all_features]
    ytr,yva=y.iloc[tr], y.iloc[va]
    pipe.fit(Xtr,ytr)
    for split_name,Xs,ys in [('train',Xtr,ytr),('val',Xva,yva)]:
        prob=pipe.predict_proba(Xs)[:,1]
        pred=(prob>=0.5).astype(int)
        metrics={
            'f1': f1_score(ys,pred,zero_division=0),'precision':precision_score(ys,pred,zero_division=0),'recall':recall_score(ys,pred,zero_division=0),
            'balanced_accuracy':balanced_accuracy_score(ys,pred),'average_precision':average_precision_score(ys,prob),'brier':brier_score_loss(ys,prob),
            'positive_rate_pred':float(pred.mean()),'positive_rate_true':float(ys.mean())}
        fold_records.append({'exp_id':'S8_00_rf_baseline_all_features','fold':fold,'split':split_name,'n_rows':len(ys),**metrics})
        if split_name=='train': train_mets.append(metrics)
        else: val_mets.append(metrics)
elapsed=time.time()-t0
experiments.append({
        'exp_id': 'S8_00_rf_baseline_all_features',
        'model': 'RandomForestClassifier',
        'features': '+'.join(all_features),
        'n_features_input': len(all_features),
        'threshold': 0.5,
        'f1_train_mean': float(np.mean([m['f1'] for m in train_mets])),
        'f1_val_mean': float(np.mean([m['f1'] for m in val_mets])),
        'f1_val_std': float(np.std([m['f1'] for m in val_mets], ddof=1)),
        'gap_train_val_f1': float(np.mean([m['f1'] for m in train_mets])-np.mean([m['f1'] for m in val_mets])),
        'average_precision_val_mean': float(np.mean([m['average_precision'] for m in val_mets])),
        'recall_val_mean': float(np.mean([m['recall'] for m in val_mets])),
        'precision_val_mean': float(np.mean([m['precision'] for m in val_mets])),
        'balanced_accuracy_val_mean': float(np.mean([m['balanced_accuracy'] for m in val_mets])),
        'brier_val_mean': float(np.mean([m['brier'] for m in val_mets])),
        'seconds': round(elapsed,3),
        'notes': 'Baseline de comparación para Sprint 8; no es la configuración ganadora de Sprint 7.'
    })

runs = pd.DataFrame(experiments)
runs = runs.sort_values('f1_val_mean', ascending=False).reset_index(drop=True)
runs.insert(0, 'rank', np.arange(1,len(runs)+1))
fold_df = pd.DataFrame(fold_records)
runs.to_csv(OUT/'logs/mlops_runs_sprint8.csv', index=False)
runs.to_csv(OUT/'results/experiment_dashboard_sprint8.csv', index=False)
fold_df.to_csv(OUT/'logs/overfitting_by_fold_sprint8.csv', index=False)

# ablation summary vs best all features
allrow = runs[runs['exp_id']=='S8_01_hpo_best_all_features'].iloc[0]
abl = runs.copy()
abl['delta_f1_vs_all_features'] = abl['f1_val_mean'] - float(allrow['f1_val_mean'])
abl['delta_ap_vs_all_features'] = abl['average_precision_val_mean'] - float(allrow['average_precision_val_mean'])
abl[['rank','exp_id','model','n_features_input','f1_val_mean','delta_f1_vs_all_features','average_precision_val_mean','delta_ap_vs_all_features','gap_train_val_f1','notes']].to_csv(OUT/'results/ablation_summary_sprint8.csv', index=False)

# overfitting gap summary
runs[['rank','exp_id','model','f1_train_mean','f1_val_mean','gap_train_val_f1','f1_val_std','brier_val_mean','notes']].to_csv(OUT/'results/overfitting_gap_sprint8.csv', index=False)

# plots
plt.figure(figsize=(10,5))
plot_df = runs.sort_values('f1_val_mean')
plt.barh(plot_df['exp_id'], plot_df['f1_val_mean'])
plt.xlabel('F1 promedio de validación temporal')
plt.title('Sprint 8 - Tablero de corridas MLOps ligero')
plt.tight_layout()
plt.savefig(OUT/'results/fig_experiment_dashboard_sprint8.png', dpi=160)
plt.close()

plt.figure(figsize=(10,5))
plot_df = runs.sort_values('gap_train_val_f1')
plt.barh(plot_df['exp_id'], plot_df['gap_train_val_f1'])
plt.xlabel('Gap F1 train - validación')
plt.title('Sprint 8 - Control de overfitting por corrida')
plt.axvline(0, linestyle='--')
plt.tight_layout()
plt.savefig(OUT/'results/fig_overfitting_gap_sprint8.png', dpi=160)
plt.close()

plt.figure(figsize=(10,5))
abl2 = abl[abl['exp_id']!='S8_01_hpo_best_all_features'].sort_values('delta_f1_vs_all_features')
plt.barh(abl2['exp_id'], abl2['delta_f1_vs_all_features'])
plt.axvline(0, linestyle='--')
plt.xlabel('Δ F1 vs HPO all features')
plt.title('Sprint 8 - Ablaciones: qué cambio movió la aguja')
plt.tight_layout()
plt.savefig(OUT/'results/fig_ablation_impact_sprint8.png', dpi=160)
plt.close()

# calibration and PR on last fold using all features best model
last_tr,last_va=list(tscv.split(inc))[-1]
pipe = make_pipe(all_features, best_params_sklearn, 'gb')
pipe.fit(inc.loc[last_tr, all_features], y.iloc[last_tr])
prob=pipe.predict_proba(inc.loc[last_va, all_features])[:,1]
prec, rec, th = precision_recall_curve(y.iloc[last_va], prob)
plt.figure(figsize=(7,5))
plt.plot(rec, prec)
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Sprint 8 - Curva Precision-Recall (último fold temporal)')
plt.tight_layout()
plt.savefig(OUT/'results/fig_precision_recall_sprint8.png', dpi=160)
plt.close()

frac_pos, mean_pred = calibration_curve(y.iloc[last_va], prob, n_bins=8, strategy='quantile')
plt.figure(figsize=(7,5))
plt.plot(mean_pred, frac_pos, marker='o')
plt.plot([0,1],[0,1], linestyle='--')
plt.xlabel('Probabilidad media predicha')
plt.ylabel('Fracción positiva observada')
plt.title('Sprint 8 - Calibración del modelo (último fold temporal)')
plt.tight_layout()
plt.savefig(OUT/'results/fig_calibration_sprint8.png', dpi=160)
plt.close()

# save final model on all data for artifact demo (processed data only)
final_pipe=make_pipe(all_features, best_params_sklearn, 'gb')
final_pipe.fit(inc[all_features], y)
joblib.dump(final_pipe, OUT/'artifacts/sprint8_demo_model.joblib')

# config/reproducibility
summary = json.loads((BASE/'data/processed/dataset_summary_hpo_sprint7.json').read_text())
config = {
    'project': 'Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC',
    'sprint': 'Sprint 8 - MLOps ligero, control de overfitting y demo 10-12 min',
    'base_from': 'Sprint 7 HPO',
    'data': summary,
    'validation': 'TimeSeriesSplit(n_splits=3)',
    'seed': 42,
    'target': 'label_over_ola',
    'primary_metric': 'F1 validación temporal',
    'secondary_metrics': ['precision','recall','average_precision','balanced_accuracy','brier'],
    'model_winner_from_sprint7': 'GradientBoostingClassifier + OrdinalEncoder + SimpleImputer',
    'winner_method': 'Random Search',
    'winner_trial': 8,
    'winner_params': {**best_params_sklearn, 'decision_threshold': threshold},
    'mlops_light_artifacts': {
        'runs': 'logs/mlops_runs_sprint8.csv',
        'folds': 'logs/overfitting_by_fold_sprint8.csv',
        'dashboard': 'results/experiment_dashboard_sprint8.csv',
        'ablations': 'results/ablation_summary_sprint8.csv',
        'overfitting': 'results/overfitting_gap_sprint8.csv',
        'model_artifact': 'artifacts/sprint8_demo_model.joblib'
    }
}
(OUT/'config/mlops_demo_sprint8_config.json').write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
(OUT/'artifacts/reproducibility_manifest_sprint8.json').write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')

# model card
model_card = f"""# Model Card - Sprint 8 Demo

**Proyecto:** Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC.  
**Modelo base:** GradientBoostingClassifier + OrdinalEncoder + SimpleImputer.  
**Target:** `label_over_ola` (Over OLA vs On Time).  
**Origen del ganador:** Sprint 7 HPO, Trial 8 con Random Search.  

## Data usada
- Incidentes históricos válidos para modelado: {summary['valid_rows_for_modeling']:,}
- Positivos Over OLA: {summary['target_positive_over_ola']:,}
- Negativos On Time: {summary['target_negative_on_time']:,}
- Tasa positiva: {summary['target_positive_rate']:.2%}
- Branches anonimizados: {summary['branch_count_anonymized']}
- Rango fechas incidentes: {summary['date_min']} a {summary['date_max']}

## Parámetros ganadores Sprint 7
```json
{json.dumps({**best_params_sklearn, 'decision_threshold': threshold}, indent=2, ensure_ascii=False)}
```

## Uso en demo
Este artefacto se usa para demostrar trazabilidad, reproducibilidad y control de overfitting. No se suben datos crudos ni identificadores sensibles.
"""
(OUT/'artifacts/model_card_sprint8.md').write_text(model_card, encoding='utf-8')

# source script copy
script = Path('/mnt/data/run_sprint8_compute.py').read_text(encoding='utf-8')
(OUT/'src/run_sprint8_mlops_demo.py').write_text(script, encoding='utf-8')

# notebook minimal
nb = {
 "cells": [
  {"cell_type":"markdown","metadata":{},"source":["# Sprint 8 - MLOps ligero y demo\n","Notebook resumen para revisar tablero, overfitting y ablaciones.\n"]},
  {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":["import pandas as pd\n","runs = pd.read_csv('../results/experiment_dashboard_sprint8.csv')\n","runs[['rank','exp_id','model','f1_val_mean','gap_train_val_f1','average_precision_val_mean']]\n"]},
  {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":["abl = pd.read_csv('../results/ablation_summary_sprint8.csv')\n","abl[['exp_id','f1_val_mean','delta_f1_vs_all_features','gap_train_val_f1']]\n"]},
  {"cell_type":"markdown","metadata":{},"source":["![Dashboard](../results/fig_experiment_dashboard_sprint8.png)\n","![Overfitting](../results/fig_overfitting_gap_sprint8.png)\n","![Ablaciones](../results/fig_ablation_impact_sprint8.png)\n"]}
 ],
 "metadata": {"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.x"}},
 "nbformat":4,"nbformat_minor":5
}
(OUT/'notebooks/03_mlops_overfitting_demo_sprint8.ipynb').write_text(json.dumps(nb, indent=2, ensure_ascii=False), encoding='utf-8')

# docs
best = json.loads((BASE/'artifacts/best_config_sprint7_hpo.json').read_text())
# Values for docs
best_metrics = best['metrics_validation_cv']

story = f"""# Demo 10-12 min - Sprint 8: storytelling técnico

## 0. Apertura (20-30 segundos)
Buenos días. En esta demo voy a presentar el avance de mi trabajo de investigación: **Modelos de IA para detección proactiva de fallas físicas en infraestructura de red NOC**. El objetivo es anticipar incidentes que podrían terminar como **Over OLA**, usando datos históricos de incidentes NOC TX/IP y una línea de trabajo reproducible en GitHub.

---

## 1. Problema y métrica (1 min)
El problema operativo es que en redes de telecomunicaciones no basta con reaccionar cuando el incidente ya venció el OLA. La meta es detectar patrones de riesgo antes de que el evento escale.

La variable objetivo es `label_over_ola`, que clasifica el incidente como **Over OLA** o **On Time**. Para evaluar el modelo uso principalmente **F1**, porque necesito balancear precision y recall. En este contexto no conviene usar solo accuracy, porque podría ocultar fallas en la clase crítica.

Data usada:
- 10,819 incidentes válidos para modelado.
- 3,505 casos Over OLA.
- 7,314 casos On Time.
- 44 branches operativos anonimizados.
- Rango temporal: 2022-08-14 a 2026-04-24.

---

## 2. Protocolo experimental (2 min)
Para que la comparación sea justa, mantuve el mismo seed, la misma métrica y el mismo esquema de validación. Usé **TimeSeriesSplit con 3 folds**, porque los incidentes tienen orden temporal. No debo entrenar con información futura para validar eventos pasados.

En Sprint 7 se compararon dos métodos de búsqueda de hiperparámetros: **Random Search** y **búsqueda Bayesiana**. Ambos buscaron hiperparámetros del mismo modelo: `GradientBoostingClassifier`.

El presupuesto fue:
- 12 trials Random Search.
- 12 trials Bayesianos.
- 24 trials en total.
- Early stopping con `n_iter_no_change` y `tol`.
- Pruning mediante `ccp_alpha` y regla de corte para trials de bajo rendimiento.

Es importante aclarar: Random y Bayes no son modelos. Son estrategias para buscar la mejor configuración del modelo.

---

## 3. Resultados principales (3-4 min)
El modelo ganador fue:

- **Modelo:** GradientBoostingClassifier.
- **Método ganador:** Random Search.
- **Trial ganador:** 8.
- **F1 promedio:** {best_metrics['f1_mean']:.4f}.
- **Precision:** {best_metrics['precision_mean']:.4f}.
- **Recall:** {best_metrics['recall_mean']:.4f}.
- **Average Precision:** {best_metrics['average_precision_mean']:.4f}.

Los hiperparámetros ganadores fueron:
- `n_estimators=60`: cantidad de árboles.
- `learning_rate=0.0783`: velocidad de aprendizaje.
- `max_depth=2`: complejidad máxima del árbol.
- `min_samples_leaf=59`: regularización por tamaño mínimo de hoja.
- `subsample=0.9233`: porcentaje de datos usados por iteración.
- `max_features=log2`: selección de variables por división.
- `ccp_alpha=0.000127`: poda del árbol.
- `n_iter_no_change=8` y `tol=0.000190`: early stopping.
- `decision_threshold=0.2304`: umbral final para clasificar Over OLA.

Para demostrarlo abro tres evidencias:
1. `artifacts/best_config_sprint7_hpo.json`: configuración ganadora.
2. `results/hpo_topk_sprint7.csv`: ranking top-k de configuraciones.
3. `logs/hpo_runs_sprint7.csv`: historial de trials.

En Sprint 8 agregué una capa de MLOps ligero: tablero de corridas, análisis de overfitting y ablaciones.

---

## 4. Ablaciones: qué cambio movió la aguja (2 min)
Una ablación significa cambiar solo una parte del pipeline y mantener todo lo demás igual. En mi caso, comparé el modelo completo contra variantes donde retiro grupos de variables.

Los experimentos controlados están en `results/ablation_summary_sprint8.csv`. La idea es responder qué variables aportan o perjudican bajo el mismo split, seed, modelo y métrica.

Lo explico así:
- Con todas las variables tengo la referencia principal.
- Sin `branch_id`, evalúo si la segmentación operativa aporta información.
- Sin `reason_group`, evalúo el peso de la causa/reason group.
- Con variables temporales solamente, mido si el patrón horario o calendario basta.
- Con variables operativas sin tiempo, mido el aporte de la información de operación.

Esto permite interpretar el modelo de forma más defendible, no solo como caja negra.

---

## 5. Riesgos y plan (1-2 min)
Riesgos identificados:
1. **Precision moderada/baja:** el modelo detecta muchos Over OLA, pero puede generar falsos positivos.
2. **Desbalance de clases:** la clase Over OLA representa aprox. 32.4%.
3. **Riesgo de leakage temporal:** se mitiga usando TimeSeriesSplit.
4. **Variabilidad por branch:** algunos branches pueden comportarse diferente.
5. **Data sensible:** no se suben tickets, coordenadas ni identificadores crudos.

Plan:
- Ajustar threshold según costo operativo de falso positivo vs falso negativo.
- Mejorar calibración del modelo.
- Agregar más señales de alarmas actuales.
- Evaluar métricas por branch operativo.
- Incorporar tracking tipo MLflow si el proyecto pasa a una fase más productiva.

---

## 6. Reproducibilidad (1 min)
Para reproducibilidad, el repositorio guarda configuración, código, logs, resultados y artefactos.

Estructura clave:
- `config/`: presupuesto y configuración.
- `notebooks/`: análisis y demo.
- `src/`: scripts reproducibles.
- `logs/`: corridas y folds.
- `results/`: tablas y figuras.
- `artifacts/`: modelo y configuración ganadora.
- `docs/`: reporte y guion.

Comando de referencia:
```bash
python src/run_sprint8_mlops_demo.py
```

Cierre:
El aporte de este sprint es que el proyecto ya no presenta solo un resultado aislado. Presenta un flujo trazable: problema, métrica, protocolo, resultados, ablaciones, riesgos y reproducibilidad.
"""
(OUT/'docs/demo_10_12_min_storytelling_sprint8.md').write_text(story, encoding='utf-8')

qna = """# Preguntas probables del profesor - Sprint 8 Demo

## 1. ¿Cuál es el modelo que estás usando?
Estoy usando un `GradientBoostingClassifier`, que es un modelo basado en árboles secuenciales. Cada árbol intenta corregir errores de los anteriores.

## 2. ¿Random Search y Bayes son modelos?
No. Random Search y búsqueda Bayesiana son métodos de búsqueda de hiperparámetros. El modelo es `GradientBoostingClassifier`.

## 3. ¿Qué hiperparámetros estás optimizando?
Optimizo hiperparámetros del `GradientBoostingClassifier`: `n_estimators`, `learning_rate`, `max_depth`, `min_samples_leaf`, `subsample`, `max_features`, `ccp_alpha`, `tol`, `n_iter_no_change` y el `decision_threshold` como umbral de decisión.

## 4. ¿Quién ganó?
Ganó el Trial 8 con Random Search usando `GradientBoostingClassifier`. Obtuvo F1 promedio aprox. 0.4986 en validación temporal.

## 5. ¿Cuáles fueron los parámetros ganadores?
`n_estimators=60`, `learning_rate≈0.0783`, `max_depth=2`, `min_samples_leaf=59`, `subsample≈0.9233`, `max_features=log2`, `ccp_alpha≈0.000127`, `tol≈0.000190`, `n_iter_no_change=8`, `decision_threshold≈0.2304`.

## 6. ¿Dónde demuestras la configuración ganadora?
En `artifacts/best_config_sprint7_hpo.json`, `results/hpo_topk_sprint7.csv` y `logs/hpo_runs_sprint7.csv`.

## 7. ¿Por qué usas F1 y no accuracy?
Porque el problema busca detectar la clase crítica `Over OLA`. Accuracy puede ser engañoso si hay desbalance de clases. F1 balancea precision y recall.

## 8. ¿Tienes alta precision?
No debo decir que la precision es alta. La precision es aprox. 0.3333. Lo que está alto es el recall, que llegó a 1.0. El modelo prioriza detección, pero debe mejorar falsos positivos.

## 9. ¿Qué significa recall alto?
Significa que el modelo detecta la mayoría o todos los casos Over OLA en validación, pero puede incluir falsos positivos.

## 10. ¿Qué significa precision baja/moderada?
Significa que no todos los casos predichos como Over OLA realmente terminan siendo Over OLA. Es un punto de mejora operacional.

## 11. ¿Por qué TimeSeriesSplit?
Porque los incidentes tienen orden temporal. Usar TimeSeriesSplit evita entrenar con datos futuros para validar el pasado.

## 12. ¿Qué es early stopping?
Es detener el entrenamiento si el modelo deja de mejorar después de cierto número de iteraciones. En mi caso se usa `n_iter_no_change=8` y `tol≈0.000190`.

## 13. ¿Qué es pruning?
Es una forma de reducir complejidad del modelo. En árboles se usa `ccp_alpha` para podar ramas que no aportan suficiente mejora.

## 14. ¿Qué guardaste para reproducibilidad?
Guardé configuración, scripts, notebooks, logs, resultados, gráficos y artefactos. No subí data cruda por confidencialidad.

## 15. ¿Cuánta data estás manejando?
Para el modelado principal uso 10,819 incidentes válidos. Además tengo 4,030 alarmas actuales limpias como insumo complementario operativo.

## 16. ¿Qué significa branch operativo?
Es una segmentación operativa anonimizada de la red o zona. No es un branch de GitHub. Sirve para analizar si ciertos grupos tienen mayor riesgo de Over OLA.

## 17. ¿Qué aportan las ablaciones?
Permiten cambiar una sola parte del pipeline y medir si mejora o empeora. Así se identifica qué componente realmente mueve la métrica.

## 18. ¿Qué riesgo principal tiene tu modelo?
El riesgo principal es generar falsos positivos por priorizar recall. El plan es calibrar probabilidades y ajustar el threshold según costo operativo.

## 19. ¿Qué diferencia hay entre Sprint 6, Sprint 7 y Sprint 8?
Sprint 6 fue baseline y estructura inicial. Sprint 7 agregó HPO Random/Bayes y configuración ganadora. Sprint 8 agrega MLOps ligero, tablero de corridas, overfitting, ablaciones y reproducibilidad.

## 20. ¿Cuál es el siguiente paso?
Mejorar calibración, ajustar threshold, validar por branch, agregar señales de alarmas actuales y preparar un flujo reproducible más cercano a MLflow.
"""
(OUT/'docs/preguntas_profesor_sprint8_qna.md').write_text(qna, encoding='utf-8')

report = f"""# Sprint 8 - MLOps ligero, overfitting y demo

## Objetivo
Agregar una capa de MLOps ligero al avance del Sprint 7: tablero de corridas, análisis de gap entrenamiento-validación, ablaciones, riesgos y reproducibilidad.

## Base utilizada
Se parte del entregable Sprint 7 HPO:
- Modelo ganador: `GradientBoostingClassifier`.
- Método ganador: Random Search.
- Trial ganador: 8.
- Target: `label_over_ola`.
- Validación: TimeSeriesSplit con 3 folds.

## Data
- Incidentes históricos válidos: {summary['valid_rows_for_modeling']:,}.
- Positivos Over OLA: {summary['target_positive_over_ola']:,}.
- Negativos On Time: {summary['target_negative_on_time']:,}.
- Branches anonimizados: {summary['branch_count_anonymized']}.

## Tablero de corridas
Archivo principal: `results/experiment_dashboard_sprint8.csv`.

Este tablero registra:
- `exp_id`
- modelo
- features usadas
- métrica F1 train/validación
- gap train-validación
- average precision
- recall
- precision
- tiempo
- notas

## Overfitting
Archivo principal: `results/overfitting_gap_sprint8.csv`.

Se mide el gap:
`F1_train_mean - F1_val_mean`.

Un gap alto indica posible sobreajuste. Un gap bajo o negativo sugiere que el modelo no está sobreajustando de forma evidente, aunque también puede indicar bajo poder predictivo o necesidad de mejores features.

## Ablaciones
Archivo principal: `results/ablation_summary_sprint8.csv`.

Ablaciones realizadas:
- Todas las features con configuración HPO ganadora.
- Sin `branch_id`.
- Sin `reason_group`.
- Solo variables temporales.
- Variables operativas sin tiempo.

## Gráficos principales
- `fig_experiment_dashboard_sprint8.png`: tablero visual de corridas.
- `fig_overfitting_gap_sprint8.png`: gap train-validación.
- `fig_ablation_impact_sprint8.png`: impacto de ablaciones.
- `fig_precision_recall_sprint8.png`: curva PR.
- `fig_calibration_sprint8.png`: calibración.

## Conclusión
Este sprint fortalece la defensa del proyecto porque conecta HPO con MLOps ligero: se demuestra cómo se comparan corridas, cómo se controla overfitting, qué cambios mueven la métrica y cómo se reproduce el experimento.
"""
(OUT/'docs/sprint8_mlops_overfitting_report.md').write_text(report, encoding='utf-8')

checklist = """# Checklist de exposición - Demo 10-12 min

## Antes de empezar
- Abrir repo en `main`.
- Tener listas las carpetas: `config`, `logs`, `results`, `artifacts`, `docs`.
- Abrir previamente `demo_10_12_min_storytelling_sprint8.md`.

## Archivos que se deben mostrar
1. `config/mlops_demo_sprint8_config.json`
2. `results/experiment_dashboard_sprint8.csv`
3. `results/fig_experiment_dashboard_sprint8.png`
4. `results/ablation_summary_sprint8.csv`
5. `results/fig_ablation_impact_sprint8.png`
6. `results/overfitting_gap_sprint8.csv`
7. `artifacts/reproducibility_manifest_sprint8.json`
8. `docs/preguntas_profesor_sprint8_qna.md`

## Frase obligatoria
“El ganador no fue elegido manualmente; fue seleccionado mediante comparación experimental y queda demostrado en logs, top-k y artefactos.”

## Cuidado
No decir: “precision muy alta”.
Decir: “recall alto, precision moderada/baja, y plan de mejora mediante calibración y ajuste de threshold.”
"""
(OUT/'docs/demo_checklist_sprint8.md').write_text(checklist, encoding='utf-8')

readme = """# Patch Sprint 8 - MLOps ligero y demo 10-12 min

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
"""
(OUT/'README_PATCH_SPRINT8_MLOPS.md').write_text(readme, encoding='utf-8')
commit = """# Comandos sugeridos para subir Sprint 8 MLOps Demo

git checkout main
git pull origin main
git checkout -b sprint8-mlops-demo

# Copiar carpetas del paquete al repo:
# config/, docs/, logs/, results/, artifacts/, src/, notebooks/

git add config docs logs results artifacts src notebooks README_PATCH_SPRINT8_MLOPS.md
git commit -m "Add Sprint 8 MLOps demo, overfitting analysis and Q&A"
git push origin sprint8-mlops-demo

# En GitHub:
# Compare & pull request -> Create pull request -> Merge pull request
"""
(OUT/'COMMIT_COMMANDS_SPRINT8_MLOPS.txt').write_text(commit, encoding='utf-8')

# zip package
import zipfile
zip_path = Path('/mnt/data/sprint8_mlops_demo_update.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(OUT))

print('OUT', OUT)
print('ZIP', zip_path, zip_path.stat().st_size)
print(runs[['rank','exp_id','model','f1_val_mean','gap_train_val_f1','average_precision_val_mean','recall_val_mean','precision_val_mean']].to_string(index=False))
