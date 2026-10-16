
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import ALLOWED_EXTENSIONS, MAX_FILE_BYTES
from backend.schemas.resume import ResumeAnalysisResponse
from backend.services.resume_service import analyze_resume_text
from backend.utils.resume_parser import extract_resume_text

router = APIRouter(prefix="/resume", tags=["Resume Analysis"])


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
) -> ResumeAnalysisResponse:
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
        resume_text = extract_resume_text(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(resume_text.strip()) < 40:
        raise HTTPException(
            status_code=422,
            detail=(
                "Very little text was found. This may be a scanned PDF; "
                "OCR support is not included yet."
            ),
        )

    profile = analyze_resume_text(resume_text)

    return ResumeAnalysisResponse(
        filename=filename,
        extracted_characters=len(resume_text),
        profile=profile,
        note=(
            "Review the extracted information for accuracy before "
            "using it for career decisions."
        ),
    )
