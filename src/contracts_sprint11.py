"""Contratos de entrada/salida del prototipo de despliegue Sprint 11.

Definición semántica:
- Clase real positiva: el incidente realmente incumple/supera el OLA.
- Predicción positiva: el sistema marca el registro como candidato de alerta.

El modo predeterminado es ``shadow_ranking``: el score se usa para ordenar y
observar, pero no elimina ni sustituye alertas de la regla BAU.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


DecisionMode = Literal["shadow_ranking", "alert_candidate", "baseline_only"]


class IncidentRecord(BaseModel):
    """Registro disponible al momento de apertura del incidente."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    domain: str | None = Field(default=None, max_length=80)
    area: str | None = Field(default=None, max_length=80)
    priority: str | None = Field(default=None, max_length=80)
    type_of_incident: str | None = Field(default=None, max_length=120)
    trouble_type: str | None = Field(default=None, max_length=120)
    incident_type: str | None = Field(default=None, max_length=160)
    network_id: str | None = Field(default=None, max_length=120)
    reason_group: str | None = Field(default=None, max_length=120)
    branch_id: str | None = Field(default=None, max_length=120)

    year: int = Field(ge=2020, le=2100)
    quarter: int = Field(ge=1, le=4)
    month: int = Field(ge=1, le=12)
    week_of_year: int = Field(ge=1, le=53)
    day_of_week: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    is_weekend: int = Field(ge=0, le=1)
    is_night: int = Field(ge=0, le=1)
    sla_threshold_hours: float = Field(gt=0.0, le=720.0)

    @field_validator(
        "domain", "area", "priority", "type_of_incident", "trouble_type",
        "incident_type", "network_id", "reason_group", "branch_id",
        mode="before",
    )
    @classmethod
    def normalize_category(cls, value: object) -> str:
        if value is None or str(value).strip() == "":
            return "MISSING"
        return str(value).strip()


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: f"req-{uuid4().hex[:16]}", max_length=80)
    records: list[IncidentRecord] = Field(min_length=1, max_length=64)
    decision_mode: DecisionMode = "shadow_ranking"
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class PredictionItem(BaseModel):
    record_index: int = Field(ge=0)
    risk_score: float = Field(ge=0.0, le=1.0)
    predicted_positive: bool
    decision: str
    ranking_band: Literal["ALTA", "MEDIA", "BAJA", "NO_APLICA"]
    threshold: float = Field(ge=0.0, le=1.0)
    latency_ms: float = Field(ge=0.0)


class PredictResponse(BaseModel):
    request_id: str
    status: Literal["ok", "model_disabled"]
    positive_class_definition: Literal["INCUMPLE_OLA"] = "INCUMPLE_OLA"
    prediction_positive_definition: Literal["CANDIDATO_ALERTA"] = "CANDIDATO_ALERTA"
    decision_mode: DecisionMode
    model_version: str
    model_sha256: str
    batch_size: int = Field(ge=0, le=64)
    model_load_ms: float = Field(ge=0.0)
    inference_total_ms: float = Field(ge=0.0)
    total_latency_ms: float = Field(ge=0.0)
    cold_start_included: bool = True
    slo_p95_target_ms: float = Field(gt=0.0)
    slo_applies_to: Literal["warm_inference"] = "warm_inference"
    predictions: list[PredictionItem]
    generated_at_utc: datetime


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    request_id: str | None = None
    status: Literal["error"] = "error"
    code: str
    message: str
    hint: str
    details: list[ErrorDetail] = []
