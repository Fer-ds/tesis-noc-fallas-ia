# Patch README - Sprint 7 HPO Random/Bayes

Agregar al README principal debajo de la sección Sprint 7:

## Sprint 7 - HPO Random/Bayes con pruning y early stopping

Se agregó una corrida de búsqueda de hiperparámetros para cumplir el entregable de la semana 7:

- Experimentos comparables: `random_search` vs `bayesian_gp_ucb`.
- Validación temporal: `TimeSeriesSplit(n_splits=3)`.
- Métrica objetivo: F1 promedio para `label_over_ola`.
- Early stopping: activado en `GradientBoostingClassifier` mediante `n_iter_no_change` y `tol`.
- Pruning: `ccp_alpha` en árboles base y corte temprano de trials malos.
- Logs: `logs/hpo_runs_sprint7.csv` y `logs/hpo_events_sprint7.jsonl`.
- Artefactos: `artifacts/best_config_sprint7_hpo.json` y `artifacts/best_hpo_model_sprint7.joblib`.
- Resultados: `results/hpo_topk_sprint7.csv`, `results/fig_hpo_evolution_sprint7.png` y `results/fig_hpo_topk_sprint7.png`.

### Configuración ganadora

- Método: `random_search`.
- Trial: `8`.
- F1 validación: `0.4986 ± 0.0461`.
- Precision: `0.3333`.
- Recall: `1.0000`.
- Average Precision: `0.4395`.

La decisión se basa en el mayor F1 promedio en validación temporal y se mantiene la restricción de privacidad: solo se publican datos procesados/anonimizados, no data cruda ni identificadores internos.
