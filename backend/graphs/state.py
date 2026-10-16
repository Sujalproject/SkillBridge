
from typing import NotRequired, TypedDict


class CareerState(TypedDict):
    """Shared information passed between SkillBridge graph nodes."""

    # Inputs to the career-planning workflow
    resume_text: NotRequired[str]
    selected_career: str
    filename: str
    file_content: bytes

    # Produced by resume analysis
    profile: NotRequired[dict]

    # Produced by skill-gap analysis
    required_skills: NotRequired[list[str]]
    matched_skills: NotRequired[list[str]]
    missing_skills: NotRequired[list[str]]
    match_percentage: NotRequired[int]

    # Produced by roadmap planning and validation
    learning_priorities: NotRequired[list[str]]
    roadmap: NotRequired[dict]
    validation_errors: NotRequired[list[str]]
   
