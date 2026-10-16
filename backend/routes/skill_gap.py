
from fastapi import APIRouter, HTTPException

from backend.schemas.skill_gap import SkillGapRequest, SkillGapResponse
from backend.services.career_service import get_required_skills
from backend.services.skill_gap_service import analyze_skill_gap

router = APIRouter(prefix="/skills", tags=["Skill Gap Analysis"])


@router.post("/analyze", response_model=SkillGapResponse)
def skill_gap_endpoint(request: SkillGapRequest) -> SkillGapResponse:
    try:
        required_skills = get_required_skills(request.career)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = analyze_skill_gap(
        student_skills=request.student_skills,
        required_skills=required_skills,
    )

    return SkillGapResponse(**result)
