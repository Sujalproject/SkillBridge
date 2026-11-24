"""Automated tests for the SkillBridge AI Evaluation Framework and ground-truth dataset.

Runs 100% offline without external API keys.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.evaluator import SkillBridgeEvaluator
from evaluation.metrics import compute_scoring_drift, compute_set_metrics


def test_evaluation_dataset_integrity():
    evaluator = SkillBridgeEvaluator()
    assert len(evaluator.cases) >= 20, "Evaluation dataset must contain at least 20 cases"

    for case in evaluator.cases:
        assert "id" in case
        assert "resume_text" in case and len(case["resume_text"].strip()) > 30
        assert "target_career" in case and len(case["target_career"].strip()) > 0
        assert "expected_extracted_skills" in case and len(case["expected_extracted_skills"]) > 0
        assert "expected_normalized_skills" in case and len(case["expected_normalized_skills"]) > 0
        assert "expected_matched_skills" in case
        assert "expected_missing_skills" in case
        assert "related_non_equivalent_skills" in case
        assert "proficiency_level" in case


def test_evaluation_metrics_computation():
    # Exact match
    res_exact = compute_set_metrics(["python", "sql"], ["python", "sql"])
    assert res_exact["precision"] == 1.0
    assert res_exact["recall"] == 1.0
    assert res_exact["f1"] == 1.0

    # Partial match
    res_partial = compute_set_metrics(["python", "sql", "docker"], ["python", "sql", "git"])
    assert res_partial["tp_count"] == 2
    assert res_partial["fp_count"] == 1
    assert res_partial["fn_count"] == 1
    assert round(res_partial["precision"], 2) == 0.67
    assert round(res_partial["recall"], 2) == 0.67

    # Disjoint
    res_disjoint = compute_set_metrics(["python"], ["java"])
    assert res_disjoint["tp_count"] == 0
    assert res_disjoint["f1"] == 0.0

    # Scoring drift
    drift = compute_scoring_drift(50.0, 55.0)
    assert drift["absolute_error"] == 5.0
    assert drift["relative_error"] == 0.1


def test_evaluator_normalization_performance():
    evaluator = SkillBridgeEvaluator()
    results = evaluator.evaluate_all()
    norm_m = results["normalization_metrics"]

    # Assert normalization meets strict quality bar (>= 95%)
    assert norm_m["mean_precision"] >= 0.95
    assert norm_m["mean_recall"] >= 0.95
    assert norm_m["mean_f1"] >= 0.95


def test_evaluator_matching_performance_and_zero_false_positives():
    evaluator = SkillBridgeEvaluator()
    results = evaluator.evaluate_all()
    match_m = results["matching_metrics"]

    # Assert matching metrics meet quality bar
    assert match_m["mean_precision"] >= 0.85
    assert match_m["mean_recall"] >= 0.70
    assert match_m["mean_f1"] >= 0.75

    # Crucial: verify zero false positive over-matching on non-equivalent skills
    assert results["false_positive_count"] == 0, (
        f"Detected {results['false_positive_count']} false positive matches on non-equivalent skills"
    )


def test_evaluator_scoring_properties_audit():
    evaluator = SkillBridgeEvaluator()
    results = evaluator.evaluate_all()

    # Verify that all 4 scoring properties pass across all 25 cases
    assert results["scoring_properties_verified"] is True
    assert results["scoring_anomalies"] == 0


def test_custom_jd_70_30_weighted_scoring_edge_cases():
    from backend.services.semantic_skill_gap_service import analyze_skill_gap

    # Case A: 100% Mandatory, 0% Preferred -> 70%
    res_mand = analyze_skill_gap(
        student_skills=["Python", "FastAPI"],
        required_skills=["Python", "FastAPI", "Kubernetes", "AWS"],
        mandatory_skills=["Python", "FastAPI"],
        preferred_skills=["Kubernetes", "AWS"],
    )
    assert res_mand["match_percentage"] == 70
    assert res_mand["scoring_breakdown"]["scoring_model"] == "weighted_custom_jd"
    assert res_mand["scoring_breakdown"]["mandatory_weight"] == 0.7
    assert res_mand["scoring_breakdown"]["preferred_weight"] == 0.3

    # Case B: 0% Mandatory, 100% Preferred -> 30%
    res_pref = analyze_skill_gap(
        student_skills=["Kubernetes", "AWS"],
        required_skills=["Python", "FastAPI", "Kubernetes", "AWS"],
        mandatory_skills=["Python", "FastAPI"],
        preferred_skills=["Kubernetes", "AWS"],
    )
    assert res_pref["match_percentage"] == 30

    # Case C: 100% Mandatory, No Preferred specified in JD -> 100%
    res_no_pref = analyze_skill_gap(
        student_skills=["Python", "FastAPI"],
        required_skills=["Python", "FastAPI"],
        mandatory_skills=["Python", "FastAPI"],
        preferred_skills=[],
    )
    assert res_no_pref["match_percentage"] == 100
    assert res_no_pref["scoring_breakdown"]["mandatory_weight"] == 1.0

    # Case D: No Mandatory specified in JD, 100% Preferred -> 100%
    res_no_mand = analyze_skill_gap(
        student_skills=["Kubernetes", "AWS"],
        required_skills=["Kubernetes", "AWS"],
        mandatory_skills=[],
        preferred_skills=["Kubernetes", "AWS"],
    )
    assert res_no_mand["match_percentage"] == 100
    assert res_no_mand["scoring_breakdown"]["preferred_weight"] == 1.0

    # Case E: Both empty -> 0%
    res_empty = analyze_skill_gap(
        student_skills=["Python"],
        required_skills=[],
        mandatory_skills=[],
        preferred_skills=[],
    )
    assert res_empty["match_percentage"] == 0


def test_predefined_role_importance_tiering():
    from backend.core.skill_importance import get_skill_importance
    from backend.services.semantic_skill_gap_service import analyze_skill_gap

    # Critical skill for Python Developer has weight 3.0
    crit_info = get_skill_importance("Python Developer", "python syntax and semantics")
    assert crit_info["weight"] == 3.0
    assert crit_info["tier"] == "critical"
    assert crit_info["is_critical"] is True

    # Secondary skill has weight 1.0
    sec_info = get_skill_importance("Python Developer", "celery")
    assert sec_info["weight"] == 1.0
    assert sec_info["tier"] == "secondary"

    # Unconfigured role defaults to 1.0 (equal weighting)
    default_info = get_skill_importance("Nonexistent Role", "python")
    assert default_info["weight"] == 1.0
    assert default_info["tier"] == "secondary"

    # Compare match score: critical skill contributes more than secondary skill
    res_crit = analyze_skill_gap(
        student_skills=["python syntax and semantics"],
        required_skills=["python syntax and semantics", "celery"],
        career="Python Developer",
    )
    # Weight: 3.0 out of 4.0 = 75%
    assert res_crit["match_percentage"] == 75

    res_sec = analyze_skill_gap(
        student_skills=["celery"],
        required_skills=["python syntax and semantics", "celery"],
        career="Python Developer",
    )
    # Weight: 1.0 out of 4.0 = 25%
    assert res_sec["match_percentage"] == 25


def test_proficiency_evidence_assessment():
    from backend.services.proficiency_service import assess_all_skills, assess_skill_proficiency

    resume_text = """
    Jane Doe
    Skills: Python, Docker, Kubernetes, SQL, PyTorch

    Experience:
    Backend Engineer at CloudCorp (3 years):
    - Built microservices using Python and Docker in production.
    - Managed relational schemas with PostgreSQL.

    Education:
    B.S. in Computer Science
    - Coursework: Machine Learning, Database Systems.
    """

    # Skill with professional employment evidence
    prof_res = assess_skill_proficiency("Python", resume_text, experience_list=["Built microservices using Python and Docker in production."])
    assert prof_res["evidence_tier"] == "professional"
    assert prof_res["confidence"] == "confirmed"

    # Skill with project / action evidence in text
    docker_res = assess_skill_proficiency("Docker", resume_text)
    assert docker_res["evidence_tier"] in ["professional", "project"]
    assert docker_res["confidence"] == "confirmed"

    # Skill with academic coursework evidence
    ml_res = assess_skill_proficiency("Machine Learning", resume_text, education_list=["Coursework: Machine Learning, Database Systems."])
    assert ml_res["evidence_tier"] == "academic"
    assert ml_res["confidence"] == "likely"

    # Skill mentioned only in skills list
    k8s_res = assess_skill_proficiency("Kubernetes", resume_text)
    assert k8s_res["evidence_tier"] == "mentioned"
    assert k8s_res["confidence"] == "likely"

    # Skill with no evidence
    rust_res = assess_skill_proficiency("Rust", resume_text)
    assert rust_res["evidence_tier"] == "insufficient_evidence"
    assert rust_res["confidence"] == "insufficient_evidence"


def test_match_explainability_and_scoring_breakdown():
    from backend.services.semantic_skill_gap_service import analyze_skill_gap

    res = analyze_skill_gap(
        student_skills=["Python", "FastAPI"],
        required_skills=["Python", "FastAPI", "Docker", "AWS"],
        career="Python Developer",
    )

    assert "match_explanations" in res
    assert "scoring_breakdown" in res
    assert "top_impact_gaps" in res

    # Python should be an exact match with confirmed confidence
    skills_matched = [e["skill"] for e in res["match_explanations"]]
    assert "Python" in skills_matched
    python_expl = [e for e in res["match_explanations"] if e["skill"] == "Python"][0]
    assert python_expl["match_type"] == "exact_match"
    assert python_expl["confidence"] == "confirmed"
