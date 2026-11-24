
from pydantic import BaseModel, Field


class LearningResource(BaseModel):
    """A single learning resource for a skill."""

    title: str = "Resource"
    url: str = "#"
    resource_type: str = "Tutorial"
    is_free: bool = True


class SkillMilestone(BaseModel):
    """One milestone in the learning roadmap, covering a single skill."""

    skill_name: str
    week_label: str = "Week 1 - 2"
    estimated_hours: int = 10
    difficulty: str = "Beginner"
    topics_to_learn: list[str] = Field(default_factory=list)
    completed_topics: list[str] = Field(default_factory=list)
    hands_on_project: str = ""
    resources: list[LearningResource] = Field(default_factory=list)


class RoadmapRequest(BaseModel):
    """Request body for POST /roadmap/generate."""

    career: str
    missing_skills: list[str]
    student_skills: list[str] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    """Response body for POST /roadmap/generate."""

    career: str
    total_estimated_weeks: int
    milestones: list[SkillMilestone] = Field(default_factory=list)


class RoadmapExportRequest(BaseModel):
    """Request body for POST /roadmap/export (the full roadmap to export)."""

    career: str
    total_estimated_weeks: int
    milestones: list[SkillMilestone] = Field(default_factory=list)

