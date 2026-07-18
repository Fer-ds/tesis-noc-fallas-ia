from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd
from sklearn.metrics import confusion_matrix


ROOT = Path(__file__).resolve().parents[1]


class ConfusionMatrixEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frame = pd.read_csv(ROOT / "logs" / "holdout_predictions_sprint10.csv")

    def _counts(self, prediction) -> tuple[int, int, int, int]:
        tn, fp, fn, tp = confusion_matrix(
            self.frame["y_true"].astype(int), prediction, labels=[0, 1]
        ).ravel()
        return int(tn), int(fp), int(fn), int(tp)

    def test_original_threshold_counts(self) -> None:
        self.assertEqual(
            self._counts(self.frame["actual_pred"].astype(int)),
            (191, 1254, 54, 662),
        )

    def test_recall_first_candidate_counts(self) -> None:
        prediction = (self.frame["actual_score"].astype(float) >= 0.20).astype(int)
        self.assertEqual(self._counts(prediction), (68, 1377, 18, 698))

    def test_positive_is_actual_ola_breach(self) -> None:
        self.assertEqual(set(self.frame["y_true"].unique()), {0, 1})
        positives = int((self.frame["y_true"] == 1).sum())
        self.assertEqual(positives, 716)


if __name__ == "__main__":
    unittest.main()
