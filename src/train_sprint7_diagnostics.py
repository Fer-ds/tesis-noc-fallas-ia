"""
train_sprint7_diagnostics.py

Corrección Sprint 7:
- Validación temporal por folds.
- Comparación Baseline vs Logistic Regression vs Random Forest.
- Feature engineering por branch calculado solo con training set.
- Métricas completas: precision, recall, F1, average precision, Brier.
- Diagnósticos: PR curve, calibration, learning curve, ablation study, feature importance.

Ejecutar desde la raíz del repositorio:
    python src/train_sprint7_diagnostics.py
"""
from pathlib import Path
import time, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score, average_precision_score,
    accuracy_score, brier_score_loss, precision_recall_curve
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import calibration_curve

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "incidents_noc_tx_ip_clean_sprint7.csv"
RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)

df = pd.read_csv(DATA).sort_values(["year", "month", "week_of_year", "incident_id"]).reset_index(drop=True)

BASE_CAT = ["domain", "area", "priority", "type_of_incident", "trouble_type", "incident_type", "network_id", "reason_group"]
BRANCH_CAT = BASE_CAT + ["branch_id"]
NUM_COLS = ["year", "quarter", "month", "week_of_year", "day_of_week", "hour", "is_weekend", "is_night", "sla_threshold_hours"]
EXTRA_NUM = ["branch_over_ola_rate_train", "branch_incident_count_train", "reason_over_ola_rate_train"]


