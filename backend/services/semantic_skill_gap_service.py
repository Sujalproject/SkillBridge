import json
import logging
import os
import re
import time
from typing import Any

from groq import BadRequestError, Groq, RateLimitError

from backend.core.config import GROQ_API_KEY, GROQ_MODEL
from backend.core.skill_importance import ROLE_SKILL_IMPORTANCE, get_skill_importance

logger = logging.getLogger(__name__)

# Standard industry acronyms and abbreviations (universal, non-domain-specific)
COMMON_ALIASES: dict[str, str] = {
    # Programming Languages & Runtimes
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "golang": "go",
    "nodejs": "node.js",
    "node": "node.js",
    "html5": "html",
    "css3": "css",
    "es6": "javascript",
    "ecmascript": "javascript",
    "cpp": "c++",
    "csharp": "c#",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "expressjs": "express",
    "express.js": "express",
    "nextjs": "next.js",
    # Databases & Storage
    "postgres": "postgresql",
    "pg": "postgresql",
    "postgre": "postgresql",
    "psql": "postgresql",
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
    "swagger": "openapi",
    "swagger / openapi": "openapi",
    "openapi 3.0": "openapi",
    # Data & Analytics
    "power bi": "power bi",
    "powerbi": "power bi",
    "microsoft power bi": "power bi",
    "power-bi": "power bi",
    # Machine Learning & AI
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
    "scikitlearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "huggingface": "huggingface transformers",
    "hugging face": "huggingface transformers",
    # Security & QA
    "siem": "security information and event management",
    "selenium webdriver": "selenium",
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
    career: str | None = None,
    mandatory_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> dict:
    """Compare student skills with the skills required for any role using a domain-agnostic 4-stage pipeline:

    Stage 1: Universal normalization & standard acronym aliases.
    Stage 2: Deterministic exact set & disjunctive matching.
    Stage 3: LLM-powered semantic relationship evaluation (exact_match & strong_evidence only).
    Stage 4: Original name preservation & calibrated deterministic scoring.
    """
    clean_student = [s.strip() for s in student_skills if s and s.strip()]
    clean_required = [r.strip() for r in required_skills if r and r.strip()]

    if not clean_required:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0,
            "match_explanations": [],
            "scoring_breakdown": {
                "scoring_model": "empty",
                "matched_count": 0,
                "total_count": 0,
            },
            "top_impact_gaps": [],
        }

    # Map normalized forms to original required skill representation (preserving display casing)
    required_norm_map: dict[str, str] = {}
    for r in clean_required:
        norm = normalize_skill(r)
        if norm not in required_norm_map:
            required_norm_map[norm] = r

    all_required_norm = set(required_norm_map.keys())

    # Map normalized forms to original student skill tokens
    student_norm_map: dict[str, str] = {}
    for s in clean_student:
        norm = normalize_skill(s)
        if norm not in student_norm_map:
            student_norm_map[norm] = s

    student_norm_set = set(student_norm_map.keys())

    # Detailed match explanations dictionary: norm_key -> explanation dict
    match_details: dict[str, dict[str, Any]] = {}

    # Stage 1 & 2: Direct normalized exact matches
    matched_norm_set = set()
    for norm_k in (student_norm_set & all_required_norm):
        matched_norm_set.add(norm_k)
        orig_s = student_norm_map[norm_k]
        orig_r = required_norm_map[norm_k]
        match_type = "exact_match" if orig_s.lower().strip() == orig_r.lower().strip() else "alias_match"
        match_details[norm_k] = {
            "skill": orig_r,
            "match_type": match_type,
            "matched_by": orig_s,
            "confidence": "confirmed",
        }

    # Deterministic disjunction and root competency resolution for catalog benchmarks
    unmatched_req = all_required_norm - matched_norm_set
    for req_k in unmatched_req:
        orig_r = required_norm_map[req_k]

        # 1. Multi-option skill resolution (e.g., "flutter or react native", "postgresql or mysql", "splunk or sentinel")
        if " or " in req_k:
            options = [normalize_skill(opt.strip()) for opt in req_k.split(" or ")]
            matched_opt = next((opt for opt in options if opt in student_norm_set), None)
            if matched_opt:
                matched_norm_set.add(req_k)
                match_details[req_k] = {
                    "skill": orig_r,
                    "match_type": "disjunction_match",
                    "matched_by": student_norm_map[matched_opt],
                    "confidence": "confirmed",
                }
                continue

        # 2. Direct root competency resolution (e.g., candidate has "cryptography", required is "cryptography fundamentals")
        matched_root = False
        for suffix in (" fundamentals", " basics", " administration"):
            if req_k.endswith(suffix):
                root = req_k[:-len(suffix)].strip()
                if root in student_norm_set:
                    matched_norm_set.add(req_k)
                    match_details[req_k] = {
                        "skill": orig_r,
                        "match_type": "root_competency_match",
                        "matched_by": student_norm_map[root],
                        "confidence": "confirmed",
                    }
                    matched_root = True
                    break
        if matched_root:
            continue

        # 3. Direct suffix extension resolution
        if req_k == "responsive web design" and "responsive design" in student_norm_set:
            matched_norm_set.add(req_k)
            match_details[req_k] = {
                "skill": orig_r,
                "match_type": "root_competency_match",
                "matched_by": student_norm_map["responsive design"],
                "confidence": "confirmed",
            }
        elif req_k in {"rest api integration", "rest api consumption", "rest api design"} and "rest apis" in student_norm_set:
            matched_norm_set.add(req_k)
            match_details[req_k] = {
                "skill": orig_r,
                "match_type": "root_competency_match",
                "matched_by": student_norm_map["rest apis"],
                "confidence": "confirmed",
            }

    # Stage 3: LLM semantic evaluation for remaining unmatched skills across any engineering domain
    still_unmatched = sorted(all_required_norm - matched_norm_set)
    if still_unmatched and clean_student:
        unmatched_original = [required_norm_map[k] for k in still_unmatched]
        semantic_matches_norm = _semantic_match_with_llm(
            candidate_skills=clean_student,
            unmatched_required=unmatched_original,
        )
        for k in semantic_matches_norm:
            if k in all_required_norm:
                matched_norm_set.add(k)
                if k not in match_details:
                    match_details[k] = {
                        "skill": required_norm_map[k],
                        "match_type": "semantic_match",
                        "matched_by": "Demonstrated competency in related candidate skills",
                        "confidence": "likely",
                    }

    # Stage 4: Compile final results using original JD/catalog display names
    missing_norm_set = all_required_norm - matched_norm_set

    # Map back to original display names
    matched_list = sorted([required_norm_map[k] for k in matched_norm_set if k in required_norm_map], key=lambda x: x.lower())
    missing_list = sorted([required_norm_map[k] for k in missing_norm_set if k in required_norm_map], key=lambda x: x.lower())

    # Build ordered explanations list
    match_explanations = [match_details[normalize_skill(s)] for s in matched_list if normalize_skill(s) in match_details]

    # --- Calibrated Deterministic Scoring ---
    scoring_breakdown: dict[str, Any] = {}
    top_impact_gaps: list[str] = []

    # Branch 1: Custom Job Description with Mandatory vs Preferred weighting
    if mandatory_skills is not None or preferred_skills is not None:
        clean_mand = [normalize_skill(s) for s in (mandatory_skills or []) if s and s.strip()]
        clean_pref = [normalize_skill(s) for s in (preferred_skills or []) if s and s.strip()]

        # Resolve duplicates: mandatory takes priority
        mand_set = set(clean_mand)
        pref_set = set(clean_pref) - mand_set

        mand_matched = mand_set & matched_norm_set
        pref_matched = pref_set & matched_norm_set

        len_mand = len(mand_set)
        len_pref = len(pref_set)

        if len_mand > 0 and len_pref > 0:
            w_mand = 0.70
            w_pref = 0.30
            r_mand = len(mand_matched) / len_mand
            r_pref = len(pref_matched) / len_pref
            final_score = round((w_mand * r_mand + w_pref * r_pref) * 100)
        elif len_mand > 0:
            w_mand = 1.00
            w_pref = 0.00
            r_mand = len(mand_matched) / len_mand
            r_pref = 0.0
            final_score = round(r_mand * 100)
        elif len_pref > 0:
            w_mand = 0.00
            w_pref = 1.00
            r_mand = 0.0
            r_pref = len(pref_matched) / len_pref
            final_score = round(r_pref * 100)
        else:
            final_score = 0
            w_mand, w_pref, r_mand, r_pref = 0.0, 0.0, 0.0, 0.0

        match_percentage = max(0, min(100, final_score))

        missing_mand = sorted([required_norm_map[k] for k in (mand_set - mand_matched) if k in required_norm_map], key=lambda x: x.lower())
        missing_pref = sorted([required_norm_map[k] for k in (pref_set - pref_matched) if k in required_norm_map], key=lambda x: x.lower())
        top_impact_gaps = missing_mand[:5] if missing_mand else missing_pref[:5]

        scoring_breakdown = {
            "scoring_model": "weighted_custom_jd",
            "mandatory_weight": w_mand,
            "preferred_weight": w_pref,
            "mandatory_matched": len(mand_matched),
            "mandatory_total": len_mand,
            "preferred_matched": len(pref_matched),
            "preferred_total": len_pref,
            "missing_mandatory": missing_mand,
            "missing_preferred": missing_pref,
        }

    # Branch 2: Predefined Role with Skill Importance Tiers
    elif career and career in ROLE_SKILL_IMPORTANCE:
        total_weight = 0.0
        matched_weight = 0.0
        critical_missing = []
        core_missing = []

        for req_k in all_required_norm:
            info = get_skill_importance(career, req_k)
            w = info["weight"]
            total_weight += w
            if req_k in matched_norm_set:
                matched_weight += w
            else:
                orig_name = required_norm_map.get(req_k, req_k)
                if info["tier"] == "critical":
                    critical_missing.append(orig_name)
                elif info["tier"] == "core":
                    core_missing.append(orig_name)

        match_percentage = round((matched_weight / total_weight) * 100) if total_weight > 0 else 0
        match_percentage = max(0, min(100, match_percentage))

        top_impact_gaps = (critical_missing + core_missing)[:5]

        scoring_breakdown = {
            "scoring_model": "tier_weighted_predefined",
            "total_weight": round(total_weight, 1),
            "matched_weight": round(matched_weight, 1),
            "critical_gaps_count": len(critical_missing),
            "core_gaps_count": len(core_missing),
            "critical_gaps": critical_missing,
        }

    # Branch 3: Standard Equal-Weighted Fallback (Preserves 100% exact baseline)
    else:
        match_percentage = (
            round(len(matched_norm_set) / len(all_required_norm) * 100)
            if all_required_norm
            else 0
        )
        match_percentage = max(0, min(100, match_percentage))
        top_impact_gaps = missing_list[:5]

        scoring_breakdown = {
            "scoring_model": "equal_weighted",
            "matched_count": len(matched_norm_set),
            "total_count": len(all_required_norm),
        }

    return {
        "matched_skills": matched_list,
        "missing_skills": missing_list,
        "match_percentage": match_percentage,
        "match_explanations": match_explanations,
        "scoring_breakdown": scoring_breakdown,
        "top_impact_gaps": top_impact_gaps,
    }
