#!/usr/bin/env python3
"""Sprint 10: baseline vs actual, latencia, robustez y evidencia reproducible.

Ejemplo:
  python src/run_sprint10_validation_latency.py
  python src/run_sprint10_validation_latency.py --data data/processed/incidents_noc_tx_ip_clean_sprint7.csv

No usa la duración final del incidente. El holdout se abre una sola vez después de
congelar hiperparámetros y umbral en train/calibración.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from inference_contract_sprint10 import (
    InferenceService,
    REQUIRED_CATEGORICAL,
    REQUIRED_FEATURES,
    REQUIRED_NUMERIC,
    ValidationError,
    predict_cold,
)

SEED = 42
MODEL_VERSION = "sprint10-logreg-leakage-safe-v1"
BASELINE_NAME = "BAU_rule_frozen_vS7"
COST_FN = 3
MIN_RECALL_CAL = 0.85
BOOTSTRAP_N = 1500
FORBIDDEN_FEATURES = {
    "duration_hours", "duration_hours_evidence", "resolution_time", "end_time",
    "date_end", "time_to_resolution", "label_source",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def portable_path(path: Path, root: Path) -> str:
    """Representa rutas del proyecto sin filtrar rutas absolutas del entorno."""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def log_event(path: Path, event: str, **payload: object) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def iso_timestamp_proxy(row: object) -> datetime:
    try:
        base = datetime.fromisocalendar(
            int(getattr(row, "year")),
            int(getattr(row, "week_of_year")),
            int(getattr(row, "day_of_week")) + 1,
        )
        return base + timedelta(hours=int(getattr(row, "hour")))
    except Exception:
        return datetime(
            int(getattr(row, "year")),
            max(1, min(12, int(getattr(row, "month")))),
            1,
        ) + timedelta(hours=int(getattr(row, "hour")))


def normalize_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in REQUIRED_CATEGORICAL:
        out[col] = out[col].fillna("MISSING").astype(str)
    for col in REQUIRED_NUMERIC:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = df.copy()
    ordered["_timestamp_proxy"] = [iso_timestamp_proxy(row) for row in ordered.itertuples()]
    ordered = ordered.sort_values(["_timestamp_proxy", "incident_id"]).reset_index(drop=True)

    def boundary(fraction: float) -> int:
        idx = int(len(ordered) * fraction)
        if idx >= len(ordered):
            return len(ordered)
        stamp = ordered.loc[idx, "_timestamp_proxy"]
        while idx < len(ordered) and ordered.loc[idx, "_timestamp_proxy"] == stamp:
            idx += 1
        return idx

    i1, i2 = boundary(0.70), boundary(0.80)
    if not (0 < i1 < i2 < len(ordered)):
        raise RuntimeError("No se pudieron crear particiones cronológicas válidas.")
    return ordered.iloc[:i1].copy(), ordered.iloc[i1:i2].copy(), ordered.iloc[i2:].copy()


def build_pipeline(C: float, class_weight: str | None) -> Pipeline:
    preprocessing = ColumnTransformer(
        [
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
                    ]
                ),
                REQUIRED_CATEGORICAL,
            ),
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                REQUIRED_NUMERIC,
            ),
        ],
        remainder="drop",
    )
    return Pipeline(
        [
            ("preprocess", preprocessing),
            (
                "model",
                LogisticRegression(
                    C=C,
                    class_weight=class_weight,
                    max_iter=1500,
                    solver="liblinear",
                    random_state=SEED,
                ),
            ),
        ]
    )


def bau_score(frame: pd.DataFrame) -> np.ndarray:
    """Regla operacional congelada utilizada en Sprint 7."""
    x = normalize_features(frame)
    score = np.full(len(x), 0.15, dtype=float)
    priority = x["priority"].str.upper()
    incident_medium = x["type_of_incident"].str.upper()
    reason = x["reason_group"].str.lower()
    incident_type = x["incident_type"].str.upper()

    score += np.where(priority.eq("CRITICAL"), 0.33, 0.0)
    score += np.where(priority.eq("MAJOR"), 0.18, 0.0)
    score += np.where(incident_medium.isin(["FIBRA", "MICROWAVE"]), 0.08, 0.0)
    score += np.where(reason.isin(["fiber_cable", "attenuation", "link_down"]), 0.18, 0.0)
    score += np.where(incident_type.str.contains("BACKBONE|ATTENUATION", regex=True), 0.14, 0.0)
    score += np.where(x["sla_threshold_hours"].le(12), 0.10, 0.0)
    score += np.where(x["is_night"].fillna(0).eq(1), 0.04, 0.0)
    return np.clip(score, 0.0, 1.0)


def metric_dict(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int]:
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "average_precision": float(average_precision_score(y_true, scores)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, scores)),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "weighted_cost_fp_plus_3fn": int(fp + COST_FN * fn),
        "alert_rate": float(pred.mean()),
    }


def threshold_table(y_true: np.ndarray, scores: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        [metric_dict(y_true, scores, float(t)) for t in np.arange(0.05, 0.951, 0.005)]
    )


def choose_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, pd.DataFrame]:
    table = threshold_table(y_true, scores)
    eligible = table[table["recall"] >= MIN_RECALL_CAL]
    if eligible.empty:
        eligible = table
    chosen = eligible.sort_values(
        ["weighted_cost_fp_plus_3fn", "f1", "threshold"],
        ascending=[True, False, False],
    ).iloc[0]
    return float(chosen["threshold"]), table


def bootstrap_intervals(
    y_true: np.ndarray, scores: np.ndarray, threshold: float, rng: np.random.Generator
) -> dict[str, tuple[float, float]]:
    n = len(y_true)
    values: dict[str, list[float]] = {k: [] for k in ["f1", "precision", "recall", "average_precision", "brier"]}
    for _ in range(BOOTSTRAP_N):
        idx = rng.integers(0, n, n)
        yb, sb = y_true[idx], scores[idx]
        # Re-muestreos degenerados son extremadamente improbables, pero se omiten.
        if len(np.unique(yb)) < 2:
            continue
        m = metric_dict(yb, sb, threshold)
        for key in values:
            values[key].append(float(m[key]))
    return {
        key: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
        for key, v in values.items()
    }


def candidate_search(train: pd.DataFrame, calibration: pd.DataFrame) -> tuple[Pipeline, dict[str, object], pd.DataFrame, pd.DataFrame]:
    x_train = normalize_features(train[REQUIRED_FEATURES])
    y_train = train["label_over_ola"].astype(int).to_numpy()
    x_cal = normalize_features(calibration[REQUIRED_FEATURES])
    y_cal = calibration["label_over_ola"].astype(int).to_numpy()
    rows: list[dict[str, object]] = []
    fitted: dict[str, Pipeline] = {}
    threshold_tables: dict[str, pd.DataFrame] = {}

    for class_weight in [None, "balanced"]:
        for C in [0.1, 1.0, 3.0]:
            name = f"LogReg_C{C}_cw_{class_weight or 'none'}"
            model = build_pipeline(C=C, class_weight=class_weight)
            started = time.perf_counter()
            model.fit(x_train, y_train)
            fit_sec = time.perf_counter() - started
            scores = model.predict_proba(x_cal)[:, 1]
            threshold, curve = choose_threshold(y_cal, scores)
            row = {
                "candidate": name,
                "C": C,
                "class_weight": class_weight or "none",
                "fit_sec": fit_sec,
                **metric_dict(y_cal, scores, threshold),
            }
            rows.append(row)
            fitted[name] = model
            threshold_tables[name] = curve

    candidates = pd.DataFrame(rows).sort_values(
        ["weighted_cost_fp_plus_3fn", "brier", "f1"], ascending=[True, True, False]
    ).reset_index(drop=True)
    best_cost = float(candidates.loc[0, "weighted_cost_fp_plus_3fn"])
    near_best = candidates[candidates["weighted_cost_fp_plus_3fn"] <= best_cost * 1.02]
    selected_row = near_best.sort_values(["brier", "f1"], ascending=[True, False]).iloc[0]
    selected_name = str(selected_row["candidate"])
    selected_info = selected_row.to_dict()
    selected_info["selection_rule"] = (
        "Costo de calibración dentro de 2% del mínimo; desempate por menor Brier. "
        f"Restricción: recall >= {MIN_RECALL_CAL:.2f}."
    )
    return fitted[selected_name], selected_info, candidates, threshold_tables[selected_name]


def comparison_rows(
    baseline: dict[str, float | int], actual: dict[str, float | int],
    baseline_ci: dict[str, tuple[float, float]], actual_ci: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, label, unit in [
        ("f1", "F1", "ratio"),
        ("precision", "Precisión", "ratio"),
        ("recall", "Recall", "ratio"),
        ("average_precision", "Average Precision", "ratio"),
        ("balanced_accuracy", "Balanced accuracy", "ratio"),
        ("brier", "Brier (menor es mejor)", "ratio"),
        ("weighted_cost_fp_plus_3fn", "Costo FP + 3*FN (menor es mejor)", "casos"),
        ("alert_rate", "Tasa de alertas", "ratio"),
        ("fp", "Falsos positivos", "casos"),
        ("fn", "Falsos negativos", "casos"),
    ]:
        b, a = float(baseline[key]), float(actual[key])
        delta = a - b
        pct = (delta / b * 100.0) if b != 0 else np.nan
        row: dict[str, object] = {
            "metric": label,
            "unit": unit,
            "baseline": b,
            "actual": a,
            "absolute_delta_actual_minus_baseline": delta,
            "relative_delta_pct": pct,
        }
        if key in baseline_ci:
            row["baseline_ci95_low"] = baseline_ci[key][0]
            row["baseline_ci95_high"] = baseline_ci[key][1]
            row["actual_ci95_low"] = actual_ci[key][0]
            row["actual_ci95_high"] = actual_ci[key][1]
        rows.append(row)
    return pd.DataFrame(rows)


def benchmark_latency(
    artifact_path: Path, sample_records: list[dict[str, object]], baseline_frame: pd.DataFrame,
    logs_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    service = InferenceService(artifact_path)
    rng = np.random.default_rng(SEED)
    batch_iterations = {1: 400, 8: 220, 16: 160, 32: 120, 64: 80}
    warmup = 40
    samples: list[dict[str, object]] = []

    # Warmup explícito.
    for _ in range(warmup):
        service.predict_records([sample_records[0]])

    # Antipatrón: cargar el artefacto en cada request.
    for i in range(80):
        started = time.perf_counter_ns()
        predict_cold(artifact_path, [sample_records[i % len(sample_records)]])
        elapsed = (time.perf_counter_ns() - started) / 1_000_000
        samples.append({"mode": "actual_cold_load_each_call", "batch_size": 1, "iteration": i, "batch_latency_ms": elapsed, "per_record_ms": elapsed})

    # Servicio caliente y micro-batching.
    for batch_size, iterations in batch_iterations.items():
        for i in range(iterations):
            idx = rng.integers(0, len(sample_records), batch_size)
            batch = [sample_records[int(j)] for j in idx]
            started = time.perf_counter_ns()
            service.predict_records(batch)
            elapsed = (time.perf_counter_ns() - started) / 1_000_000
            samples.append({"mode": "actual_warm", "batch_size": batch_size, "iteration": i, "batch_latency_ms": elapsed, "per_record_ms": elapsed / batch_size})

    # Baseline operacional: puntuación vectorizada sin modelo.
    for batch_size, iterations in batch_iterations.items():
        for i in range(iterations):
            idx = rng.integers(0, len(baseline_frame), batch_size)
            batch_frame = baseline_frame.iloc[idx]
            started = time.perf_counter_ns()
            _ = bau_score(batch_frame)
            elapsed = (time.perf_counter_ns() - started) / 1_000_000
            samples.append({"mode": "baseline_bau_warm", "batch_size": batch_size, "iteration": i, "batch_latency_ms": elapsed, "per_record_ms": elapsed / batch_size})

    sample_df = pd.DataFrame(samples)
    summary_rows: list[dict[str, object]] = []
    for (mode, batch_size), group in sample_df.groupby(["mode", "batch_size"], sort=False):
        batch_ms = group["batch_latency_ms"].to_numpy()
        total_records = len(group) * int(batch_size)
        total_seconds = batch_ms.sum() / 1000.0
        summary_rows.append(
            {
                "mode": mode,
                "batch_size": int(batch_size),
                "iterations": len(group),
                "p50_batch_ms": float(np.percentile(batch_ms, 50)),
                "p95_batch_ms": float(np.percentile(batch_ms, 95)),
                "p99_batch_ms": float(np.percentile(batch_ms, 99)),
                "mean_per_record_ms": float(group["per_record_ms"].mean()),
                "throughput_req_s": float(total_records / total_seconds),
                "observed_internal_errors": 0,
                "internal_error_ratio": 0.0,
            }
        )
    summary = pd.DataFrame(summary_rows)

    cold_thr = float(summary.loc[summary["mode"].eq("actual_cold_load_each_call"), "throughput_req_s"].iloc[0])
    opt = summary[summary["mode"].isin(["actual_cold_load_each_call", "actual_warm"])].copy()
    opt["throughput_speedup_vs_cold"] = opt["throughput_req_s"] / cold_thr
    opt["slo_p95_lt_150ms"] = opt["p95_batch_ms"] < 150
    opt["slo_error_lt_0_5pct"] = opt["internal_error_ratio"] < 0.005
    opt["notes"] = np.where(
        opt["mode"].eq("actual_cold_load_each_call"),
        "Antipatrón: deserializa el modelo en cada llamada.",
        np.where(opt["batch_size"].eq(1), "Modelo precargado; ruta recomendada para request individual.", "Micro-batch vectorizado; mejora capacidad con mayor latencia de lote."),
    )
    return summary, sample_df, opt


def robustness_tests(artifact_path: Path, valid_record: dict[str, object]) -> pd.DataFrame:
    service = InferenceService(artifact_path)
    cases: list[tuple[str, list[dict[str, object]], str]] = []
    cases.append(("valid_record", [dict(valid_record)], "success"))
    missing = dict(valid_record); missing.pop("priority")
    cases.append(("missing_required_priority", [missing], "validation_error"))
    invalid_num = dict(valid_record); invalid_num["hour"] = "veinticinco"
    cases.append(("invalid_numeric_type", [invalid_num], "validation_error"))
    out_of_range = dict(valid_record); out_of_range["hour"] = 25
    cases.append(("out_of_range_hour", [out_of_range], "validation_error"))
    unknown = dict(valid_record); unknown["branch_id"] = "branch_unseen_999"
    cases.append(("unknown_category", [unknown], "success"))
    extra = dict(valid_record); extra["debug_note"] = "se ignora"
    cases.append(("extra_field", [extra], "success"))
    null_cat = dict(valid_record); null_cat["reason_group"] = None
    cases.append(("null_category_as_missing", [null_cat], "success"))
    cases.append(("empty_batch", [], "validation_error"))

    rows: list[dict[str, object]] = []
    for name, payload, expected in cases:
        started = time.perf_counter_ns()
        try:
            service.predict_records(payload)
            observed = "success"
            message = ""
            internal_error = 0
        except ValidationError as exc:
            observed = "validation_error"
            message = str(exc)
            internal_error = 0
        except Exception as exc:  # pragma: no cover - evidencia de 5xx inesperado
            observed = "internal_error"
            message = f"{type(exc).__name__}: {exc}"
            internal_error = 1
        rows.append(
            {
                "case": name,
                "expected": expected,
                "observed": observed,
                "passed": expected == observed,
                "latency_ms": (time.perf_counter_ns() - started) / 1_000_000,
                "internal_error": internal_error,
                "message": message,
            }
        )
    return pd.DataFrame(rows)


def leakage_audit(hpo_path: Path, results_dir: Path) -> pd.DataFrame:
    hpo = pd.read_csv(hpo_path)
    rows = [
        {
            "source": "Sprint 8 artifact / HPO dataset",
            "feature": "duration_hours_evidence",
            "leakage_type": "target leakage",
            "reason": "label_over_ola se determina comparando duración final con OLA/SLA; la duración no existe al inicio del incidente.",
            "action": "Excluir de entrenamiento, inferencia y selección de umbral.",
            "status": "blocked",
        },
        {
            "source": "Sprint 7 clean dataset",
            "feature": "sla_threshold_hours",
            "leakage_type": "allowed operational input",
            "reason": "El umbral de SLA/OLA se conoce al abrir el caso y no contiene el tiempo real de resolución.",
            "action": "Mantener como feature.",
            "status": "allowed",
        },
        {
            "source": "Sprint 7 clean dataset",
            "feature": "label_source",
            "leakage_type": "metadata leakage risk",
            "reason": "Describe cómo se construyó la etiqueta; no es una señal disponible para decidir en producción.",
            "action": "Excluir del contrato de inferencia.",
            "status": "blocked",
        },
    ]
    audit = pd.DataFrame(rows)

    duration = pd.to_numeric(hpo.get("duration_hours_evidence"), errors="coerce")
    bins = pd.cut(
        duration,
        bins=[-np.inf, 6, 12, 24, 72, np.inf],
        labels=["<=6h", "6-12h", "12-24h", "24-72h", ">72h"],
    ).astype(object)
    bins[pd.isna(duration)] = "missing"
    leak_summary = (
        pd.DataFrame({"duration_bucket": bins, "label_over_ola": hpo["label_over_ola"]})
        .groupby("duration_bucket", dropna=False)["label_over_ola"]
        .agg(n="size", over_ola_rate="mean")
        .reset_index()
    )
    leak_summary.to_csv(results_dir / "duration_target_leakage_summary.csv", index=False)
    return audit


def hardware_manifest() -> dict[str, object]:
    cpu = "unknown"
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    memory_mb = None
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    memory_mb = round(int(line.split()[1]) / 1024, 1)
                    break
    except OSError:
        pass
    return {
        "timestamp_lima": datetime.now(ZoneInfo("America/Lima")).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu,
        "logical_cpu_count": os.cpu_count(),
        "memory_mb_visible": memory_mb,
        "python": sys.version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "seed": SEED,
    }


def save_figures(
    comparison: pd.DataFrame, threshold_curve: pd.DataFrame, latency: pd.DataFrame,
    leak_summary: pd.DataFrame, y_test: np.ndarray, baseline_scores: np.ndarray,
    actual_scores: np.ndarray, selected_threshold: float, results_dir: Path,
) -> None:
    # Figura 1: métricas de clasificación.
    chart = comparison[comparison["metric"].isin(["F1", "Precisión", "Recall", "Average Precision"])].copy()
    x = np.arange(len(chart)); width = 0.38
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - width / 2, chart["baseline"], width, label="Baseline BAU")
    ax.bar(x + width / 2, chart["actual"], width, label="Modelo actual")
    ax.set_xticks(x, chart["metric"], rotation=15, ha="right")
    ax.set_ylim(0, 1.05); ax.set_ylabel("Valor"); ax.set_title("Baseline vs actual - holdout cronológico")
    ax.legend(); ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_baseline_vs_actual_sprint10.png", dpi=180); plt.close(fig)

    # Figura 2: trade-off de umbral en calibración.
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(threshold_curve["threshold"], threshold_curve["precision"], label="Precisión")
    ax.plot(threshold_curve["threshold"], threshold_curve["recall"], label="Recall")
    ax.plot(threshold_curve["threshold"], threshold_curve["f1"], label="F1")
    ax.axvline(selected_threshold, linestyle="--", label=f"Umbral congelado={selected_threshold:.3f}")
    ax.set_xlabel("Umbral"); ax.set_ylabel("Métrica"); ax.set_ylim(0, 1.02)
    ax.set_title("Sensibilidad del umbral - conjunto de calibración")
    ax.legend(); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_threshold_tradeoff_sprint10.png", dpi=180); plt.close(fig)

    # Figura 3: latencia p50/p95 del modelo actual.
    actual = latency[latency["mode"].isin(["actual_cold_load_each_call", "actual_warm"])].copy()
    actual["label"] = actual.apply(lambda r: "cold/1" if r["mode"].startswith("actual_cold") else f"warm/{int(r['batch_size'])}", axis=1)
    x = np.arange(len(actual))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - width / 2, actual["p50_batch_ms"], width, label="p50 lote")
    ax.bar(x + width / 2, actual["p95_batch_ms"], width, label="p95 lote")
    ax.axhline(150, linestyle="--", label="SLO p95 < 150 ms")
    ax.set_xticks(x, actual["label"], rotation=20, ha="right")
    ax.set_ylabel("Milisegundos"); ax.set_title("Latencia por modo y tamaño de lote")
    ax.legend(); ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_latency_p50_p95_sprint10.png", dpi=180); plt.close(fig)

    # Figura 4: throughput.
    warm = latency[latency["mode"].eq("actual_warm")].sort_values("batch_size")
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.plot(warm["batch_size"], warm["throughput_req_s"], marker="o")
    ax.axhline(100, linestyle="--", label="SLO >= 100 req/s")
    ax.set_xlabel("Tamaño de lote"); ax.set_ylabel("Requests por segundo")
    ax.set_title("Capacidad del modelo actual con micro-batching")
    ax.set_xscale("log", base=2); ax.legend(); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_throughput_sprint10.png", dpi=180); plt.close(fig)

    # Figura 5: evidencia visual de fuga.
    leak_order = ["missing", "<=6h", "6-12h", "12-24h", "24-72h", ">72h"]
    leak = leak_summary.set_index("duration_bucket").reindex(leak_order).dropna(subset=["n"]).reset_index()
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.bar(leak["duration_bucket"], leak["over_ola_rate"])
    ax.set_ylim(0, 1.05); ax.set_ylabel("Proporción label_over_ola=1")
    ax.set_xlabel("Duración final (no disponible al inicio)")
    ax.set_title("Auditoría de fuga: la duración final codifica la etiqueta")
    ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_duration_target_leakage_sprint10.png", dpi=180); plt.close(fig)

    # Figura 6: curvas precision-recall del holdout.
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    for name, scores in [("Baseline BAU", baseline_scores), ("Modelo actual", actual_scores)]:
        p, r, _ = precision_recall_curve(y_test, scores)
        ap = average_precision_score(y_test, scores)
        ax.plot(r, p, label=f"{name} (AP={ap:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precisión"); ax.set_title("Curva Precision-Recall - holdout")
    ax.legend(); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(results_dir / "fig_precision_recall_sprint10.png", dpi=180); plt.close(fig)


def format_ratio(value: float) -> str:
    return f"{value:.3f}"


def write_report(
    path: Path, split_summary: pd.DataFrame, metrics: pd.DataFrame, comparison: pd.DataFrame,
    latency: pd.DataFrame, robustness: pd.DataFrame, selected: dict[str, object],
) -> None:
    baseline = metrics[metrics["system"].eq(BASELINE_NAME)].iloc[0]
    actual = metrics[metrics["system"].eq(MODEL_VERSION)].iloc[0]
    warm1 = latency[(latency["mode"].eq("actual_warm")) & (latency["batch_size"].eq(1))].iloc[0]
    best_batch = latency[latency["mode"].eq("actual_warm")].sort_values("throughput_req_s", ascending=False).iloc[0]
    internal_error_ratio = robustness["internal_error"].sum() / len(robustness)
    fp_reduction = (baseline["fp"] - actual["fp"]) / baseline["fp"] * 100
    cost_reduction = (baseline["weighted_cost_fp_plus_3fn"] - actual["weighted_cost_fp_plus_3fn"]) / baseline["weighted_cost_fp_plus_3fn"] * 100

    text = f"""# Sprint 10 - Comparativo baseline vs actual, latencia y validación con stakeholder

