import json
import logging
import os
import re
from typing import Any

from groq import Groq

from backend.core.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Common acronyms, abbreviations, and canonical tech aliases
COMMON_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "pg": "postgresql",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "nodejs": "node.js",
    "node": "node.js",
    "golang": "go",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "azure": "microsoft azure",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "ci/cd": "cicd",
    "rest": "rest api",
    "restful": "rest api",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill for comparison."""
    cleaned = skill.strip().lower()
    return COMMON_ALIASES.get(cleaned, cleaned)


def _token_match(student_norm: str, required_norm: str) -> bool:
    """Check if normalized skills match via substring or token boundary."""
    if student_norm == required_norm:
        return True

    # Check word boundary matching (e.g. 'docker' in 'docker containers')
    pattern_req = r"\b" + re.escape(required_norm) + r"\b"
    pattern_stu = r"\b" + re.escape(student_norm) + r"\b"

    if re.search(pattern_req, student_norm) or re.search(pattern_stu, required_norm):
        return True

    return False


def _semantic_match_with_llm(
    candidate_skills: list[str],
    unmatched_required: list[str],
) -> set[str]:
    """Call Groq to semantically match candidate skills against required skills."""
    if not GROQ_API_KEY or not candidate_skills or not unmatched_required:
        return set()

    try:
        client = Groq(api_key=GROQ_API_KEY)

        system_prompt = (
            "You are an expert technical evaluator. Output valid JSON only."
        )

        user_prompt = (
            f"Candidate Skills: {json.dumps(candidate_skills[:25])}\n"
            f"Required Skills to Check: {json.dumps(unmatched_required[:35])}\n\n"
            "Identify which required skills are semantically satisfied by the candidate's skills.\n"
            "Rules:\n"
            "- A required skill is satisfied if the candidate skill is a direct implementation, synonym, framework, or proves competency in that skill (e.g., 'PostgreSQL' satisfies 'SQL', 'FastAPI' satisfies 'REST APIs', 'AWS EC2' satisfies 'Cloud Computing').\n"
            "- Only pick skills that exist verbatim in the 'Required Skills to Check' list.\n"
            "Output JSON with this exact structure:\n"
            '{"matched_required_skills": ["skill1", "skill2"]}'
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=800,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content
        if not content:
            return set()

        data: dict[str, Any] = json.loads(content)
        matched_from_llm = data.get("matched_required_skills", [])

        # Validate that each returned skill actually exists in the required list
        lookup_map = {normalize_skill(r): normalize_skill(r) for r in unmatched_required}
        matched_norm = set()
        for s in matched_from_llm:
            if isinstance(s, str):
                s_norm = normalize_skill(s)
                if s_norm in lookup_map:
                    matched_norm.add(lookup_map[s_norm])

        return matched_norm

    except Exception as exc:
        logger.warning("LLM semantic skill matching failed, falling back to deterministic matching: %s", exc)
        return set()


def analyze_skill_gap(
    student_skills: list[str],
    required_skills: list[str],
) -> dict:
    """Compare student skills with the skills required for a role using semantic matching.

    1. Normalization & direct set matching.
    2. Token & alias matching.
    3. LLM-powered semantic equivalence evaluation via Groq.
    """
    clean_student = [s.strip() for s in student_skills if s and s.strip()]
    clean_required = [r.strip() for r in required_skills if r and r.strip()]

    if not clean_required:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0,
        }

    # Map normalized forms to original required representation for display
    required_norm_map: dict[str, str] = {
        normalize_skill(r): normalize_skill(r) for r in clean_required
    }
    all_required_norm = set(required_norm_map.keys())

    student_norm_set = {normalize_skill(s) for s in clean_student}

    # Phase 1: Direct & exact normalized matches
    matched_set = student_norm_set & all_required_norm

    # Phase 2: Token / substring / alias matching
    unmatched_required = all_required_norm - matched_set
    for req_norm in list(unmatched_required):
        for stu_norm in student_norm_set:
            if _token_match(stu_norm, req_norm):
                matched_set.add(req_norm)
                break

    # Phase 3: Semantic evaluation with LLM for remaining skills
    still_unmatched = sorted(all_required_norm - matched_set)
    if still_unmatched and clean_student:
        semantic_matches = _semantic_match_with_llm(
            candidate_skills=clean_student,
            unmatched_required=still_unmatched,
        )
        matched_set.update(semantic_matches)

    # Compile final results
    missing_set = all_required_norm - matched_set

    matched_list = sorted(matched_set)
    missing_list = sorted(missing_set)

    match_percentage = (
        round(len(matched_list) / len(all_required_norm) * 100)
        if all_required_norm
        else 0
    )

    return {
        "matched_skills": matched_list,
        "missing_skills": missing_list,
        "match_percentage": match_percentage,
    }
