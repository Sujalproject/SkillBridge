"""Test suite for validating end-to-end extraction on Sujal Kumar's actual resume."""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.resume_parser import extract_resume_text
from backend.services.resume_service import analyze_resume_text
from backend.services.semantic_skill_gap_service import analyze_skill_gap
from backend.services.career_service import get_required_skills


RESUME_PATH = Path(__file__).resolve().parents[1] / "Sujal_Kumar_Patwa_Resume.pdf"

# Ground-truth technical skills explicitly stated in Sujal Kumar's resume
EXPECTED_RESUME_SKILLS = [
    # Programming Languages
    "Python", "C++", "SQL",
    # ML & Deep Learning
    "Scikit-learn", "TensorFlow", "Keras", "Feature Engineering", "Model Evaluation", "CNNs",
    # AI / GenAI
    "LLMs", "Retrieval-Augmented Generation (RAG)", "AI Agents", "Agentic Workflows",
    "Prompt Engineering", "Tool Calling", "Hugging Face", "Embeddings", "Semantic Search",
    "Query Rewriting", "LLM Guardrails", "MCP", "Reranking",
    # Frameworks & Libraries
    "LangChain", "LangGraph", "FastAPI", "Streamlit", "Pydantic", "SQLAlchemy",
    # Vector Search & Databases
    "FAISS", "Pinecone", "PostgreSQL", "MySQL", "SQLite",
    # APIs & Tools
    "REST APIs", "Groq API", "Google Gemini API", "Postman", "Git", "GitHub", "Docker", "LangSmith"
]


@pytest.fixture(scope="module")
def sujal_resume_data():
    """Load and parse the resume once for all tests in this module."""
    if not RESUME_PATH.exists():
        pytest.skip(f"Resume file not found at {RESUME_PATH}")
    
    content = RESUME_PATH.read_bytes()
    text = extract_resume_text(RESUME_PATH.name, content)
    profile = analyze_resume_text(text)
    return {
        "text": text,
        "profile": profile,
    }


def test_resume_text_extraction(sujal_resume_data):
    """Verify raw text extraction captures the resume content properly."""
    text = sujal_resume_data["text"]
    assert len(text) > 800, "Extracted text is too short"
    assert "SUJAL KUMAR" in text.upper(), "Candidate name missing from text"
    assert "sujalkumarpatwa1@gmail.com" in text.lower(), "Email missing from text"
    assert "Bennett University" in text, "University name missing from text"
    assert "LangGraph" in text, "Key technology LangGraph missing from text"


def test_candidate_profile_extraction(sujal_resume_data):
    """Verify candidate metadata and education extraction."""
    profile = sujal_resume_data["profile"]
    assert profile.full_name is not None
    assert "sujal" in profile.full_name.lower()

    assert profile.email is not None
    assert "sujalkumarpatwa1@gmail.com" in profile.email.lower()

    # Education verification
    assert len(profile.education) > 0
    edu_text = " ".join(profile.education).lower()
    assert "bennett" in edu_text or "computer science" in edu_text


def test_atomic_skill_extraction_coverage(sujal_resume_data):
    """Audit whether skills are extracted as atomic items with high coverage."""
    profile = sujal_resume_data["profile"]
    extracted_skills = profile.skills

    print(f"\nTotal extracted skills count: {len(extracted_skills)}")
    assert len(extracted_skills) >= 20, (
        f"Expected at least 20 atomic skills extracted, got {len(extracted_skills)}. "
        "Check that skills are not grouped into comma-separated lines."
    )

    extracted_normalized = {s.strip().lower() for s in extracted_skills}

    # Core must-have skills from the resume
    core_skills = [
        "python", "sql", "docker", "git", "fastapi", "langgraph",
        "langchain", "postgresql", "scikit-learn", "tensorflow"
    ]

    matched_core = [c for c in core_skills if any(c in s for s in extracted_normalized)]
    coverage_pct = (len(matched_core) / len(core_skills)) * 100

    print(f"Core skills matched: {matched_core}")
    print(f"Core skill coverage: {coverage_pct:.1f}%")

    assert coverage_pct >= 80.0, f"Core skill coverage too low: {coverage_pct}%"


def test_skill_gap_analysis_against_ai_engineer(sujal_resume_data):
    """Test full pipeline matching against the 'AI Engineer' benchmark role."""
    profile = sujal_resume_data["profile"]
    ai_engineer_skills = get_required_skills("AI Engineer")

    gap_result = analyze_skill_gap(
        student_skills=profile.skills,
        required_skills=ai_engineer_skills,
    )

    matched = gap_result["matched_skills"]
    missing = gap_result["missing_skills"]
    percentage = gap_result["match_percentage"]

    print(f"\n--- AI Engineer Role Matching for Sujal Kumar ---")
    print(f"Match Percentage: {percentage}%")
    print(f"Matched Skills ({len(matched)}): {matched}")
    print(f"Missing Skills ({len(missing)}): {missing[:8]}... ({len(missing)} total)")

    assert percentage > 0, "Match percentage should be greater than 0"
    assert len(matched) > 0, "Candidate should have matched skills for AI Engineer"
    
    # Sujal definitely possesses these key skills for an AI Engineer
    matched_str = " ".join(matched).lower()
    assert "python" in matched_str or "git" in matched_str or "docker" in matched_str
