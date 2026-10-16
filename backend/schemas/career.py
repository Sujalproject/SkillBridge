
from pydantic import BaseModel


class CareerListResponse(BaseModel):
    careers: list[str]


class CareerSkillsResponse(BaseModel):
    career: str
    required_skills: list[str]
