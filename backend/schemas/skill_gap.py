
from pydantic import BaseModel


class SkillGapRequest(BaseModel):
    student_skills: list[str]
    career: str


class SkillGapResponse(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: int