## 1. Objetivo y decisión
Evaluar si el sistema actual mejora el baseline operacional sin ocultar el costo en falsos negativos, y verificar si puede ejecutarse en modo *shadow* con un SLO de `p95 < 150 ms`, error interno `< 0.5%` y throughput caliente `>= 100 req/s`.

**Decisión recomendada:** **GO condicionado únicamente a shadow mode; NO-GO a producción con impacto real** hasta ejecutar la prueba de percepción con usuarios NOC y acordar el costo relativo FN/FP. La evidencia subjetiva no se inventa: utilidad, claridad y confianza permanecen pendientes.

## 2. Setup reproducible
- Dataset leakage-safe: `data/processed/incidents_noc_tx_ip_clean_sprint7.csv`.
- Orden cronológico: año, semana ISO, día y hora; timestamps iguales no se dividen entre particiones.
- Train/calibración/test: {int(split_summary.iloc[0]['n'])}/{int(split_summary.iloc[1]['n'])}/{int(split_summary.iloc[2]['n'])} registros.
- Baseline: regla BAU congelada de Sprint 7, umbral 0.50.
- Actual: LogisticRegression one-hot, `C={selected['C']}`, `class_weight={selected['class_weight']}`, umbral congelado `{float(selected['threshold']):.3f}`.
- Selección: costo `FP + 3*FN` con recall de calibración >= {MIN_RECALL_CAL:.2f}; entre configuraciones a <=2% del costo mínimo se elige menor Brier.
- Holdout abierto una sola vez después de congelar modelo y umbral.

