
from typing import NotRequired, TypedDict


class CareerState(TypedDict):
    """Shared information passed between SkillBridge graph nodes."""

    # Inputs to the career-planning workflow
    resume_text: NotRequired[str]
    selected_career: str
    filename: str
    file_content: bytes
    job_description: NotRequired[str | None]

    # Produced by job description analysis (if JD provided)
    jd_analysis: NotRequired[dict]
    mandatory_skills: NotRequired[list[str]]
    preferred_skills: NotRequired[list[str]]

    # Produced by resume analysis
    profile: NotRequired[dict]

    # Produced by skill-gap analysis
    required_skills: NotRequired[list[str]]
    matched_skills: NotRequired[list[str]]
    missing_skills: NotRequired[list[str]]
    match_percentage: NotRequired[int]
    match_explanations: NotRequired[list[dict]]
    scoring_breakdown: NotRequired[dict]
    top_impact_gaps: NotRequired[list[str]]
    proficiency_assessments: NotRequired[list[dict]]

    # Produced by roadmap planning and validation
    learning_priorities: NotRequired[list[str]]
    roadmap: NotRequired[dict]
    validation_errors: NotRequired[list[str]]
   
