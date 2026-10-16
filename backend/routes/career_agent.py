
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.core.config import ALLOWED_EXTENSIONS, MAX_FILE_BYTES
from backend.graphs.career_graph import career_graph

router = APIRouter(prefix="/career-agent", tags=["Career Agent"])


@router.post("/analyze")
async def analyze_career(
    career: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    filename = file.filename or "resume"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Upload a PDF or DOCX file.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum size is 5 MB.",
        )

    try:
        result = career_graph.invoke(
            {
                "filename": filename,
                "file_content": content,
                "selected_career": career,
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Career analysis failed. Check the backend logs.",
        ) from exc

    return {
        "filename": filename,
        "career": career,
        "profile": result["profile"],
        "required_skills": result["required_skills"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "match_percentage": result["match_percentage"],
    }