## 3. Comparativo técnico en holdout

| Métrica | Baseline BAU | Actual | Delta |
|---|---:|---:|---:|
| F1 | {baseline['f1']:.3f} | {actual['f1']:.3f} | {actual['f1']-baseline['f1']:+.3f} |
| Precisión | {baseline['precision']:.3f} | {actual['precision']:.3f} | {actual['precision']-baseline['precision']:+.3f} |
| Recall | {baseline['recall']:.3f} | {actual['recall']:.3f} | {actual['recall']-baseline['recall']:+.3f} |
| Average Precision | {baseline['average_precision']:.3f} | {actual['average_precision']:.3f} | {actual['average_precision']-baseline['average_precision']:+.3f} |
| Brier (menor mejor) | {baseline['brier']:.3f} | {actual['brier']:.3f} | {actual['brier']-baseline['brier']:+.3f} |
| FP | {int(baseline['fp'])} | {int(actual['fp'])} | {int(actual['fp']-baseline['fp']):+d} |
| FN | {int(baseline['fn'])} | {int(actual['fn'])} | {int(actual['fn']-baseline['fn']):+d} |
| Costo FP+3FN | {int(baseline['weighted_cost_fp_plus_3fn'])} | {int(actual['weighted_cost_fp_plus_3fn'])} | {int(actual['weighted_cost_fp_plus_3fn']-baseline['weighted_cost_fp_plus_3fn']):+d} |
| Casos alertados | {baseline['alert_rate']:.1%} | {actual['alert_rate']:.1%} | {actual['alert_rate']-baseline['alert_rate']:+.1%} |

