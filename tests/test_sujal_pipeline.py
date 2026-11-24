"""Test suite for validating end-to-end extraction and matching using synthetic candidate fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.resume_parser import extract_resume_text
from backend.services.resume_service import analyze_resume_text
from backend.services.semantic_skill_gap_service import analyze_skill_gap
from backend.services.career_service import get_required_skills
from tests.conftest import make_mock_groq_completion


CANDIDATE_PROFILE_MOCK = {
    "full_name": "Alex Rivera",
    "email": "alex.rivera@example.com",
    "education": ["Bachelor of Science in Computer Science, Tech University"],
    "skills": [
        "Python", "C++", "SQL", "Scikit-learn", "TensorFlow", "Keras",
        "LLMs", "Retrieval-Augmented Generation (RAG)", "AI Agents", "LangChain",
        "LangGraph", "FastAPI", "Pydantic", "SQLAlchemy", "PostgreSQL", "Docker",
        "Git", "GitHub", "REST APIs", "Pinecone", "FAISS", "Prompt Engineering"
    ],
    "projects": ["Career Intelligence Matcher", "RAG Document Search"],
    "experience": ["Backend AI Developer at CloudScale Systems"],
    "certifications": [],
    "target_role": "AI Engineer",
    "summary": "AI Engineer specialized in agentic workflows and retrieval systems.",
}


@pytest.fixture
def candidate_resume_data(sample_pdf_bytes):
    """Load and parse synthetic resume in memory for all tests in this module."""
    text = extract_resume_text("candidate_resume.pdf", sample_pdf_bytes)

    with patch("backend.services.resume_service.Groq") as mock_groq_class, \
         patch("backend.services.resume_service.GROQ_API_KEY", "mock_key"):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_mock_groq_completion(CANDIDATE_PROFILE_MOCK)
        mock_groq_class.return_value = mock_client
        profile = analyze_resume_text(text)

    return {
        "text": text,
        "profile": profile,
    }


def test_resume_text_extraction(candidate_resume_data):
    """Verify raw text extraction captures the resume content properly."""
    text = candidate_resume_data["text"]
    assert len(text) > 100, "Extracted text is too short"
    assert "Alex Rivera" in text, "Candidate name missing from text"
    assert "alex.rivera@example.com" in text.lower(), "Email missing from text"
    assert "LangGraph" in text, "Key technology LangGraph missing from text"


def test_candidate_profile_extraction(candidate_resume_data):
    """Verify candidate metadata and education extraction."""
    profile = candidate_resume_data["profile"]
    assert profile.full_name == "Alex Rivera"
    assert profile.email == "alex.rivera@example.com"
    assert len(profile.education) > 0
    assert "computer science" in profile.education[0].lower()


def test_atomic_skill_extraction_coverage(candidate_resume_data):
    """Audit whether skills are extracted as atomic items with high coverage."""
    profile = candidate_resume_data["profile"]
    extracted_skills = profile.skills

    assert len(extracted_skills) >= 15, (
        f"Expected at least 15 atomic skills extracted, got {len(extracted_skills)}."
    )

    extracted_normalized = {s.strip().lower() for s in extracted_skills}

    # Core must-have skills from the resume
    core_skills = ["python", "sql", "docker", "git", "fastapi", "langgraph", "langchain", "postgresql"]
    matched_core = [c for c in core_skills if any(c in s for s in extracted_normalized)]
    coverage_pct = (len(matched_core) / len(core_skills)) * 100

    assert coverage_pct >= 80.0, f"Core skill coverage too low: {coverage_pct}%"


def test_skill_gap_analysis_against_ai_engineer(candidate_resume_data):
    """Test full pipeline matching against the 'AI Engineer' benchmark role."""
    profile = candidate_resume_data["profile"]
    ai_engineer_skills = get_required_skills("AI Engineer")

    # analyze_skill_gap runs Stage 1 (aliases) and Stage 2 (exact matches) deterministically
    gap_result = analyze_skill_gap(
        student_skills=profile.skills,
        required_skills=ai_engineer_skills,
    )

    matched = gap_result["matched_skills"]
    missing = gap_result["missing_skills"]
    percentage = gap_result["match_percentage"]

    assert percentage > 0, "Match percentage should be greater than 0"
    assert len(matched) > 0, "Candidate should have matched skills for AI Engineer"
    matched_str = " ".join(matched).lower()
    assert "python" in matched_str or "git" in matched_str or "docker" in matched_str
