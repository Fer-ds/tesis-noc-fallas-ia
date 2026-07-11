"""Contrato de inferencia y validación para Sprint 10.

Este módulo mantiene la lógica de servicio separada del entrenamiento. El artefacto
es un diccionario joblib con pipeline sklearn, umbral y metadatos. Las entradas
inválidas producen ValidationError (equivalente a 4xx); los errores inesperados
se consideran 5xx y se contabilizan por separado en las pruebas.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import time

import joblib
import numpy as np
import pandas as pd

REQUIRED_CATEGORICAL = [
    "domain", "area", "priority", "type_of_incident", "trouble_type",
    "incident_type", "network_id", "reason_group", "branch_id",
]
REQUIRED_NUMERIC = [
    "year", "quarter", "month", "week_of_year", "day_of_week", "hour",
    "is_weekend", "is_night", "sla_threshold_hours",
]
REQUIRED_FEATURES = REQUIRED_CATEGORICAL + REQUIRED_NUMERIC


class ValidationError(ValueError):
    """Entrada rechazada por contrato; debe mapearse a un error 4xx."""


@dataclass(frozen=True)
class Prediction:
    risk_score: float
    prediction: int
    decision: str
    threshold: float
    model_version: str
    latency_ms: float


def _records_to_frame(records: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise ValidationError("La entrada debe ser una secuencia de registros JSON.")
    if len(records) == 0:
        raise ValidationError("El lote no puede estar vacío.")
    if not all(isinstance(r, Mapping) for r in records):
        raise ValidationError("Cada elemento del lote debe ser un objeto/diccionario.")

    frame = pd.DataFrame(list(records))
    missing = [c for c in REQUIRED_FEATURES if c not in frame.columns]
    if missing:
        raise ValidationError("Faltan campos requeridos: " + ", ".join(missing))

    # Campos extra se ignoran de forma explícita para compatibilidad hacia delante.
    frame = frame[REQUIRED_FEATURES].copy()
    for col in REQUIRED_CATEGORICAL:
        frame[col] = frame[col].fillna("MISSING").astype(str)
    for col in REQUIRED_NUMERIC:
        converted = pd.to_numeric(frame[col], errors="coerce")
        invalid = frame[col].notna() & converted.isna()
        if invalid.any():
            bad = frame.loc[invalid, col].iloc[0]
            raise ValidationError(f"El campo numérico '{col}' contiene un valor inválido: {bad!r}")
        frame[col] = converted

    bounds = {
        "quarter": (1, 4), "month": (1, 12), "week_of_year": (1, 53),
        "day_of_week": (0, 6), "hour": (0, 23), "is_weekend": (0, 1),
        "is_night": (0, 1), "sla_threshold_hours": (0.01, 24 * 30),
    }
    for col, (lo, hi) in bounds.items():
        values = frame[col]
        invalid = values.notna() & ~values.between(lo, hi)
        if invalid.any():
            bad = values[invalid].iloc[0]
            raise ValidationError(f"'{col}' fuera de rango [{lo}, {hi}]: {bad}")
    return frame


class InferenceService:
    """Servicio en memoria. Cargar una vez y reutilizar por proceso."""

    def __init__(self, artifact_path: str | Path):
        self.artifact_path = Path(artifact_path)
        bundle = joblib.load(self.artifact_path)
        required = {"pipeline", "threshold", "feature_names", "model_version"}
        absent = required.difference(bundle)
        if absent:
            raise RuntimeError(f"Artefacto incompleto; faltan: {sorted(absent)}")
        self.pipeline = bundle["pipeline"]
        self.threshold = float(bundle["threshold"])
        self.feature_names = list(bundle["feature_names"])
        self.model_version = str(bundle["model_version"])
        if self.feature_names != REQUIRED_FEATURES:
            raise RuntimeError("El contrato de features no coincide con el artefacto.")

    def predict_records(self, records: Sequence[Mapping[str, Any]]) -> list[Prediction]:
        start = time.perf_counter_ns()
        frame = _records_to_frame(records)
        scores = self.pipeline.predict_proba(frame[self.feature_names])[:, 1]
        labels = (scores >= self.threshold).astype(int)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        per_record_ms = elapsed_ms / len(frame)
        return [
            Prediction(
                risk_score=float(score),
                prediction=int(label),
                decision="ALERTA_OVER_OLA" if label else "BAJO_UMBRAL",
                threshold=self.threshold,
                model_version=self.model_version,
                latency_ms=per_record_ms,
            )
            for score, label in zip(scores, labels)
        ]


def predict_cold(artifact_path: str | Path, records: Sequence[Mapping[str, Any]]) -> list[Prediction]:
    """Antipatrón medido: carga el modelo en cada llamada."""
    return InferenceService(artifact_path).predict_records(records)