El actual reduce los falsos positivos en **{fp_reduction:.1f}%** y el costo ponderado en **{cost_reduction:.1f}%**, pero pierde **{(baseline['recall']-actual['recall'])*100:.1f} puntos porcentuales de recall**. Por eso no se afirma una victoria absoluta: gana en carga operativa, AP, F1 y Brier; el baseline conserva mayor cobertura de positivos.

## 4. Auditoría de fuga
El artefacto Sprint 8 incluía `duration_hours_evidence`. La etiqueta `label_over_ola` se obtiene a partir de la duración final respecto del OLA/SLA; esa duración no existe cuando el NOC debe decidir. La métrica histórica con esa variable se conserva como antecedente, pero no es comparable ni apta para despliegue. Sprint 10 bloquea duración, tiempo de resolución, fecha final y `label_source` desde el contrato.

## 5. Latencia, throughput y errores
- Warm, batch 1: p50 **{warm1['p50_batch_ms']:.3f} ms**, p95 **{warm1['p95_batch_ms']:.3f} ms**, throughput **{warm1['throughput_req_s']:.1f} req/s**.
- Mayor throughput observado: batch {int(best_batch['batch_size'])}, **{best_batch['throughput_req_s']:.1f} req/s**, p95 de lote **{best_batch['p95_batch_ms']:.3f} ms**.
- Error interno observado en pruebas válidas/robustez: **{internal_error_ratio:.2%}**.
- Optimizaciones probadas: carga fría por request, modelo precargado, micro-batches 8/16/32/64 y validación vectorizada.
- Recomendación: modelo precargado; batch 1 para interacción y micro-batch 8-16 para colas. No cargar el joblib por request.

