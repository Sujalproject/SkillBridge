#!/usr/bin/env python3
"""SkillBridge AI Evaluation Runner

Executes the automated AI evaluation suite against the synthetic evaluation dataset.
Usage:
    python -m evaluation.run
    python -m evaluation.run --verbose
    python -m evaluation.run --output evaluation/results/evaluation_report.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.evaluator import SkillBridgeEvaluator


def print_banner():
    print("=" * 80)
    print("   🌉 SkillBridge AI Intelligence & Scoring Calibration (Phase 9)")
    print("=" * 80)


def print_summary_table(summary: dict):
    norm_m = summary["normalization_metrics"]
    match_m = summary["matching_metrics"]
    scoring_models = summary.get("scoring_models", {})
    prof_dist = summary.get("proficiency_distribution", {})

    print("\n📊 OVERALL PIPELINE EVALUATION SUMMARY:")
    print("-" * 80)
    print(f" Total Synthetic Evaluation Cases : {summary['total_cases']}")
    print("-" * 80)
    print(" 1. Skill Normalization Performance:")
    print(f"    • Mean Precision : {norm_m['mean_precision'] * 100:.2f}%")
    print(f"    • Mean Recall    : {norm_m['mean_recall'] * 100:.2f}%")
    print(f"    • Mean F1 Score  : {norm_m['mean_f1'] * 100:.2f}%")
    print("-" * 80)
    print(" 2. Semantic Skill Matching Performance:")
    print(f"    • Mean Precision : {match_m['mean_precision'] * 100:.2f}%")
    print(f"    • Mean Recall    : {match_m['mean_recall'] * 100:.2f}%")
    print(f"    • Mean F1 Score  : {match_m['mean_f1'] * 100:.2f}%")
    print(f"    • False Positives Detected : {summary['false_positive_count']}")
    print("-" * 80)
    print(" 3. Career Match Scoring Calibration & Property Integrity:")
    print(f"    • Boundedness (0 - 100%)         : {'PASSED [✓]' if summary['scoring_properties_verified'] else 'FAILED [✗]'}")
    print(f"    • Score Monotonicity             : {'PASSED [✓]' if summary['scoring_properties_verified'] else 'FAILED [✗]'}")
    print(f"    • Neutrality to Unrelated Skills : {'PASSED [✓]' if summary['scoring_properties_verified'] else 'FAILED [✗]'}")
    print(f"    • Deduplication Resilience       : {'PASSED [✓]' if summary['scoring_properties_verified'] else 'FAILED [✗]'}")
    print(f"    • Target Calibration Alignment   : {'PASSED [✓]' if summary['scoring_anomalies'] == 0 else 'FAILED [✗]'}")
    print(f"    • Scoring Anomalies              : {summary['scoring_anomalies']}")
    print("    • Active Scoring Models:")
    for model_name, count in sorted(scoring_models.items()):
        print(f"      - {model_name}: {count} cases")
    print("-" * 80)
    print(" 4. Candidate Evidence-Based Proficiency Distribution:")
    for prof_level, count in sorted(prof_dist.items()):
        print(f"    • {prof_level}: {count} cases")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="SkillBridge AI Pipeline Evaluation")
    parser.add_argument("--output", type=str, default="evaluation/results/evaluation_report.json", help="Path to write report JSON")
    parser.add_argument("--verbose", action="store_true", help="Print detailed per-case metrics")
    args = parser.parse_args()

    print_banner()
    evaluator = SkillBridgeEvaluator()
    print(f"Loaded {len(evaluator.cases)} synthetic evaluation cases.")
    print("Evaluating normalization, skill gap matching, scoring properties, and proficiency...")

    results = evaluator.evaluate_all()
    print_summary_table(results)

    if args.verbose:
        print("\n🔍 PER-CASE EVALUATION BREAKDOWN:")
        for case_res in results["case_evaluations"]["matching"]:
            cid = case_res["case_id"]
            prec = case_res["match_metrics"]["precision"]
            rec = case_res["match_metrics"]["recall"]
            f1 = case_res["match_metrics"]["f1"]
            matched_len = len(case_res["actual_matched"])
            print(f"[{cid}] Matched: {matched_len} | P: {prec*100:.1f}% | R: {rec*100:.1f}% | F1: {f1*100:.1f}%")

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Complete evaluation report written to: {out_path}\n")


if __name__ == "__main__":
    main()
