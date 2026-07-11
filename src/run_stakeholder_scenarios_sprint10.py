#!/usr/bin/env python3
"""Genera las salidas A/B para los escenarios anonimizados del protocolo."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from inference_contract_sprint10 import InferenceService, REQUIRED_FEATURES
from run_sprint10_validation_latency import bau_score


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=Path, default=root / "templates/stakeholder_scenarios_sprint10.csv")
    parser.add_argument("--artifact", type=Path, default=root / "artifacts/actual_logreg_sprint10.joblib")
    parser.add_argument("--output", type=Path, default=root / "results/stakeholder_scenario_outputs_sprint10.csv")
    args = parser.parse_args()

    scenarios = pd.read_csv(args.scenarios)
    records = scenarios[REQUIRED_FEATURES].where(pd.notna(scenarios[REQUIRED_FEATURES]), None).to_dict("records")
    service = InferenceService(args.artifact)
    actual = service.predict_records(records)
    baseline_scores = bau_score(scenarios[REQUIRED_FEATURES])

    out = scenarios[["scenario_id", "scenario_name", "business_question"]].copy()
    out["variant_A_score"] = baseline_scores
    out["variant_A_prediction"] = (baseline_scores >= 0.50).astype(int)
    out["variant_A_decision"] = out["variant_A_prediction"].map({1: "PRIORIZAR", 0: "NO_PRIORIZAR"})
    out["variant_B_score"] = [p.risk_score for p in actual]
    out["variant_B_threshold"] = [p.threshold for p in actual]
    out["variant_B_prediction"] = [p.prediction for p in actual]
    out["variant_B_decision"] = [p.decision for p in actual]
    out["facilitator_note"] = "No presentar ambas variantes simultáneamente; contrabalancear el orden."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
