
from fastapi import APIRouter, HTTPException

from backend.schemas.career import CareerListResponse, CareerSkillsResponse
from backend.services.career_service import (
    get_career_names,
    get_required_skills,
)

router = APIRouter(prefix="/careers", tags=["Careers"])


@router.get("", response_model=CareerListResponse)
def list_careers() -> CareerListResponse:
    return CareerListResponse(careers=get_career_names())


@router.get("/{career_name}/skills", response_model=CareerSkillsResponse)
def career_skills(career_name: str) -> CareerSkillsResponse:
    try:
        skills = get_required_skills(career_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CareerSkillsResponse(
        career=career_name,
        required_skills=skills,
    )
