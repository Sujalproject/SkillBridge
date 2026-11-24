"""Core Evaluation Engine for SkillBridge AI pipeline.

Evaluates:
1. Skill Extraction & Normalization
2. Semantic Skill Matching & False Positive Rates
3. Career Match Scoring Formula Integrity & Monotonicity
4. Proficiency Evidence Assessment
5. Roadmap Personalization & Learning Resource Logic
"""

import json
from pathlib import Path
from typing import Any

from backend.services.career_service import get_required_skills
from backend.services.proficiency_service import assess_all_skills
from backend.services.semantic_skill_gap_service import analyze_skill_gap, normalize_skill
from evaluation.metrics import compute_set_metrics


class SkillBridgeEvaluator:
    """Evaluates the SkillBridge pipeline against ground-truth evaluation cases."""

    def __init__(self, cases_path: Path | None = None):
        if cases_path is None:
            cases_path = Path(__file__).resolve().parent / "dataset" / "cases.json"
        self.cases_path = cases_path
        self.cases: list[dict[str, Any]] = self._load_cases()

    def _load_cases(self) -> list[dict[str, Any]]:
        with open(self.cases_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_normalization(self, case: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Phase A/C: Skill token normalization."""
        extracted = case.get("expected_extracted_skills", [])
        expected_norm = case.get("expected_normalized_skills", [])
        actual_norm = [normalize_skill(s) for s in extracted]

        metrics = compute_set_metrics(expected_norm, actual_norm)
        return {
            "case_id": case["id"],
            "metrics": metrics,
            "actual_normalized": actual_norm,
        }

    def evaluate_skill_matching(self, case: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Phase D: Semantic skill matching against required career or custom JD."""
        target_career = case["target_career"]
        job_description = case.get("job_description")
        student_skills = case.get("expected_extracted_skills", [])
        mandatory_skills = case.get("mandatory_skills")
        preferred_skills = case.get("preferred_skills")

        # Get required benchmark skills
        if job_description:
            if mandatory_skills is not None or preferred_skills is not None:
                required_skills = (mandatory_skills or []) + (preferred_skills or [])
            else:
                required_skills = case.get("expected_matched_skills", []) + case.get("expected_missing_skills", [])
        else:
            required_skills = get_required_skills(target_career)

        gap_result = analyze_skill_gap(
            student_skills=student_skills,
            required_skills=required_skills,
            career=target_career,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
        )

        actual_matched = gap_result["matched_skills"]
        actual_missing = gap_result["missing_skills"]
        expected_matched = case.get("expected_matched_skills", [])

        match_metrics = compute_set_metrics(expected_matched, actual_matched)

        # Check for false positive matches against non-equivalent skills
        non_equivalent_checks = []
        false_positive_matches = []
        actual_matched_norm = {normalize_skill(m) for m in actual_matched}

        for rel in case.get("related_non_equivalent_skills", []):
            non_eq = rel.get("non_equivalent_to", "")
            norm_non_eq = normalize_skill(non_eq)
            is_falsely_matched = (norm_non_eq in actual_matched_norm) or any(
                norm_non_eq in m for m in actual_matched_norm
            )
            non_equivalent_checks.append({
                "candidate_skill": rel.get("skill"),
                "non_equivalent_to": non_eq,
                "falsely_matched": is_falsely_matched,
                "reason": rel.get("reason"),
            })
            if is_falsely_matched:
                false_positive_matches.append(non_eq)

        return {
            "case_id": case["id"],
            "match_metrics": match_metrics,
            "actual_matched": actual_matched,
            "actual_missing": actual_missing,
            "match_percentage": gap_result["match_percentage"],
            "scoring_breakdown": gap_result.get("scoring_breakdown", {}),
            "match_explanations": gap_result.get("match_explanations", {}),
            "top_impact_gaps": gap_result.get("top_impact_gaps", []),
            "false_positive_matches": false_positive_matches,
            "non_equivalent_checks": non_equivalent_checks,
        }

    def audit_scoring_properties(self, case: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Phase F: Career match scoring formula properties:

        1. Boundedness: 0 <= score <= 100
        2. Monotonicity: Adding a genuine required skill must increase or preserve score
        3. Neutrality: Adding completely unrelated skills must NOT change the score
        4. Deduplication: Duplicate skills in candidate profile must NOT artificially inflate score
        5. Expected Score Match: Validates calibrated weights against expected benchmark score
        """
        student_skills = case.get("expected_extracted_skills", [])
        target_career = case["target_career"]
        mandatory_skills = case.get("mandatory_skills")
        preferred_skills = case.get("preferred_skills")

        if case.get("job_description"):
            if mandatory_skills is not None or preferred_skills is not None:
                required_skills = (mandatory_skills or []) + (preferred_skills or [])
            else:
                required_skills = case.get("expected_matched_skills", []) + case.get("expected_missing_skills", [])
        else:
            required_skills = get_required_skills(target_career)

        base_res = analyze_skill_gap(
            student_skills=student_skills,
            required_skills=required_skills,
            career=target_career,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
        )
        base_score = base_res["match_percentage"]

        # Property 1: Boundedness
        is_bounded = 0 <= base_score <= 100

        # Property 2: Monotonicity (Add a missing skill)
        missing = base_res["missing_skills"]
        monotonicity_preserved = True
        added_skill_score = base_score
        if missing:
            augmented_skills = student_skills + [missing[0]]
            aug_res = analyze_skill_gap(
                student_skills=augmented_skills,
                required_skills=required_skills,
                career=target_career,
                mandatory_skills=mandatory_skills,
                preferred_skills=preferred_skills,
            )
            added_skill_score = aug_res["match_percentage"]
            monotonicity_preserved = added_skill_score >= base_score

        # Property 3: Neutrality (Add unrelated culinary / random skills)
        unrelated_skills = student_skills + ["Artisanal Pasta Rolling", "Culinary Knife Work", "Wine Tasting"]
        unrelated_res = analyze_skill_gap(
            student_skills=unrelated_skills,
            required_skills=required_skills,
            career=target_career,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
        )
        neutrality_preserved = (unrelated_res["match_percentage"] == base_score)

        # Property 4: Deduplication (Repeat existing skills 5 times)
        duplicated_skills = student_skills * 5
        dup_res = analyze_skill_gap(
            student_skills=duplicated_skills,
            required_skills=required_skills,
            career=target_career,
            mandatory_skills=mandatory_skills,
            preferred_skills=preferred_skills,
        )
        dedup_preserved = (dup_res["match_percentage"] == base_score)

        # Property 5: Expected score calibration (if specified in case)
        expected_score = case.get("expected_score")
        expected_score_matched = True
        if expected_score is not None:
            expected_score_matched = abs(base_score - expected_score) <= 2

        return {
            "case_id": case["id"],
            "base_score": base_score,
            "expected_score": expected_score,
            "expected_score_matched": expected_score_matched,
            "is_bounded": is_bounded,
            "monotonicity_preserved": monotonicity_preserved,
            "neutrality_preserved": neutrality_preserved,
            "deduplication_preserved": dedup_preserved,
            "score_with_added_missing": added_skill_score,
            "scoring_breakdown": base_res.get("scoring_breakdown", {}),
        }

    def evaluate_proficiency_evidence(self, case: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Phase E: Evidence of candidate proficiency from resume text.

        Uses assess_all_skills to assess evidence tier without inventing years or ratings.
        """
        student_skills = case.get("expected_extracted_skills", [])
        resume_text = case.get("resume_text", "")
        level = case.get("proficiency_level", "Unknown")

        assessments = assess_all_skills(skills=student_skills, resume_text=resume_text)

        tier_counts = {
            "professional": 0,
            "internship": 0,
            "project": 0,
            "academic": 0,
            "mentioned": 0,
            "insufficient_evidence": 0,
        }
        for item in assessments:
            t = item.get("evidence_tier", "insufficient_evidence")
            tier_counts[t] = tier_counts.get(t, 0) + 1

        if tier_counts["professional"] > 0:
            detected_classification = "Professional Experience"
        elif tier_counts["internship"] > 0:
            detected_classification = "Internship Experience"
        elif tier_counts["project"] > 0:
            detected_classification = "Project Experience"
        elif tier_counts["academic"] > 0:
            detected_classification = "Academic / Project Knowledge"
        elif tier_counts["mentioned"] > 0:
            detected_classification = "Mentioned / Keyword Listing"
        else:
            detected_classification = "Insufficient Evidence"

        return {
            "case_id": case["id"],
            "expected_level": level,
            "detected_classification": detected_classification,
            "tier_counts": tier_counts,
            "assessments": assessments,
        }

    def evaluate_all(self) -> dict[str, Any]:
        """Execute complete evaluation across all test cases."""
        norm_results = []
        match_results = []
        scoring_results = []
        proficiency_results = []

        total_norm_precision = 0.0
        total_norm_recall = 0.0
        total_norm_f1 = 0.0

        total_match_precision = 0.0
        total_match_recall = 0.0
        total_match_f1 = 0.0

        total_false_positives = 0
        total_scoring_anomalies = 0

        for case in self.cases:
            norm_res = self.evaluate_normalization(case)
            norm_results.append(norm_res)
            total_norm_precision += norm_res["metrics"]["precision"]
            total_norm_recall += norm_res["metrics"]["recall"]
            total_norm_f1 += norm_res["metrics"]["f1"]

            match_res = self.evaluate_skill_matching(case)
            match_results.append(match_res)
            total_match_precision += match_res["match_metrics"]["precision"]
            total_match_recall += match_res["match_metrics"]["recall"]
            total_match_f1 += match_res["match_metrics"]["f1"]
            total_false_positives += len(match_res["false_positive_matches"])

            score_res = self.audit_scoring_properties(case)
            scoring_results.append(score_res)
            if not (
                score_res["is_bounded"]
                and score_res["monotonicity_preserved"]
                and score_res["neutrality_preserved"]
                and score_res["deduplication_preserved"]
                and score_res.get("expected_score_matched", True)
            ):
                total_scoring_anomalies += 1

            prof_res = self.evaluate_proficiency_evidence(case)
            proficiency_results.append(prof_res)

        n = len(self.cases)

        # Aggregate Phase 9 scoring models & proficiency distribution
        scoring_models: dict[str, int] = {}
        for s in scoring_results:
            model = s.get("scoring_breakdown", {}).get("scoring_model", "flat_predefined")
            scoring_models[model] = scoring_models.get(model, 0) + 1

        proficiency_dist: dict[str, int] = {}
        for p in proficiency_results:
            cls_name = p.get("detected_classification", "Unknown")
            proficiency_dist[cls_name] = proficiency_dist.get(cls_name, 0) + 1

        summary = {
            "total_cases": n,
            "normalization_metrics": {
                "mean_precision": round(total_norm_precision / n, 4) if n else 0.0,
                "mean_recall": round(total_norm_recall / n, 4) if n else 0.0,
                "mean_f1": round(total_norm_f1 / n, 4) if n else 0.0,
            },
            "matching_metrics": {
                "mean_precision": round(total_match_precision / n, 4) if n else 0.0,
                "mean_recall": round(total_match_recall / n, 4) if n else 0.0,
                "mean_f1": round(total_match_f1 / n, 4) if n else 0.0,
            },
            "false_positive_count": total_false_positives,
            "scoring_anomalies": total_scoring_anomalies,
            "scoring_properties_verified": total_scoring_anomalies == 0,
            "scoring_models": scoring_models,
            "proficiency_distribution": proficiency_dist,
            "case_evaluations": {
                "normalization": norm_results,
                "matching": match_results,
                "scoring": scoring_results,
                "proficiency": proficiency_results,
            },
        }

        return summary
