"""Evaluation metrics calculation for SkillBridge AI pipeline.

Computes precision, recall, F1 score, false positive rate, and scoring drift.
"""

from typing import Any, Iterable


def normalize_token(token: str) -> str:
    """Normalize a skill token for metric comparison."""
    if not token or not isinstance(token, str):
        return ""
    cleaned = token.strip().lower()
    return cleaned.replace("-", " ").replace("_", " ")


def compute_set_metrics(expected: Iterable[str], actual: Iterable[str]) -> dict[str, Any]:
    """Compute Precision, Recall, and F1 between expected and actual skill collections.

    Matching uses normalized string comparison.
    """
    exp_set = {normalize_token(x) for x in expected if normalize_token(x)}
    act_set = {normalize_token(x) for x in actual if normalize_token(x)}

    if not exp_set and not act_set:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "true_positives": [],
            "false_positives": [],
            "false_negatives": [],
            "tp_count": 0,
            "fp_count": 0,
            "fn_count": 0,
        }

    # True positives: in both expected and actual (fuzzy or exact normalized)
    tp = set()
    for a in act_set:
        if a in exp_set or any(a in e or e in a for e in exp_set if len(a) > 2 and len(e) > 2):
            tp.add(a)

    fp = act_set - tp
    # FN: expected items that weren't captured by any tp
    fn = set()
    for e in exp_set:
        if not any(e == t or (len(e) > 2 and len(t) > 2 and (e in t or t in e)) for t in tp):
            fn.add(e)

    tp_count = len(tp)
    fp_count = len(fp)
    fn_count = len(fn)

    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": sorted(list(tp)),
        "false_positives": sorted(list(fp)),
        "false_negatives": sorted(list(fn)),
        "tp_count": tp_count,
        "fp_count": fp_count,
        "fn_count": fn_count,
    }


def compute_scoring_drift(expected_score: float, actual_score: float) -> dict[str, float]:
    """Calculate absolute and relative deviation between expected and actual match score."""
    abs_diff = abs(actual_score - expected_score)
    rel_diff = (abs_diff / expected_score) if expected_score > 0 else 0.0
    return {
        "expected": expected_score,
        "actual": actual_score,
        "absolute_error": round(abs_diff, 2),
        "relative_error": round(rel_diff, 4),
    }
