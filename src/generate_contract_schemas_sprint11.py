"""Regenera los esquemas JSON del contrato Pydantic Sprint 11."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from contracts_sprint11 import ErrorResponse, PredictRequest, PredictResponse
except ImportError:  # pragma: no cover
    from src.contracts_sprint11 import ErrorResponse, PredictRequest, PredictResponse


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "contracts"


def dump(name: str, schema: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    dump("predict_request_schema_sprint11.json", PredictRequest.model_json_schema())
    dump("predict_response_schema_sprint11.json", PredictResponse.model_json_schema())
    dump("error_response_schema_sprint11.json", ErrorResponse.model_json_schema())
    print(f"Esquemas generados en {OUT}")


if __name__ == "__main__":
    main()
