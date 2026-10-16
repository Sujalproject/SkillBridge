from pydantic import BaseModel, Field


class CareerProfile(BaseModel):
    full_name: str | None = None
    email: str | None = None
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    target_role: str | None = None
    summary: str | None = ""


class ResumeAnalysisResponse(BaseModel):
    filename: str
    extracted_characters: int
    profile: CareerProfile
    note: str