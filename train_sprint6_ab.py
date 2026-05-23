"""
train_sprint6_ab.py

Ejecuta la comparación A/B usando el dataset anonimizado de incidentes.
Requiere: scikit-learn, numpy, matplotlib.
"""
from pathlib import Path
import csv, time
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, average_precision_score, precision_recall_curve
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "incidents_noc_tx_ip_anon_sprint6.csv"
RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)

rows = []
with DATA.open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        r["year"] = int(float(r["year"]))
        r["quarter"] = int(float(r["quarter"]))
        r["month"] = int(float(r["month"]))
        r["week_of_year"] = int(float(r["week_of_year"]))
        r["sla_threshold_hours"] = float(r["sla_threshold_hours"])
        r["label_over_ola"] = int(r["label_over_ola"])
        rows.append(r)

rows = sorted(rows, key=lambda x: (x["year"], x["month"], x["week_of_year"], x["incident_id"]))
split = int(len(rows) * 0.8)
train, test = rows[:split], rows[split:]
y_train = np.array([r["label_over_ola"] for r in train])
y_test = np.array([r["label_over_ola"] for r in test])

cat_cols = ["area", "priority", "type_of_incident", "trouble_type", "incident_type", "network_id"]
cat_cols_v2 = cat_cols + ["branch_id"]
num_cols = ["year", "quarter", "month", "week_of_year", "sla_threshold_hours"]

def matrix(data, cols):
    return np.array([[r[c] for c in cols] for r in data], dtype=object)

def metrics(name, model, change, y_true, y_pred, y_score, train_time, pred_time):
    return {
        "experimento": name,
        "modelo": model,
        "cambio_realizado": change,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_over_ola": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall_over_ola": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_over_ola": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "average_precision": round(float(average_precision_score(y_true, y_score)), 4),
        "train_time_sec": round(float(train_time), 4),
        "latency_ms_per_1000": round(float(pred_time * 1000 / max(1, len(y_true)) * 1000), 4),
        "n_train": len(y_train),
        "n_test": len(y_test),
        "split": "temporal_80_20_fixed_seed_42",
    }

out = []
# Baseline rule
scores = []
for r in test:
    s = 0.15
    if r["priority"] == "CRITICAL": s += 0.35
    if r["priority"] == "MAJOR": s += 0.25
    if r["type_of_incident"] in ["FIBRA", "MICROWAVE"]: s += 0.10
    if any(k in r["trouble_type"] for k in ["LINK DOWN", "ATTENUATION", "BAD PERFORMANCE"]): s += 0.25
    if float(r["sla_threshold_hours"]) <= 12: s += 0.15
    scores.append(min(1, s))
pred = np.array([1 if s >= 0.5 else 0 for s in scores])
out.append(metrics("Baseline", "Regla operacional", "Prioridad + trouble + OLA", y_test, pred, np.array(scores), 0, 0.001))

# Var1
cols1 = cat_cols + num_cols
pre1 = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), list(range(len(cat_cols)))),
    ("num", StandardScaler(), list(range(len(cat_cols), len(cols1))))
])
clf1 = Pipeline([("pre", pre1), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])
start = time.perf_counter(); clf1.fit(matrix(train, cols1), y_train); tt = time.perf_counter()-start
start = time.perf_counter(); s1 = clf1.predict_proba(matrix(test, cols1))[:,1]; pt = time.perf_counter()-start
out.append(metrics("Var1", "LogisticRegression", "One-hot + temporal + balanceo", y_test, (s1>=0.5).astype(int), s1, tt, pt))

# Var2
cols2 = cat_cols_v2 + num_cols
pre2 = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", max_categories=50), list(range(len(cat_cols_v2)))),
    ("num", StandardScaler(), list(range(len(cat_cols_v2), len(cols2))))
])
clf2 = Pipeline([("pre", pre2), ("clf", RandomForestClassifier(n_estimators=250, max_depth=12, min_samples_leaf=5, class_weight="balanced", random_state=42, n_jobs=-1))])
start = time.perf_counter(); clf2.fit(matrix(train, cols2), y_train); tt = time.perf_counter()-start
start = time.perf_counter(); s2 = clf2.predict_proba(matrix(test, cols2))[:,1]; pt = time.perf_counter()-start
out.append(metrics("Var2", "RandomForestClassifier", "Branch anonimizado + umbral 0.40", y_test, (s2>=0.40).astype(int), s2, tt, pt))

with (RESULTS / "metrics_ab_sprint6.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)

p, r, _ = precision_recall_curve(y_test, s2)
plt.figure(figsize=(7, 5))
plt.plot(r, p, label="Var2 RandomForest")
plt.xlabel("Recall Over OLA")
plt.ylabel("Precision Over OLA")
plt.title("Precision-Recall Curve - Sprint 6")
plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(RESULTS / "pr_curve_sprint6.png", dpi=160)
print("Resultados actualizados en results/metrics_ab_sprint6.csv y results/pr_curve_sprint6.png")