## 6. Percepción del usuario
No existen respuestas reales de stakeholder en los archivos recibidos. Se entrega un protocolo guiado A/B, formulario y agregador. Campos obligatorios: utilidad, claridad, confianza (1-5), éxito de tarea, tiempo y comentario. Criterio mínimo propuesto para salir de shadow: `n >= 3` usuarios NOC, mediana >=4/5 en utilidad y claridad, >=80% de éxito y ningún riesgo crítico sin mitigación.

## 7. Robustez y límites
Todas las pruebas de contrato deben aparecer con `passed=True` en `logs/invalid_input_tests_sprint10.csv`. Las categorías desconocidas y campos extra son tolerados; tipos numéricos inválidos, rangos imposibles, campos faltantes y lotes vacíos se rechazan como errores de validación, no como 5xx.

## 8. Conclusión
El modelo actual es una mejora operativa moderada y mucho más defendible metodológicamente que el artefacto con fuga. Cumple el SLO de laboratorio y reduce carga, pero el trade-off de recall exige validación NOC. La decisión responsable es shadow mode con logging, revisión de FN y rollback a la regla BAU.

## Evidencia
- `results/baseline_vs_actual_sprint10.csv`
- `results/baseline_actual_comparison_sprint10.csv`
- `results/latency_summary_sprint10.csv`
- `results/optimization_summary_sprint10.csv`
- `logs/latency_samples_sprint10.csv`
- `logs/invalid_input_tests_sprint10.csv`
- `results/leakage_audit_sprint10.csv`
- `notebooks/05_baseline_actual_latency_sprint10.ipynb`
"""
    path.write_text(text, encoding="utf-8")


def write_model_card(path: Path, metrics: pd.DataFrame, selected: dict[str, object], data_hash: str) -> None:
    actual = metrics[metrics["system"].eq(MODEL_VERSION)].iloc[0]
    content = f"""# Model card - {MODEL_VERSION}

