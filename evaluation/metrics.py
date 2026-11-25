"""Evaluation metrics calculation for SkillBridge AI pipeline.

Computes precision, recall, F1 score, false positive rate, and scoring drift.

P2 FIX: Replaced arbitrary substring matching with canonical alias-aware exact matching.
Substring matching caused false positives (e.g. "rest api integration" matching "rest apis")
and false negatives (e.g. "object oriented programming" vs "object-oriented programming").
"""

from typing import Any, Iterable

# P2 FIX — Canonical equivalence map for metric matching.
# Maps normalized variant → canonical form so both sides are compared on the same label.
# Bidirectional where needed (both directions listed explicitly).
METRIC_EQUIVALENCES: dict[str, str] = {
    # REST API variants
    "rest api integration": "rest apis",
    "rest api": "rest apis",
    "rest": "rest apis",
    "restful": "rest apis",
    "rest api development": "rest apis",
    "rest api design": "rest apis",
    # Responsive design
    "responsive web design": "responsive design",
    # OOP casing
    "object oriented programming": "object-oriented programming",
    # AWS bidirectional (cases where dataset uses full name, alias dict uses abbreviation)
    "amazon web services": "aws",
    # Static site generators singular/plural
    "static site generators": "static site generator",
    # HuggingFace variants
    "huggingface transformers": "hugging face transformers",
    "huggingface": "hugging face transformers",
    "hugging face": "hugging face transformers",
    # Flutter / React Native combined catalogue entry
    "react native": "flutter or react native",
    "flutter": "flutter or react native",
    # SRE
    "slo/sli": "slo sli",
    "slos and slis": "slo sli",
    # Splunk
    "siem (splunk)": "splunk or sentinel",
    "splunk": "splunk or sentinel",
    # Power BI
    "microsoft power bi": "power bi",
    "powerbi": "power bi",
    # Scikit-learn
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    # Git aliases
    "github": "git",
    "gitlab": "git",
    # HTML/CSS versioned
    "html5": "html",
    "css3": "css",
}


def normalize_token(token: str) -> str:
    """Normalize a skill token for metric comparison."""
    if not token or not isinstance(token, str):
        return ""
    cleaned = token.strip().lower()
    return cleaned.replace("-", " ").replace("_", " ")


def canonical_token(token: str) -> str:
    """Apply normalize_token then resolve known equivalences to a single canonical form."""
    norm = normalize_token(token)
    return METRIC_EQUIVALENCES.get(norm, norm)


def compute_set_metrics(expected: Iterable[str], actual: Iterable[str]) -> dict[str, Any]:
    """Compute Precision, Recall, and F1 between expected and actual skill collections.

    P2 FIX: Uses canonical alias-aware exact matching instead of arbitrary substring matching.
    Two skills are a TP if and only if their canonical forms are equal.
    This eliminates false positives from partial substring overlap (e.g. "java" ⊂ "javascript")
    and false negatives from surface variation (e.g. hyphens, plurals, known synonyms).
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

    # Canonical sets for comparison
    exp_canonical = {canonical_token(e) for e in exp_set}
    act_canonical_map = {a: canonical_token(a) for a in act_set}

    # TP: actual item whose canonical form is in the expected canonical set
    tp = {a for a, c in act_canonical_map.items() if c in exp_canonical}
    tp_canonical = {act_canonical_map[a] for a in tp}

    fp = act_set - tp

    # FN: expected items whose canonical form was not covered by any TP
    fn = {e for e in exp_set if canonical_token(e) not in tp_canonical}

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
