from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from predict_cli_sprint11 import load_config, run_prediction  # noqa: E402


class GoldenPredictionTests(unittest.TestCase):
    def test_golden_scores_are_stable(self) -> None:
        config = load_config(ROOT / "config" / "deployment_sprint11.json")
        payload = json.loads((ROOT / "examples" / "input_valid_sprint11.json").read_text(encoding="utf-8"))
        golden = json.loads((ROOT / "examples" / "golden_output_sprint11.json").read_text(encoding="utf-8"))
        response = run_prediction(payload, config)
        actual_scores = [item.risk_score for item in response.predictions]
        self.assertEqual(len(actual_scores), len(golden["risk_scores"]))
        for actual, expected in zip(actual_scores, golden["risk_scores"]):
            self.assertAlmostEqual(actual, expected, delta=golden["absolute_tolerance"])
        self.assertEqual(
            [item.predicted_positive for item in response.predictions],
            golden["predicted_positive"],
        )


if __name__ == "__main__":
    unittest.main()
