#!/usr/bin/env python3
"""Valida y resume respuestas reales de la prueba A/B con stakeholder."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

REQUIRED = [
    "participant_id", "scenario_id", "variant", "task_success", "task_time_seconds",
    "utility_1_5", "clarity_1_5", "confidence_1_5", "critical_risk",
]


def validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(missing))
    if df.empty:
        return df
    out = df.copy()
    out["variant"] = out["variant"].astype(str).str.upper().str.strip()
    if not out["variant"].isin(["A", "B"]).all():
        raise ValueError("variant solo admite A o B.")
    for c in ["task_success", "critical_risk"]:
        out[c] = pd.to_numeric(out[c], errors="raise")
        if not out[c].isin([0, 1]).all():
            raise ValueError(f"{c} solo admite 0/1.")
    out["task_time_seconds"] = pd.to_numeric(out["task_time_seconds"], errors="raise")
    if (out["task_time_seconds"] < 0).any():
        raise ValueError("task_time_seconds no puede ser negativo.")
    for c in ["utility_1_5", "clarity_1_5", "confidence_1_5"]:
        out[c] = pd.to_numeric(out[c], errors="raise")
        if not out[c].between(1, 5).all():
            raise ValueError(f"{c} debe estar entre 1 y 5.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    df = validate(pd.read_csv(args.input))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if df.empty:
        status = pd.DataFrame([{"status": "not_collected", "message": "No hay respuestas reales; no se calculan métricas."}])
        status.to_csv(args.output_dir / "stakeholder_feedback_summary_sprint10.csv", index=False)
        print(status.to_string(index=False))
        return 0

    summary = (
        df.groupby("variant")
        .agg(
            participants=("participant_id", "nunique"),
            observations=("participant_id", "size"),
            task_success_rate=("task_success", "mean"),
            median_task_time_seconds=("task_time_seconds", "median"),
            median_utility=("utility_1_5", "median"),
            median_clarity=("clarity_1_5", "median"),
            median_confidence=("confidence_1_5", "median"),
            critical_risk_count=("critical_risk", "sum"),
        )
        .reset_index()
    )
    summary.to_csv(args.output_dir / "stakeholder_feedback_summary_sprint10.csv", index=False)

    # Comparación pareada por participante y escenario cuando existen ambas variantes.
    value_cols = ["task_success", "task_time_seconds", "utility_1_5", "clarity_1_5", "confidence_1_5"]
    pivot = df.pivot_table(index=["participant_id", "scenario_id"], columns="variant", values=value_cols, aggfunc="first")
    deltas = []
    for metric in value_cols:
        if (metric, "A") in pivot.columns and (metric, "B") in pivot.columns:
            d = (pivot[(metric, "B")] - pivot[(metric, "A")]).dropna()
            deltas.append({"metric": metric, "paired_n": len(d), "median_delta_B_minus_A": float(d.median()) if len(d) else np.nan, "mean_delta_B_minus_A": float(d.mean()) if len(d) else np.nan})
    pd.DataFrame(deltas).to_csv(args.output_dir / "stakeholder_paired_deltas_sprint10.csv", index=False)

    metrics = ["median_utility", "median_clarity", "median_confidence"]
    plot = summary.set_index("variant")[metrics].T
    fig, ax = plt.subplots(figsize=(8, 4.8))
    plot.plot(kind="bar", ax=ax)
    ax.set_ylim(0, 5.2); ax.set_ylabel("Mediana (1-5)")
    ax.set_title("Percepción A/B del stakeholder")
    ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(args.output_dir / "fig_stakeholder_perception_sprint10.png", dpi=180)
    plt.close(fig)

    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
