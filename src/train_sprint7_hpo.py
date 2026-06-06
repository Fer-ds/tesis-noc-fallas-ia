"""
Sprint 7 - HPO Random/Bayes para incidentes NOC TX/IP.
Ejecutar desde la raíz del repositorio:
    python src/train_sprint7_hpo.py

Este launcher revisa los artefactos generados del paquete. La corrida completa está documentada en docs/sprint7_hpo_report.md.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
print("Sprint 7 HPO package")
for p in [ROOT/"logs/hpo_runs_sprint7.csv", ROOT/"results/hpo_topk_sprint7.csv", ROOT/"results/fig_hpo_evolution_sprint7.png", ROOT/"artifacts/best_config_sprint7_hpo.json"]:
    print("-", p, "OK" if p.exists() else "NO ENCONTRADO")
cfg = ROOT / "artifacts/best_config_sprint7_hpo.json"
if cfg.exists():
    best=json.loads(cfg.read_text(encoding="utf-8"))
    print("
Config ganadora:")
    print(json.dumps(best, indent=2, ensure_ascii=False)[:3000])
