import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.graphs.career_graph import career_graph
from backend.services.jd_service import extract_skills_from_jd
from tests.conftest import make_mock_groq_completion

SAMPLE_JD = """
Job Title: Senior GenAI / LLM Engineer
Company: CloudScale AI
Location: Remote

About the Role:
We are seeking an experienced AI Engineer to design and scale our agentic systems and RAG infrastructure.

Mandatory Requirements:
- 3+ years of Python programming.
- Deep expertise in LLMs, LangGraph or LangChain, and Prompt Engineering.
- Hands-on experience with Retrieval-Augmented Generation (RAG) and Vector Databases (Pinecone, FAISS, or Qdrant).
- Experience building and deploying REST APIs with FastAPI.
- Proficiency in Docker and Git version control.

Preferred Qualifications:
- Experience with PyTorch or Hugging Face Transformers.
- Knowledge of Kubernetes and Cloud platforms (AWS or GCP).
- Experience with LLM observability tools like LangSmith.
"""

MOCK_JD_PARSED = {
    "job_title": "Senior GenAI / LLM Engineer",
    "seniority_level": "Senior",
    "mandatory_skills": ["Python", "FastAPI", "Docker", "Git", "RAG", "LangGraph", "Vector Databases"],
    "preferred_skills": ["Kubernetes", "PyTorch", "AWS", "LangSmith"],
    "summary": "Senior AI Engineer to lead agentic workflows and RAG infrastructure.",
}

MOCK_RESUME_PARSED = {
    "full_name": "Alex Rivera",
    "email": "alex.rivera@example.com",
    "education": ["BS in Computer Science"],
    "skills": ["Python", "SQL", "Docker", "Git", "FastAPI", "LangGraph", "PostgreSQL"],
    "projects": ["Career Agent", "RAG Search Engine"],
    "experience": ["Backend AI Developer at CloudScale Systems"],
    "certifications": [],
    "target_role": "AI Engineer",
    "summary": "Passionate AI Developer building agentic workflows.",
}


@patch("backend.services.jd_service.Groq")
def test_jd_service_extraction(mock_groq_class):
    """Verify that extract_skills_from_jd accurately parses title and atomic skills with mocked Groq."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_mock_groq_completion(MOCK_JD_PARSED)
    mock_groq_class.return_value = mock_client

    with patch("backend.services.jd_service.GROQ_API_KEY", "mock_key"):
        analysis = extract_skills_from_jd(SAMPLE_JD)

    assert analysis["job_title"] == "Senior GenAI / LLM Engineer"
    assert analysis["seniority_level"] == "Senior"
    assert "required_skills" in analysis
    assert len(analysis["required_skills"]) >= 5

    skills_lower = [s.lower() for s in analysis["required_skills"]]
    assert any("python" in s for s in skills_lower)
    assert any("fastapi" in s for s in skills_lower)
    assert any("docker" in s for s in skills_lower)
    assert any("rag" in s for s in skills_lower)


@patch("backend.services.semantic_skill_gap_service._semantic_match_with_llm", return_value={"retrieval-augmented generation", "langgraph"})
@patch("backend.services.jd_service.Groq")
@patch("backend.services.resume_service.Groq")
def test_career_graph_with_jd_branch(mock_resume_groq, mock_jd_groq, mock_semantic_match, sample_pdf_bytes):
    """Verify that career_graph routes to extract_jd_skills when job_description is provided."""
    # Mock resume extraction
    mock_res_client = MagicMock()
    mock_res_client.chat.completions.create.return_value = make_mock_groq_completion(MOCK_RESUME_PARSED)
    mock_resume_groq.return_value = mock_res_client

    # Mock JD extraction
    mock_jd_client = MagicMock()
    mock_jd_client.chat.completions.create.return_value = make_mock_groq_completion(MOCK_JD_PARSED)
    mock_jd_groq.return_value = mock_jd_client

    with patch("backend.services.resume_service.GROQ_API_KEY", "mock_key"), \
         patch("backend.services.jd_service.GROQ_API_KEY", "mock_key"):
        result = career_graph.invoke(
            {
                "filename": "alex_rivera_resume.pdf",
                "file_content": sample_pdf_bytes,
                "selected_career": "",
                "job_description": SAMPLE_JD,
            }
        )

    assert "jd_analysis" in result
    assert result["jd_analysis"] is not None
    assert result["jd_analysis"]["job_title"] == "Senior GenAI / LLM Engineer"
    assert len(result["required_skills"]) > 0
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert result["match_percentage"] > 0


@patch("backend.services.semantic_skill_gap_service._semantic_match_with_llm", return_value=set())
@patch("backend.services.resume_service.Groq")
def test_career_graph_without_jd_branch(mock_resume_groq, mock_semantic_match, sample_pdf_bytes):
    """Verify that career_graph routes to load_predefined_skills when job_description is None."""
    mock_res_client = MagicMock()
    mock_res_client.chat.completions.create.return_value = make_mock_groq_completion(MOCK_RESUME_PARSED)
    mock_resume_groq.return_value = mock_res_client

    with patch("backend.services.resume_service.GROQ_API_KEY", "mock_key"):
        result = career_graph.invoke(
            {
                "filename": "alex_rivera_resume.pdf",
                "file_content": sample_pdf_bytes,
                "selected_career": "Python Developer",
                "job_description": None,
            }
        )

    assert result.get("jd_analysis") is None
    assert len(result["required_skills"]) > 0
    assert "python" in [s.lower() for s in result["required_skills"]]
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert result["match_percentage"] > 0
