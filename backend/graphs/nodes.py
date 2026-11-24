from backend.graphs.state import CareerState
from backend.services.career_service import get_required_skills
from backend.services.jd_service import extract_skills_from_jd
from backend.services.proficiency_service import assess_all_skills
from backend.services.resume_service import analyze_resume_text
from backend.services.semantic_skill_gap_service import analyze_skill_gap
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


def route_skill_source(state: CareerState) -> str:
    """Conditional router: decide whether to extract skills from custom JD or load from catalog."""
    jd = state.get("job_description")
    if jd and isinstance(jd, str) and len(jd.strip()) >= 30:
        return "extract_jd_skills"
    return "load_predefined_skills"


def extract_jd_skills_node(state: CareerState) -> dict:
    """Extract skills dynamically from a user-supplied Job Description."""
    jd_text = state.get("job_description", "")
    analysis = extract_skills_from_jd(jd_text)

    detected_career = analysis.get("job_title") or state.get("selected_career") or "Target Role"

    return {
        "jd_analysis": analysis,
        "required_skills": analysis["required_skills"],
        "mandatory_skills": analysis.get("mandatory_skills", []),
        "preferred_skills": analysis.get("preferred_skills", []),
        "selected_career": detected_career,
    }


def load_predefined_skills_node(state: CareerState) -> dict:
    """Load required skills from the predefined career catalog."""
    career = state.get("selected_career", "")
    required_skills = get_required_skills(career)

    return {
        "required_skills": required_skills,
    }


def analyze_skill_gap_node(state: CareerState) -> dict:
    """Compare candidate skills with the required skills (from either branch)."""
    profile = state.get("profile", {})
    student_skills = profile.get("skills", [])
    required_skills = state.get("required_skills", [])
    career = state.get("selected_career", "")
    mandatory_skills = state.get("mandatory_skills")
    preferred_skills = state.get("preferred_skills")

    result = analyze_skill_gap(
        student_skills=student_skills,
        required_skills=required_skills,
        career=career,
        mandatory_skills=mandatory_skills,
        preferred_skills=preferred_skills,
    )

    proficiency_assessments = assess_all_skills(
        skills=result["matched_skills"],
        resume_text=state.get("resume_text", ""),
        experience_list=profile.get("experience", []),
        projects_list=profile.get("projects", []),
        education_list=profile.get("education", []),
    )

    return {
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "match_percentage": result["match_percentage"],
        "match_explanations": result.get("match_explanations", []),
        "scoring_breakdown": result.get("scoring_breakdown", {}),
        "top_impact_gaps": result.get("top_impact_gaps", []),
        "proficiency_assessments": proficiency_assessments,
    }
