import json
import logging
import os
import re
import time
from typing import Any

from groq import BadRequestError, Groq, RateLimitError

from backend.core.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Standard industry acronyms and abbreviations (universal, non-domain-specific)
COMMON_ALIASES: dict[str, str] = {
    # Programming Languages & Runtimes
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "nodejs": "node.js",
    "node": "node.js",
    # Databases & Storage
    "postgres": "postgresql",
    "pg": "postgresql",
    "mongo": "mongodb",
    # Cloud Platforms
    "aws": "amazon web services",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "azure": "microsoft azure",
    # Infrastructure & DevOps
    "k8s": "kubernetes",
    "ci/cd": "cicd",
    "ci cd": "cicd",
    "continuous integration": "cicd",
    "continuous deployment": "cicd",
    # Web & APIs
    "rest": "rest apis",
    "restful": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "rest api development": "rest apis",
    "rest api design": "rest apis",
    # General AI / ML Acronyms
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "llm": "large language models",
    "llms": "large language models",
    "large language model": "large language models",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "rag": "retrieval-augmented generation",
    "retrieval augmented generation": "retrieval-augmented generation",
    # Version Control
    "git / github": "git",
    "github or gitlab": "git",
    "github": "git",
    "gitlab": "git",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill for comparison using standard aliases and character cleanup."""
    cleaned = skill.strip().lower()
    cleaned = re.sub(r"^[\"'\(\[]+|[\"'\)\]]+$", "", cleaned).strip()
    return COMMON_ALIASES.get(cleaned, cleaned)


def _semantic_match_with_llm(
    candidate_skills: list[str],
    unmatched_required: list[str],
) -> set[str]:
    """Call Groq to evaluate whether candidate skills demonstrate required skills using domain-agnostic relationship criteria."""
    if not GROQ_API_KEY or not candidate_skills or not unmatched_required:
        return set()

    client = Groq(api_key=GROQ_API_KEY)
    matched_skills = set()
    clean_candidate = candidate_skills[:45]

    # Batch unmatched required skills in groups of 25 to avoid token limits & truncation
    batch_size = 25
    batches = [
        unmatched_required[i : i + batch_size]
        for i in range(0, len(unmatched_required), batch_size)
    ]

    for batch in batches:
        system_prompt = (
            "You are an expert technical evaluator across all software engineering, data, cloud, and AI domains. "
            "Output valid JSON only."
        )

        user_prompt = f"""Candidate Skills:
{json.dumps(clean_candidate)}

Required Skills:
{json.dumps(batch)}

Your task is to evaluate whether the candidate demonstrates each required skill based on their listed resume skills.

RULES:
1. Exact matches and standard technical synonyms/acronyms are matches (e.g. "K8s" is "Kubernetes", "LLM" is "Large Language Models").
2. A specific tool, framework, or technology demonstrates a broader competency or concept when it provides direct evidence of that ability across any engineering domain (e.g., "Docker" demonstrates "Containerization", "React" demonstrates "Frontend Frameworks", "PostgreSQL" demonstrates "SQL" or "Relational Databases", "Terraform" demonstrates "Infrastructure as Code", "Pinecone" demonstrates "Vector Databases", "Pytest" demonstrates "Unit Testing").
3. Do not assume that knowing a broad framework implies proficiency in every distinct, unrelated technology or concept.
4. Distinguish between:
   - exact_match
   - strong_evidence
   - related_but_insufficient
   - no_evidence
5. Only exact_match and strong_evidence count as matched skills.
6. Evaluate every required skill independently.

Return JSON using this exact structure:
{{
    "evaluations": [
        {{
            "required_skill": "<exact skill name from Required Skills>",
            "candidate_evidence": ["<candidate skill>"],
            "relationship": "exact_match",
            "is_matched": true,
            "reason": "<short justification>"
        }}
    ]
}}
Return only valid JSON."""

        content: str | None = None
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
        except RateLimitError as rate_err:
            logger.warning("Groq rate limit during semantic matching: %s. Retrying in 3.5s...", rate_err)
            time.sleep(3.5)
            try:
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=1500,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = completion.choices[0].message.content
            except Exception as retry_err:
                logger.warning("Retry failed during semantic matching: %s", retry_err)
                continue
        except BadRequestError as bad_req:
            logger.info("Retrying semantic matching without json_object mode: %s", bad_req)
            try:
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=1500,
                    messages=[
                        {"role": "system", "content": system_prompt + " Output raw JSON only."},
                        {"role": "user", "content": user_prompt + " Output JSON:"},
                    ],
                )
                content = completion.choices[0].message.content
            except Exception as retry_err:
                logger.warning("Standard mode retry failed: %s", retry_err)
                continue
        except Exception as exc:
            logger.warning("LLM semantic skill matching call failed: %s", exc)
            continue

        if not content or not content.strip():
            continue

        # Parse JSON robustly
        cleaned_text = content.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

        match = re.search(r"\{[\s\S]*\}", cleaned_text)
        try:
            data = json.loads(match.group(0)) if match else json.loads(cleaned_text)
        except Exception as json_err:
            logger.warning("Failed to parse LLM evaluation JSON: %s", json_err)
            continue

        evaluations = data.get("evaluations", [])
        batch_lookup = {normalize_skill(r): normalize_skill(r) for r in batch}

        for ev in evaluations:
            if not isinstance(ev, dict):
                continue
            is_matched = ev.get("is_matched", False)
            relationship = str(ev.get("relationship", "")).lower()
            if is_matched or relationship in {"exact_match", "strong_evidence"}:
                req_skill = ev.get("required_skill", "")
                if isinstance(req_skill, str):
                    req_norm = normalize_skill(req_skill)
                    if req_norm in batch_lookup:
                        matched_skills.add(batch_lookup[req_norm])

    return matched_skills


def analyze_skill_gap(
    student_skills: list[str],
    required_skills: list[str],
) -> dict:
    """Compare student skills with the skills required for any role using a domain-agnostic 3-stage pipeline:

    Stage 1: Universal normalization & standard acronym aliases.
    Stage 2: Deterministic exact set matching.
    Stage 3: LLM-powered semantic relationship evaluation (exact_match & strong_evidence only).
    Stage 4: Original name preservation for accurate frontend presentation.
    """
    clean_student = [s.strip() for s in student_skills if s and s.strip()]
    clean_required = [r.strip() for r in required_skills if r and r.strip()]

    if not clean_required:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0,
        }

    # Map normalized forms to original required skill representation (preserving display casing)
    required_norm_map: dict[str, str] = {}
    for r in clean_required:
        norm = normalize_skill(r)
        if norm not in required_norm_map:
            required_norm_map[norm] = r

    all_required_norm = set(required_norm_map.keys())
    student_norm_set = {normalize_skill(s) for s in clean_student}

    # Stage 1 & 2: Direct normalized exact matches
    matched_norm_set = student_norm_set & all_required_norm

    # Stage 3: LLM semantic evaluation for remaining unmatched skills across any engineering domain
    still_unmatched = sorted(all_required_norm - matched_norm_set)
    if still_unmatched and clean_student:
        unmatched_original = [required_norm_map[k] for k in still_unmatched]
        semantic_matches_norm = _semantic_match_with_llm(
            candidate_skills=clean_student,
            unmatched_required=unmatched_original,
        )
        matched_norm_set.update(semantic_matches_norm)

    # Stage 4: Compile final results using original JD/catalog display names
    missing_norm_set = all_required_norm - matched_norm_set

    # Map back to original display names
    matched_list = sorted([required_norm_map[k] for k in matched_norm_set], key=lambda x: x.lower())
    missing_list = sorted([required_norm_map[k] for k in missing_norm_set], key=lambda x: x.lower())

    match_percentage = (
        round(len(matched_norm_set) / len(all_required_norm) * 100)
        if all_required_norm
        else 0
    )

    return {
        "matched_skills": matched_list,
        "missing_skills": missing_list,
        "match_percentage": match_percentage,
    }
