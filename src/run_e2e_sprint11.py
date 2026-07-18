"""Prueba end-to-end en limpio del prototipo CLI Sprint 11."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from contracts_sprint11 import PredictResponse
except ImportError:  # pragma: no cover
    from src.contracts_sprint11 import PredictResponse


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "examples" / "input_valid_sprint11.json"
OUTPUT = ROOT / "results" / "e2e_output_sprint11.json"
GOLDEN = ROOT / "examples" / "golden_output_sprint11.json"
SUMMARY = ROOT / "results" / "e2e_summary_sprint11.json"
LOG = ROOT / "logs" / "e2e_sprint11.log"
MANIFEST = ROOT / "artifacts" / "deployment_manifest_sprint11.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    started = datetime.now(timezone.utc)
    command = [
        sys.executable,
        str(ROOT / "src" / "predict_cli_sprint11.py"),
        "--input", str(INPUT),
        "--output", str(OUTPUT),
        "--pretty",
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    checks: dict[str, bool] = {
        "cli_exit_zero": completed.returncode == 0,
        "output_exists": OUTPUT.exists(),
    }
    errors: list[str] = []
    if completed.returncode != 0:
        errors.append(completed.stderr.strip())

    response = None
    if OUTPUT.exists():
        try:
            response = PredictResponse.model_validate_json(OUTPUT.read_text(encoding="utf-8"))
            checks["output_contract_valid"] = True
        except Exception as exc:  # noqa: BLE001
            checks["output_contract_valid"] = False
            errors.append(f"Contrato de salida: {exc}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if response is not None:
        checks["batch_size_expected"] = response.batch_size == 2
        checks["model_hash_matches_manifest"] = (
            response.model_sha256 == manifest["model_sha256"]
        )
        checks["scores_in_range"] = all(
            0.0 <= item.risk_score <= 1.0 for item in response.predictions
        )
        checks["safe_mode_default"] = response.decision_mode == "shadow_ranking"
        checks["positive_class_explicit"] = (
            response.positive_class_definition == "INCUMPLE_OLA"
        )

        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        actual_scores = [item.risk_score for item in response.predictions]
        expected_scores = golden["risk_scores"]
        checks["golden_scores_within_tolerance"] = (
            len(actual_scores) == len(expected_scores)
            and all(abs(a - e) <= golden["absolute_tolerance"] for a, e in zip(actual_scores, expected_scores))
        )
        checks["golden_labels_match"] = (
            [item.predicted_positive for item in response.predictions]
            == golden["predicted_positive"]
        )

    success = all(checks.values()) and not errors
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "started_at_utc": started.isoformat(),
        "success": success,
        "command": command,
        "checks": checks,
        "errors": errors,
        "input_sha256": sha256_file(INPUT),
        "output_sha256": sha256_file(OUTPUT) if OUTPUT.exists() else None,
        "criterion": (
            "Exit code 0; salida valida; 2 predicciones; scores 0..1; hash de modelo correcto; "
            "modo shadow_ranking; proyección estable igual al golden dentro de tolerancia."
        ),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        "\n".join([
            f"timestamp_utc={summary['timestamp_utc']}",
            f"success={success}",
            f"returncode={completed.returncode}",
            f"stdout={completed.stdout.strip()}",
            f"stderr={completed.stderr.strip()}",
            f"checks={json.dumps(checks, ensure_ascii=False)}",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
