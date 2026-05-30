"""
prepare_datasets_sprint7.py

Este script valida que los datasets procesados existan.
Los Excel crudos NO se publican en GitHub por confidencialidad.

Salida esperada:
- data/processed/incidents_noc_tx_ip_clean_sprint7.csv
- data/processed/current_alarms_clean_sprint7.csv
- data/processed/branch_summary_sprint7.csv
- data/processed/dataset_summary_sprint7.json
"""
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
REQUIRED = [
    "incidents_noc_tx_ip_clean_sprint7.csv",
    "current_alarms_clean_sprint7.csv",
    "branch_summary_sprint7.csv",
    "dataset_summary_sprint7.json",
]

missing = [name for name in REQUIRED if not (PROCESSED / name).exists()]
if missing:
    raise FileNotFoundError(f"Faltan archivos procesados: {missing}")

inc = pd.read_csv(PROCESSED / "incidents_noc_tx_ip_clean_sprint7.csv")
alarms = pd.read_csv(PROCESSED / "current_alarms_clean_sprint7.csv")
branch = pd.read_csv(PROCESSED / "branch_summary_sprint7.csv")

print("OK datasets procesados")
print(f"Incidentes modelables: {len(inc):,}")
print(f"Alarmas actuales procesadas: {len(alarms):,}")
print(f"Branches: {branch['branch_id'].nunique():,}")
print("Distribución target:")
print(inc["label_over_ola"].value_counts().to_string())

with open(PROCESSED / "dataset_summary_sprint7.json", encoding="utf-8") as f:
    print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
