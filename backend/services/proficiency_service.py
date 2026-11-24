"""Evidence-based candidate proficiency assessment.

Evaluates resume evidence without inventing years of experience or arbitrary ratings.
Qualitative states:
- confirmed: Supported by direct professional employment or project implementation evidence.
- likely: Supported by academic coursework or technical skills inventory listing.
- insufficient_evidence: Minimal or unverifiable context.
"""

import re
from typing import Any


def assess_skill_proficiency(
    skill: str,
    resume_text: str,
    experience_list: list[str] | None = None,
    projects_list: list[str] | None = None,
    education_list: list[str] | None = None,
) -> dict[str, Any]:
    """Assess candidate evidence tier and qualitative confidence for an individual skill."""
    skill_clean = skill.strip()
    skill_norm = skill_clean.lower()
    skill_pattern = re.compile(rf"\b{re.escape(skill_norm)}\b", re.IGNORECASE)

    experience_list = experience_list or []
    projects_list = projects_list or []
    education_list = education_list or []

    # 1. Check Professional Employment History
    for exp in experience_list:
        if skill_pattern.search(exp):
            return {
                "skill": skill_clean,
                "evidence_tier": "professional",
                "confidence": "confirmed",
                "supporting_evidence": exp.strip()[:140],
            }

    # 2. Check Personal / Practical Projects
    for proj in projects_list:
        if skill_pattern.search(proj):
            return {
                "skill": skill_clean,
                "evidence_tier": "project",
                "confidence": "confirmed",
                "supporting_evidence": proj.strip()[:140],
            }

    # 3. Check Internship mentions in raw text
    text_lower = resume_text.lower()
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    for line in lines:
        if "intern" in line.lower() and skill_pattern.search(line):
            return {
                "skill": skill_clean,
                "evidence_tier": "internship",
                "confidence": "confirmed",
                "supporting_evidence": line[:140],
            }

    # 4. Check Academic Coursework & Education
    for edu in education_list:
        if skill_pattern.search(edu):
            return {
                "skill": skill_clean,
                "evidence_tier": "academic",
                "confidence": "likely",
                "supporting_evidence": edu.strip()[:140],
            }

    # 5. Check if present in raw text lines containing project or work context
    for line in lines:
        if skill_pattern.search(line):
            line_l = line.lower()
            if any(k in line_l for k in ["built", "developed", "implemented", "managed", "deployed", "scaled", "trained"]):
                return {
                    "skill": skill_clean,
                    "evidence_tier": "project",
                    "confidence": "confirmed",
                    "supporting_evidence": line[:140],
                }

    # 6. Mentioned in skills list only
    if skill_pattern.search(resume_text):
        return {
            "skill": skill_clean,
            "evidence_tier": "mentioned",
            "confidence": "likely",
            "supporting_evidence": "Listed in candidate skills inventory without narrative description.",
        }

    # 7. Insufficient Evidence
    return {
        "skill": skill_clean,
        "evidence_tier": "insufficient_evidence",
        "confidence": "insufficient_evidence",
        "supporting_evidence": "No direct contextual evidence found in resume text.",
    }


def assess_all_skills(
    skills: list[str],
    resume_text: str,
    experience_list: list[str] | None = None,
    projects_list: list[str] | None = None,
    education_list: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Assess proficiency and supporting evidence across all matched candidate skills."""
    return [
        assess_skill_proficiency(
            skill=s,
            resume_text=resume_text,
            experience_list=experience_list,
            projects_list=projects_list,
            education_list=education_list,
        )
        for s in skills
    ]