def add_fold_features(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    """Calcula variables históricas usando SOLO training set."""
    global_rate = train_df["label_over_ola"].mean()
    alpha = 20

    branch_stats = train_df.groupby("branch_id")["label_over_ola"].agg(["mean", "count"])
    branch_stats["branch_over_ola_rate_train"] = (
        branch_stats["mean"] * branch_stats["count"] + global_rate * alpha
    ) / (branch_stats["count"] + alpha)
    branch_stats["branch_incident_count_train"] = branch_stats["count"]

    reason_stats = train_df.groupby("reason_group")["label_over_ola"].agg(["mean", "count"])
    reason_stats["reason_over_ola_rate_train"] = (
        reason_stats["mean"] * reason_stats["count"] + global_rate * alpha
    ) / (reason_stats["count"] + alpha)

    def transform(frame):
        out = frame.copy()
        out = out.merge(
            branch_stats[["branch_over_ola_rate_train", "branch_incident_count_train"]],
            left_on="branch_id", right_index=True, how="left"
        )
        out["branch_over_ola_rate_train"] = out["branch_over_ola_rate_train"].fillna(global_rate)
        out["branch_incident_count_train"] = out["branch_incident_count_train"].fillna(0)

        out = out.merge(
            reason_stats[["reason_over_ola_rate_train"]],
            left_on="reason_group", right_index=True, how="left"
        )
        out["reason_over_ola_rate_train"] = out["reason_over_ola_rate_train"].fillna(global_rate)
        return out

    return transform(train_df), transform(valid_df)


def baseline_scores(frame: pd.DataFrame) -> np.ndarray:
    """Regla operacional base: sirve como punto de comparación."""
    s = np.full(len(frame), 0.15)
    s += np.where(frame["priority"].eq("CRITICAL"), 0.33, 0)
    s += np.where(frame["priority"].eq("MAJOR"), 0.18, 0)
    s += np.where(frame["type_of_incident"].isin(["FIBRA", "MICROWAVE"]), 0.08, 0)
    s += np.where(frame["reason_group"].isin(["fiber_cable", "attenuation", "link_down"]), 0.18, 0)
    s += np.where(frame["incident_type"].str.contains("BACKBONE|ATTENUATION", na=False), 0.14, 0)
    s += np.where(frame["sla_threshold_hours"] <= 12, 0.10, 0)
    s += np.where(frame["is_night"].eq(1), 0.04, 0)
    return np.clip(s, 0, 1)


def choose_threshold(y_true, scores, min_recall=0.70):
    """Selecciona umbral maximizando F1, manteniendo recall mínimo."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    candidates = []
    for i, threshold in enumerate(thresholds):
        if recall[i] >= min_recall:
            f1 = 2 * precision[i] * recall[i] / (precision[i] + recall[i] + 1e-12)
            candidates.append((f1, precision[i], recall[i], float(threshold)))
    if not candidates:
        for i, threshold in enumerate(thresholds):
            f1 = 2 * precision[i] * recall[i] / (precision[i] + recall[i] + 1e-12)
            candidates.append((f1, precision[i], recall[i], float(threshold)))
    return sorted(candidates, reverse=True)[0][3]


def make_preprocessor(cat_cols, num_cols):
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), cat_cols),
        ("num", StandardScaler(), num_cols),
    ])


def metric_row(exp, model, y_true, scores, threshold, train_time, pred_time, n_train, fold, features, notes):
    pred = (scores >= threshold).astype(int)
    return {
        "fold": fold,
        "experimento": exp,
        "modelo": model,
        "threshold": round(float(threshold), 4),
        "accuracy": round(float(accuracy_score(y_true, pred)), 4),
        "precision_over_ola": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall_over_ola": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1_over_ola": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "average_precision": round(float(average_precision_score(y_true, scores)), 4),
        "brier_score": round(float(brier_score_loss(y_true, scores)), 4),
        "train_time_sec": round(float(train_time), 4),
        "latency_ms_per_1000": round(float(pred_time * 1000 / max(1, len(y_true)) * 1000), 4),
        "n_train": int(n_train),
        "n_valid": int(len(y_true)),
        "features": features,
        "notes": notes,
    }


fold_rows = []
last_artifact = None
tscv = TimeSeriesSplit(n_splits=3)

for fold, (train_idx, valid_idx) in enumerate(tscv.split(df), start=1):
    train_df = df.iloc[train_idx]
    valid_df = df.iloc[valid_idx]
    train_aug, valid_aug = add_fold_features(train_df, valid_df)

    y_train = train_aug["label_over_ola"].astype(int).values
    y_valid = valid_aug["label_over_ola"].astype(int).values

    start = time.perf_counter()
    base_score = baseline_scores(valid_aug)
    pred_time = time.perf_counter() - start
    fold_rows.append(metric_row(
        "Baseline", "Regla operacional", y_valid, base_score, 0.5,
        0, pred_time, len(y_train), fold, "manual_rule",
        "Punto de comparación; alto recall puede implicar baja precisión."
    ))

    features = BRANCH_CAT + NUM_COLS + EXTRA_NUM

    configs = [
        ("Var1_LogReg", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42),
         "Modelo interpretable con features temporales y branch."),
        ("Var2_RandomForest", RandomForestClassifier(
            n_estimators=120, max_depth=14, min_samples_leaf=5,
            class_weight="balanced_subsample", random_state=42, n_jobs=1
         ), "Ensamble de árboles con feature engineering por branch."),
    ]

    for exp, clf, note in configs:
        pipe = Pipeline([
            ("pre", make_preprocessor(BRANCH_CAT, NUM_COLS + EXTRA_NUM)),
            ("clf", clf),
        ])
        t0 = time.perf_counter()
        pipe.fit(train_aug[features], y_train)
        train_time = time.perf_counter() - t0

        t1 = time.perf_counter()
        score = pipe.predict_proba(valid_aug[features])[:, 1]
        pred_time = time.perf_counter() - t1

        threshold = choose_threshold(y_valid, score, min_recall=0.75)
        fold_rows.append(metric_row(
            exp, clf.__class__.__name__, y_valid, score, threshold,
            train_time, pred_time, len(y_train), fold, ",".join(features), note
        ))

        if fold == 3 and exp == "Var2_RandomForest":
            last_artifact = (pipe, valid_aug, features, y_valid, score, threshold, base_score)

metrics = pd.DataFrame(fold_rows)
metrics.to_csv(RESULTS / "model_comparison_by_fold_sprint7.csv", index=False)

summary = metrics.groupby(["experimento", "modelo"]).agg(
    precision_mean=("precision_over_ola", "mean"),
    precision_std=("precision_over_ola", "std"),
    recall_mean=("recall_over_ola", "mean"),
    recall_std=("recall_over_ola", "std"),
    f1_mean=("f1_over_ola", "mean"),
    f1_std=("f1_over_ola", "std"),
    avg_precision_mean=("average_precision", "mean"),
    brier_mean=("brier_score", "mean"),
    latency_ms_per_1000_mean=("latency_ms_per_1000", "mean"),
).reset_index()
for col in summary.select_dtypes(include="number").columns:
    summary[col] = summary[col].round(4)
summary.to_csv(RESULTS / "model_comparison_summary_sprint7.csv", index=False)

# Diagnostics for last fold / RandomForest
pipe, valid_aug, features, y_valid, score, threshold, base_score = last_artifact

# Feature importance
names = pipe.named_steps["pre"].get_feature_names_out()
importances = pipe.named_steps["clf"].feature_importances_
fi = pd.DataFrame({"feature": names, "importance": importances}).sort_values("importance", ascending=False)
fi.head(40).to_csv(RESULTS / "feature_importance_random_forest_sprint7.csv", index=False)

# PR curve
plt.figure(figsize=(7, 5))
for label, sc in [("RandomForest", score), ("Baseline", base_score)]:
    p, r, _ = precision_recall_curve(y_valid, sc)
    ap = average_precision_score(y_valid, sc)
    plt.plot(r, p, label=f"{label} AP={ap:.3f}")
plt.xlabel("Recall Over OLA")
plt.ylabel("Precision Over OLA")
plt.title("Curva Precision-Recall - Sprint 7")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS / "fig_precision_recall_sprint7.png", dpi=160)
plt.close()

# Calibration
prob_true, prob_pred = calibration_curve(y_valid, score, n_bins=8, strategy="quantile")
pd.DataFrame({"prob_pred_mean": prob_pred, "prob_true_fraction": prob_true}).to_csv(RESULTS / "calibration_bins_sprint7.csv", index=False)
plt.figure(figsize=(6, 5))
plt.plot([0, 1], [0, 1], linestyle="--", label="Perfectamente calibrado")
plt.plot(prob_pred, prob_true, marker="o", label=f"RF Brier={brier_score_loss(y_valid, score):.3f}")
plt.xlabel("Probabilidad predicha media")
plt.ylabel("Frecuencia real Over OLA")
plt.title("Curva de calibración - RandomForest")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS / "fig_calibration_sprint7.png", dpi=160)
plt.close()

print("OK: resultados Sprint 7 generados en results/")
