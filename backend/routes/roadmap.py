
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.roadmap import (
    RoadmapExportRequest,
    RoadmapRequest,
    RoadmapResponse,
)
from backend.services.roadmap_service import generate_roadmap
from backend.utils.excel_exporter import generate_roadmap_excel

router = APIRouter(prefix="/roadmap", tags=["Learning Roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
def generate_roadmap_endpoint(request: RoadmapRequest) -> RoadmapResponse:
    """Generate a personalized learning roadmap for the missing skills."""
    if not request.missing_skills:
        return RoadmapResponse(
            career=request.career,
            total_estimated_weeks=0,
            milestones=[],
        )

    try:
        roadmap = generate_roadmap(
            career=request.career,
            missing_skills=request.missing_skills,
            student_skills=request.student_skills,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Roadmap generation failed: {type(exc).__name__}",
        ) from exc

    return roadmap


@router.post("/export")
def export_roadmap_excel(request: RoadmapExportRequest) -> StreamingResponse:
    """Export the learning roadmap as a styled Excel (.xlsx) file."""
    try:
        excel_buffer = generate_roadmap_excel(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Excel generation failed: {type(exc).__name__}",
        ) from exc

    career_slug = request.career.replace(" ", "_")
    filename = f"{career_slug}_Learning_Roadmap.xlsx"

    return StreamingResponse(
        excel_buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

