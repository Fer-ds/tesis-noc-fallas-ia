from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from contracts_sprint11 import PredictRequest, PredictResponse  # noqa: E402
from predict_cli_sprint11 import load_config, run_prediction  # noqa: E402


class ContractSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(ROOT / "config" / "deployment_sprint11.json")
        cls.valid_payload = json.loads(
            (ROOT / "examples" / "input_valid_sprint11.json").read_text(encoding="utf-8")
        )

    def test_smoke_valid_input_returns_valid_output(self) -> None:
        response = run_prediction(self.valid_payload, self.config)
        validated = PredictResponse.model_validate(response.model_dump())
        self.assertEqual(validated.status, "ok")
        self.assertEqual(validated.batch_size, 2)
        self.assertEqual(validated.positive_class_definition, "INCUMPLE_OLA")

    def test_invalid_hour_is_rejected(self) -> None:
        invalid = json.loads(
            (ROOT / "examples" / "input_invalid_sprint11.json").read_text(encoding="utf-8")
        )
        with self.assertRaises(Exception):
            PredictRequest.model_validate(invalid)

    def test_boundary_and_unknown_categories_are_supported(self) -> None:
        boundary = json.loads(
            (ROOT / "examples" / "input_boundary_sprint11.json").read_text(encoding="utf-8")
        )
        response = run_prediction(boundary, self.config)
        self.assertEqual(response.status, "ok")
        self.assertEqual(response.batch_size, 1)

    def test_safe_mode_is_default(self) -> None:
        response = run_prediction(self.valid_payload, self.config)
        self.assertEqual(response.decision_mode, "shadow_ranking")
        self.assertTrue(all("PRIORIZAR" in item.decision or "COLA" in item.decision for item in response.predictions))

    def test_schema_blocks_leakage_features(self) -> None:
        schema_text = json.dumps(PredictRequest.model_json_schema())
        for forbidden in ["duration_hours", "duration_hours_evidence", "label_source", "resolution_time"]:
            self.assertNotIn(forbidden, schema_text)


if __name__ == "__main__":
    unittest.main()
