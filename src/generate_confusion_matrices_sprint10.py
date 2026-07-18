"""Genera matrices de confusión para Sprint 10.

Fuente:
    logs/holdout_predictions_sprint10.csv

Salidas:
    results/matriz_confusion_baseline_bau_sprint10.png
    results/matriz_confusion_modelo_actual_umbral_0245_sprint10.png
    results/matriz_confusion_modelo_actual_umbral_0200_candidato_sprint10.png
    results/comparativo_matrices_confusion_sprint10.csv

Notas metodológicas:
- y_true=1 significa que el incidente realmente incumplió/superó el OLA.
- y_pred=1 significa que el sistema emite una alerta.
- El umbral 0.200 es un análisis candidato posterior al feedback y debe
  revalidarse en un periodo temporal nuevo antes de considerarlo definitivo.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "logs" / "holdout_predictions_sprint10.csv"
RESULTS = ROOT / "results"


def save_confusion_figure(
    cm: np.ndarray,
    title: str,
    subtitle: str,
    output_path: Path,
) -> None:
    """Guarda una matriz con conteos y porcentajes por clase real."""
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    image = ax.imshow(cm)

    ax.set_xticks([0, 1], labels=["No alerta", "Alerta"])
    ax.set_yticks([0, 1], labels=["No incumple OLA", "Incumple OLA"])
    ax.set_xlabel("Predicción del sistema")
    ax.set_ylabel("Resultado real")
    ax.set_title(f"{title}\n{subtitle}")

    row_totals = cm.sum(axis=1, keepdims=True)
    row_pct = np.divide(
        cm,
        row_totals,
        out=np.zeros_like(cm, dtype=float),
        where=row_totals != 0,
    )
    labels = np.array([["TN", "FP"], ["FN", "TP"]])
    midpoint = (float(cm.max()) + float(cm.min())) / 2

    for row in range(2):
        for column in range(2):
            count = int(cm[row, column])
            percentage = row_pct[row, column] * 100
            text_color = "white" if count > midpoint else "black"
            ax.text(
                column,
                row,
                f"{labels[row, column]}\n{count:,}\n{percentage:.1f}% de la fila",
                ha="center",
                va="center",
                color=text_color,
                fontsize=12,
                fontweight="bold",
            )

    fig.colorbar(image, ax=ax, label="Cantidad de incidentes")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def calculate_row(
    name: str,
    threshold: float,
    y_true: np.ndarray,
    prediction: np.ndarray,
) -> dict[str, float | int | str]:
    """Calcula métricas y conteos de una configuración."""
    tn, fp, fn, tp = confusion_matrix(
        y_true,
        prediction,
        labels=[0, 1],
    ).ravel()

    return {
        "sistema": name,
        "umbral": threshold,
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
        "recall": recall_score(y_true, prediction, zero_division=0),
        "FNR": 1 - recall_score(y_true, prediction, zero_division=0),
        "precision": precision_score(y_true, prediction, zero_division=0),
        "F1": f1_score(y_true, prediction, zero_division=0),
        "tasa_alertas": float(prediction.mean()),
        "alertas_emitidas": int(prediction.sum()),
        "total_incidentes": int(len(prediction)),
    }


def main() -> None:
    if not PREDICTIONS.exists():
        raise FileNotFoundError(
            f"No se encontró {PREDICTIONS}. "
            "Ejecuta primero src/run_sprint10_validation_latency.py."
        )

    frame = pd.read_csv(PREDICTIONS)
    required = {"y_true", "baseline_pred", "actual_pred", "actual_score"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            "El archivo de predicciones no contiene las columnas requeridas: "
            + ", ".join(sorted(missing))
        )

    RESULTS.mkdir(parents=True, exist_ok=True)

    y_true = frame["y_true"].astype(int).to_numpy()
    configurations = [
        {
            "name": "Baseline BAU",
            "threshold": 0.500,
            "prediction": frame["baseline_pred"].astype(int).to_numpy(),
            "filename": "matriz_confusion_baseline_bau_sprint10.png",
            "subtitle": "Regla BAU congelada — umbral 0.500",
        },
        {
            "name": "Modelo actual",
            "threshold": 0.245,
            "prediction": frame["actual_pred"].astype(int).to_numpy(),
            "filename": "matriz_confusion_modelo_actual_umbral_0245_sprint10.png",
            "subtitle": "Umbral original 0.245",
        },
        {
            "name": "Modelo actual — candidato recall-first",
            "threshold": 0.200,
            "prediction": (
                frame["actual_score"].astype(float).to_numpy() >= 0.200
            ).astype(int),
            "filename": (
                "matriz_confusion_modelo_actual_umbral_0200_candidato_sprint10.png"
            ),
            "subtitle": "Umbral candidato 0.200 — sujeto a revalidación temporal",
        },
    ]

    rows = []
    for config in configurations:
        prediction = config["prediction"]
        cm = confusion_matrix(y_true, prediction, labels=[0, 1])
        save_confusion_figure(
            cm=cm,
            title=f"Matriz de confusión — {config['name']}",
            subtitle=config["subtitle"],
            output_path=RESULTS / config["filename"],
        )
        rows.append(
            calculate_row(
                name=config["name"],
                threshold=config["threshold"],
                y_true=y_true,
                prediction=prediction,
            )
        )

    summary = pd.DataFrame(rows)
    baseline = summary.iloc[0]
    summary["delta_FP_vs_baseline"] = summary["FP"] - baseline["FP"]
    summary["delta_FN_vs_baseline"] = summary["FN"] - baseline["FN"]
    summary["delta_recall_pp_vs_baseline"] = (
        summary["recall"] - baseline["recall"]
    ) * 100
    summary["delta_tasa_alertas_pp_vs_baseline"] = (
        summary["tasa_alertas"] - baseline["tasa_alertas"]
    ) * 100

    output_csv = RESULTS / "comparativo_matrices_confusion_sprint10.csv"
    summary.to_csv(output_csv, index=False)
    print(summary.to_string(index=False))
    print(f"\nArchivos generados en: {RESULTS}")


if __name__ == "__main__":
    main()
