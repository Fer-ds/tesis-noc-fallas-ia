"""CLI reproducible para inferencia local/batch del Sprint 11.

Uso:
    python src/predict_cli_sprint11.py \
      --input examples/input_valid_sprint11.json \
      --output results/prediction_cli_sprint11.json --pretty

La interfaz por defecto trabaja en ``shadow_ranking``. En ese modo la salida
no sustituye ni suprime alertas BAU; únicamente asigna score y prioridad.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

try:
    from contracts_sprint11 import (
        ErrorDetail,
        ErrorResponse,
        PredictRequest,
        PredictResponse,
        PredictionItem,
    )
    from inference_contract_sprint10 import InferenceService
except ImportError:  # pragma: no cover - soporte para python -m src...
    from src.contracts_sprint11 import (
        ErrorDetail,
        ErrorResponse,
        PredictRequest,
        PredictResponse,
        PredictionItem,
    )
    from src.inference_contract_sprint10 import InferenceService


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "deployment_sprint11.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    # Variables de entorno prevalecen sobre el archivo versionado.
    env_map = {
        "NOC_MODEL_PATH": ("model_path", str),
        "NOC_MODEL_ENABLED": ("model_enabled", lambda x: x.lower() in {"1", "true", "yes"}),
        "NOC_DECISION_MODE": ("decision_mode", str),
        "NOC_DECISION_THRESHOLD": ("decision_threshold", float),
        "NOC_MAX_BATCH_SIZE": ("max_batch_size", int),
        "NOC_MAX_PAYLOAD_BYTES": ("max_payload_bytes", int),
        "NOC_REQUEST_TIMEOUT_MS": ("request_timeout_ms", float),
        "NOC_LOG_LEVEL": ("log_level", str),
        "NOC_LOG_PATH": ("log_path", str),
        "NOC_METRICS_PATH": ("metrics_path", str),
        "NOC_SEED": ("seed", int),
    }
    for env_name, (key, caster) in env_map.items():
        if env_name in os.environ:
            config[key] = caster(os.environ[env_name])
    return config


def resolve_root_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_payload(path: Path, max_bytes: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Payload de {size} bytes excede el límite de {max_bytes} bytes.")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {"records": raw}
    if isinstance(raw, dict) and "records" in raw:
        return raw
    if isinstance(raw, dict):
        return {"records": [raw]}
    raise ValueError("El JSON debe ser un registro, una lista o un objeto con 'records'.")


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def append_metrics_csv(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    fields = [
        "timestamp_utc", "request_id", "status", "decision_mode", "batch_size",
        "total_latency_ms", "mean_latency_ms", "model_version", "threshold", "error_code",
    ]
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def error_from_pydantic(exc: PydanticValidationError, request_id: str | None = None) -> ErrorResponse:
    details: list[ErrorDetail] = []
    for issue in exc.errors():
        location = ".".join(str(part) for part in issue.get("loc", []))
        details.append(ErrorDetail(field=location or None, message=issue.get("msg", "Entrada inválida")))
    return ErrorResponse(
        request_id=request_id,
        code="INPUT_VALIDATION_ERROR",
        message="La entrada no cumple el contrato de inferencia.",
        hint="Revise campos obligatorios, tipos, rangos y el máximo de 64 registros por lote.",
        details=details,
    )


def _ranking_band(score: float, threshold: float, mode: str) -> str:
    if mode == "baseline_only":
        return "NO_APLICA"
    if score >= threshold:
        return "ALTA"
    if score >= max(0.0, threshold * 0.75):
        return "MEDIA"
    return "BAJA"


def run_prediction(payload: dict[str, Any], config: dict[str, Any]) -> PredictResponse:
    request = PredictRequest.model_validate(payload)
    if len(request.records) > int(config["max_batch_size"]):
        raise ValueError(
            f"El lote tiene {len(request.records)} registros y el límite configurado es "
            f"{config['max_batch_size']}."
        )

    mode = request.decision_mode or str(config["decision_mode"])
    threshold = float(
        request.threshold if request.threshold is not None else config["decision_threshold"]
    )
    model_path = resolve_root_path(str(config["model_path"]))
    model_hash = sha256_file(model_path)
    started = time.perf_counter_ns()

    if not bool(config.get("model_enabled", True)) or mode == "baseline_only":
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        return PredictResponse(
            request_id=request.request_id,
            status="model_disabled",
            decision_mode="baseline_only",
            model_version=str(config.get("fallback_baseline", "BAU_rule_frozen_vS7")),
            model_sha256=model_hash,
            batch_size=len(request.records),
            model_load_ms=0.0,
            inference_total_ms=0.0,
            total_latency_ms=elapsed_ms,
            cold_start_included=False,
            slo_p95_target_ms=float(config["request_timeout_ms"]),
            predictions=[],
            generated_at_utc=datetime.now(timezone.utc),
        )

    load_started = time.perf_counter_ns()
    service = InferenceService(model_path)
    model_load_ms = (time.perf_counter_ns() - load_started) / 1_000_000
    records = [record.model_dump() for record in request.records]
    inference_started = time.perf_counter_ns()
    raw_predictions = service.predict_records(records)
    inference_total_ms = (time.perf_counter_ns() - inference_started) / 1_000_000
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000

    items: list[PredictionItem] = []
    for index, raw in enumerate(raw_predictions):
        positive = raw.risk_score >= threshold
        if mode == "shadow_ranking":
            decision = "PRIORIZAR_PARA_REVISION" if positive else "MANTENER_COLA_ESTANDAR"
        else:
            decision = "ALERTA_OVER_OLA" if positive else "BAJO_UMBRAL"
        items.append(
            PredictionItem(
                record_index=index,
                risk_score=raw.risk_score,
                predicted_positive=positive,
                decision=decision,
                ranking_band=_ranking_band(raw.risk_score, threshold, mode),
                threshold=threshold,
                latency_ms=raw.latency_ms,
            )
        )

    return PredictResponse(
        request_id=request.request_id,
        status="ok",
        decision_mode=mode,
        model_version=service.model_version,
        model_sha256=model_hash,
        batch_size=len(items),
        model_load_ms=model_load_ms,
        inference_total_ms=inference_total_ms,
        total_latency_ms=elapsed_ms,
        cold_start_included=True,
        slo_p95_target_ms=float(config["request_timeout_ms"]),
        predictions=items,
        generated_at_utc=datetime.now(timezone.utc),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inferencia NOC Sprint 11 por CLI.")
    parser.add_argument("--input", required=True, type=Path, help="JSON de entrada.")
    parser.add_argument("--output", type=Path, help="Ruta JSON de salida; por defecto stdout.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    log_path = resolve_root_path(str(config["log_path"]))
    metrics_path = resolve_root_path(str(config["metrics_path"]))
    timestamp = datetime.now(timezone.utc).isoformat()
    request_id: str | None = None
    try:
        payload = load_payload(args.input, int(config["max_payload_bytes"]))
        request_id = payload.get("request_id") if isinstance(payload, dict) else None
        response = run_prediction(payload, config)
        rendered = response.model_dump(mode="json")
        text = json.dumps(rendered, ensure_ascii=False, indent=2 if args.pretty else None)
        if args.output:
            out = args.output if args.output.is_absolute() else ROOT / args.output
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)

        mean_ms = response.total_latency_ms / max(response.batch_size, 1)
        append_jsonl(log_path, {
            "timestamp_utc": timestamp,
            "request_id": response.request_id,
            "event": "prediction_completed",
            "status": response.status,
            "decision_mode": response.decision_mode,
            "batch_size": response.batch_size,
            "total_latency_ms": round(response.total_latency_ms, 6),
            "mean_latency_ms": round(mean_ms, 6),
            "model_version": response.model_version,
            "model_sha256": response.model_sha256,
            "threshold": response.predictions[0].threshold if response.predictions else None,
        })
        append_metrics_csv(metrics_path, {
            "timestamp_utc": timestamp,
            "request_id": response.request_id,
            "status": response.status,
            "decision_mode": response.decision_mode,
            "batch_size": response.batch_size,
            "total_latency_ms": round(response.total_latency_ms, 6),
            "mean_latency_ms": round(mean_ms, 6),
            "model_version": response.model_version,
            "threshold": response.predictions[0].threshold if response.predictions else "",
            "error_code": "",
        })
        return 0
    except PydanticValidationError as exc:
        error = error_from_pydantic(exc, request_id)
        code = 2
    except (ValueError, json.JSONDecodeError) as exc:
        error = ErrorResponse(
            request_id=request_id,
            code="INPUT_FORMAT_ERROR",
            message=str(exc),
            hint="Use los ejemplos de examples/ y valide el esquema JSON antes de ejecutar.",
        )
        code = 2
    except FileNotFoundError as exc:
        error = ErrorResponse(
            request_id=request_id,
            code="ARTIFACT_NOT_FOUND",
            message=str(exc),
            hint="Verifique NOC_MODEL_PATH y descargue/restaure el artefacto versionado.",
        )
        code = 3
    except Exception as exc:  # noqa: BLE001
        error = ErrorResponse(
            request_id=request_id,
            code="INTERNAL_ERROR",
            message=f"{type(exc).__name__}: {exc}",
            hint="Revise versiones fijadas, integridad del artefacto y logs de ejecución.",
        )
        code = 5

    err_text = json.dumps(error.model_dump(mode="json"), ensure_ascii=False, indent=2)
    print(err_text, file=sys.stderr)
    append_jsonl(log_path, {
        "timestamp_utc": timestamp,
        "request_id": request_id,
        "event": "prediction_failed",
        "status": "error",
        "error_code": error.code,
        "message": error.message,
    })
    append_metrics_csv(metrics_path, {
        "timestamp_utc": timestamp,
        "request_id": request_id or "",
        "status": "error",
        "decision_mode": config.get("decision_mode", ""),
        "batch_size": 0,
        "total_latency_ms": "",
        "mean_latency_ms": "",
        "model_version": "",
        "threshold": config.get("decision_threshold", ""),
        "error_code": error.code,
    })
    return code


if __name__ == "__main__":
    raise SystemExit(main())
