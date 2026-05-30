"""
prepare_datasets.py

En este sprint los Excel crudos se procesaron localmente y NO se publican por confidencialidad.
Este script valida que existan los datasets anonimizados mínimos esperados.
"""
from pathlib import Path
import csv, json

BASE = Path(__file__).resolve().parents[1]
processed = BASE / "data" / "processed"
expected = [
    processed / "incidents_noc_tx_ip_anon_sprint6.csv",
    processed / "current_alarms_anon_sprint6.csv",
    processed / "dataset_summary_sprint6.json",
]

for path in expected:
    if not path.exists():
        raise FileNotFoundError(f"Falta archivo procesado: {path}")

for csv_path in expected[:2]:
    with csv_path.open(encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1
    print(f"OK: {csv_path.name}: {rows} filas")

print("Datasets procesados listos para entrenamiento y análisis.")
