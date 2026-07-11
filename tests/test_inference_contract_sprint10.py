from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inference_contract_sprint10 import InferenceService, REQUIRED_FEATURES, ValidationError


class InferenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = InferenceService(ROOT / "artifacts/actual_logreg_sprint10.joblib")
        cls.record = {
            "domain": "IP", "area": "IPNOC", "priority": "CRITICAL",
            "type_of_incident": "FIBRA", "trouble_type": "LINK DOWN",
            "incident_type": "CABLE BROKEN ACCESS", "network_id": "network_005",
            "reason_group": "fiber_cable", "branch_id": "branch_001",
            "year": 2026, "quarter": 1, "month": 2, "week_of_year": 8,
            "day_of_week": 2, "hour": 10, "is_weekend": 0, "is_night": 0,
            "sla_threshold_hours": 15,
        }

    def test_feature_contract_has_no_duration(self):
        self.assertNotIn("duration_hours_evidence", REQUIRED_FEATURES)
        self.assertNotIn("duration_hours", REQUIRED_FEATURES)

    def test_valid_prediction(self):
        pred = self.service.predict_records([self.record])[0]
        self.assertIn(pred.prediction, (0, 1))
        self.assertGreaterEqual(pred.risk_score, 0.0)
        self.assertLessEqual(pred.risk_score, 1.0)
        self.assertEqual(pred.model_version, "sprint10-logreg-leakage-safe-v1")

    def test_unknown_category_is_supported(self):
        record = dict(self.record)
        record["branch_id"] = "branch_never_seen"
        self.assertEqual(len(self.service.predict_records([record])), 1)

    def test_missing_required_field_is_rejected(self):
        record = dict(self.record)
        record.pop("priority")
        with self.assertRaises(ValidationError):
            self.service.predict_records([record])

    def test_out_of_range_hour_is_rejected(self):
        record = dict(self.record)
        record["hour"] = 25
        with self.assertRaises(ValidationError):
            self.service.predict_records([record])

    def test_empty_batch_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.predict_records([])


class EvidenceTests(unittest.TestCase):
    def test_core_evidence_exists(self):
        required = [
            ROOT / "results/baseline_vs_actual_sprint10.csv",
            ROOT / "results/latency_summary_sprint10.csv",
            ROOT / "logs/invalid_input_tests_sprint10.csv",
            ROOT / "artifacts/reproducibility_manifest_sprint10.json",
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))

    def test_manifest_matches_contract(self):
        manifest = json.loads((ROOT / "artifacts/reproducibility_manifest_sprint10.json").read_text())
        self.assertEqual(manifest["actual_model"], "sprint10-logreg-leakage-safe-v1")
        self.assertIn("duration_hours_evidence", manifest["forbidden_features"])


if __name__ == "__main__":
    unittest.main()
