
from backend.graphs.state import CareerState
from backend.services.career_service import get_required_skills
from backend.services.resume_service import analyze_resume_text
from backend.services.skill_gap_service import analyze_skill_gap
from backend.utils.resume_parser import extract_resume_text


def extract_resume_node(state: CareerState) -> dict:
    """Extract text from the uploaded resume."""
    resume_text = extract_resume_text(
        state["filename"],
        state["file_content"],
    )

    if len(resume_text.strip()) < 40:
        raise ValueError(
            "Very little text was found in the resume. "
            "The PDF may be scanned or contain no readable text."
        )

    return {"resume_text": resume_text}

def analyze_resume_node(state: CareerState) -> dict:
    """Analyze extracted resume text and save the candidate profile."""
    profile = analyze_resume_text(state["resume_text"])

    return {
        "profile": profile.model_dump(mode="json"),
    }


def analyze_skill_gap_node(state: CareerState) -> dict:
    """Compare the candidate's skills with the selected career."""
    profile = state["profile"]
    career = state["selected_career"]

    required_skills = get_required_skills(career)
    student_skills = profile.get("skills", [])

    result = analyze_skill_gap(
        student_skills=student_skills,
        required_skills=required_skills,
    )

    return {
        "required_skills": required_skills,
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "match_percentage": result["match_percentage"],
    }