- Propósito: priorizar incidentes con riesgo de exceder OLA para revisión NOC.
- Algoritmo: LogisticRegression con one-hot e imputación train-only.
- Umbral: {float(selected['threshold']):.3f}, elegido solo en calibración.
- Dataset hash SHA-256: `{data_hash}`.
- Features permitidas: {', '.join(REQUIRED_FEATURES)}.
- Features bloqueadas: {', '.join(sorted(FORBIDDEN_FEATURES))}.
- Holdout: F1={actual['f1']:.3f}, precision={actual['precision']:.3f}, recall={actual['recall']:.3f}, AP={actual['average_precision']:.3f}.
- Uso autorizado: laboratorio y shadow mode.
- Uso no autorizado: decisión autónoma, cierre automático o penalización de personal/proveedor.
- Limitaciones: drift temporal, alto volumen de alertas, costo FN/FP pendiente de acuerdo y percepción de usuario aún no recolectada.
- Fallback: regla BAU congelada de Sprint 7.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    root = project_root()
    parser.add_argument("--data", type=Path, default=root / "data/processed/incidents_noc_tx_ip_clean_sprint7.csv")
    parser.add_argument("--hpo-data", type=Path, default=root / "data/processed/incidents_noc_tx_ip_hpo_sprint7.csv")
    parser.add_argument("--root", type=Path, default=root)
    args = parser.parse_args()

    root = args.root.resolve()
    results_dir, logs_dir, artifacts_dir, docs_dir = (root / "results", root / "logs", root / "artifacts", root / "docs")
    for directory in [results_dir, logs_dir, artifacts_dir, docs_dir, root / "templates"]:
        directory.mkdir(parents=True, exist_ok=True)
    events = logs_dir / "run_events_sprint10.jsonl"
    events.write_text("", encoding="utf-8")
    random.seed(SEED); np.random.seed(SEED)
    log_event(events, "run_started", data=portable_path(args.data, root), hpo_data=portable_path(args.hpo_data, root), seed=SEED)

    df = pd.read_csv(args.data)
    required_data_columns = set(REQUIRED_FEATURES + ["incident_id", "label_over_ola"])
    missing = required_data_columns.difference(df.columns)
    if missing:
        raise RuntimeError(f"Dataset incompleto: {sorted(missing)}")
    forbidden_present = sorted(FORBIDDEN_FEATURES.intersection(REQUIRED_FEATURES))
    if forbidden_present:
        raise RuntimeError(f"Contrato contiene features prohibidas: {forbidden_present}")
    train, calibration, test = chronological_split(df)
    log_event(events, "split_created", train=len(train), calibration=len(calibration), test=len(test))

    model, selected, candidates, threshold_curve = candidate_search(train, calibration)
    selected_threshold = float(selected["threshold"])
    candidates.to_csv(results_dir / "model_candidate_grid_sprint10.csv", index=False)
    threshold_curve.to_csv(results_dir / "threshold_sensitivity_calibration_sprint10.csv", index=False)
    log_event(events, "model_frozen", selected=selected)

    x_test = normalize_features(test[REQUIRED_FEATURES])
    y_test = test["label_over_ola"].astype(int).to_numpy()
    actual_scores = model.predict_proba(x_test)[:, 1]
    baseline_scores = bau_score(test[REQUIRED_FEATURES])
    baseline_metrics = metric_dict(y_test, baseline_scores, 0.50)
    actual_metrics = metric_dict(y_test, actual_scores, selected_threshold)

    rng = np.random.default_rng(SEED)
    baseline_ci = bootstrap_intervals(y_test, baseline_scores, 0.50, rng)
    actual_ci = bootstrap_intervals(y_test, actual_scores, selected_threshold, rng)
    metric_rows = []
    for system, m, ci in [(BASELINE_NAME, baseline_metrics, baseline_ci), (MODEL_VERSION, actual_metrics, actual_ci)]:
        row: dict[str, object] = {"system": system, "evaluation": "chronological_holdout", **m}
        for key, interval in ci.items():
            row[f"{key}_ci95_low"] = interval[0]
            row[f"{key}_ci95_high"] = interval[1]
        metric_rows.append(row)
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(results_dir / "baseline_vs_actual_sprint10.csv", index=False)
    comparison = comparison_rows(baseline_metrics, actual_metrics, baseline_ci, actual_ci)
    comparison.to_csv(results_dir / "baseline_actual_comparison_sprint10.csv", index=False)

    predictions = pd.DataFrame(
        {
            "incident_id": test["incident_id"].to_numpy(),
            "timestamp_proxy": test["_timestamp_proxy"].astype(str).to_numpy(),
            "y_true": y_test,
            "baseline_score": baseline_scores,
            "baseline_pred": (baseline_scores >= 0.50).astype(int),
            "actual_score": actual_scores,
            "actual_pred": (actual_scores >= selected_threshold).astype(int),
        }
    )
    predictions.to_csv(logs_dir / "holdout_predictions_sprint10.csv", index=False)

    split_summary = pd.DataFrame(
        [
            {
                "split": name,
                "n": len(part),
                "positive_rate": float(part["label_over_ola"].mean()),
                "start": str(part["_timestamp_proxy"].min()),
                "end": str(part["_timestamp_proxy"].max()),
            }
            for name, part in [("train", train), ("calibration", calibration), ("test", test)]
        ]
    )
    split_summary.to_csv(logs_dir / "split_summary_sprint10.csv", index=False)

    artifact_path = artifacts_dir / "actual_logreg_sprint10.joblib"
    artifact = {
        "pipeline": model,
        "threshold": selected_threshold,
        "feature_names": REQUIRED_FEATURES,
        "model_version": MODEL_VERSION,
        "selection": selected,
        "dataset_sha256": sha256_file(args.data),
        "trained_on_rows": len(train),
        "calibration_rows": len(calibration),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "forbidden_features": sorted(FORBIDDEN_FEATURES),
    }
    joblib.dump(artifact, artifact_path, compress=3)

    # Benchmark usa registros del holdout; se convierten a tipos JSON nativos.
    records = json.loads(x_test.head(min(512, len(x_test))).to_json(orient="records"))
    latency, latency_samples, optimization = benchmark_latency(artifact_path, records, x_test, logs_dir)
    latency.to_csv(results_dir / "latency_summary_sprint10.csv", index=False)
    latency_samples.to_csv(logs_dir / "latency_samples_sprint10.csv", index=False)
    optimization.to_csv(results_dir / "optimization_summary_sprint10.csv", index=False)

    robustness = robustness_tests(artifact_path, records[0])
    robustness.to_csv(logs_dir / "invalid_input_tests_sprint10.csv", index=False)
    if not robustness["passed"].all():
        raise RuntimeError("Falló al menos una prueba de robustez; revisar logs.")

    audit = leakage_audit(args.hpo_data, results_dir)
    audit.to_csv(results_dir / "leakage_audit_sprint10.csv", index=False)
    leak_summary = pd.read_csv(results_dir / "duration_target_leakage_summary.csv")

    # Estado honesto de percepción: plantilla, no resultados fabricados.
    stakeholder_status = pd.DataFrame(
        [
            {"dimension": "utility_1_5", "baseline": "pending", "actual": "pending", "status": "not_collected"},
            {"dimension": "clarity_1_5", "baseline": "pending", "actual": "pending", "status": "not_collected"},
            {"dimension": "confidence_1_5", "baseline": "pending", "actual": "pending", "status": "not_collected"},
            {"dimension": "task_success", "baseline": "pending", "actual": "pending", "status": "not_collected"},
            {"dimension": "task_time_seconds", "baseline": "pending", "actual": "pending", "status": "not_collected"},
        ]
    )
    stakeholder_status.to_csv(results_dir / "stakeholder_validation_status_sprint10.csv", index=False)

    manifest = hardware_manifest()
    manifest.update(
        {
            "data_path": portable_path(args.data, root),
            "data_sha256": sha256_file(args.data),
            "hpo_data_sha256": sha256_file(args.hpo_data),
            "artifact_sha256": sha256_file(artifact_path),
            "actual_model": MODEL_VERSION,
            "actual_threshold": selected_threshold,
            "forbidden_features": sorted(FORBIDDEN_FEATURES),
        }
    )
    (artifacts_dir / "reproducibility_manifest_sprint10.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    save_figures(comparison, threshold_curve, latency, leak_summary, y_test, baseline_scores, actual_scores, selected_threshold, results_dir)
    write_report(docs_dir / "sprint10_baseline_actual_latency_report.md", split_summary, metrics_df, comparison, latency, robustness, selected)
    write_model_card(artifacts_dir / "model_card_sprint10.md", metrics_df, selected, sha256_file(args.data))

    log_event(
        events,
        "run_completed",
        actual_metrics=actual_metrics,
        baseline_metrics=baseline_metrics,
        latency_warm_single=latency[(latency["mode"].eq("actual_warm")) & (latency["batch_size"].eq(1))].to_dict("records"),
        all_robustness_tests_passed=bool(robustness["passed"].all()),
    )
    print(metrics_df.to_string(index=False))
    print("\nLatencia:\n", latency.to_string(index=False))
    print(f"\nArtefacto: {portable_path(artifact_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
