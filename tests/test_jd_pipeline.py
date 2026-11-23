import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.graphs.career_graph import career_graph
from backend.services.jd_service import extract_skills_from_jd


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

SAMPLE_RESUME_BYTES = b"%PDF-1.4 Mock resume content for testing purposes"


def test_jd_service_extraction():
    """Verify that extract_skills_from_jd accurately parses title and atomic skills."""
    analysis = extract_skills_from_jd(SAMPLE_JD)

    assert "job_title" in analysis
    assert "seniority_level" in analysis
    assert "required_skills" in analysis
    assert len(analysis["required_skills"]) >= 5

    skills_lower = [s.lower() for s in analysis["required_skills"]]
    assert any("python" in s for s in skills_lower)
    assert any("fastapi" in s for s in skills_lower)
    assert any("docker" in s for s in skills_lower)
    assert any("rag" in s or "retrieval" in s for s in skills_lower)


def test_career_graph_with_jd_branch():
    """Verify that career_graph routes to extract_jd_skills when job_description is provided."""
    # Mock text parser to return predictable candidate skills for the graph
    resume_file = Path("Sujal_Kumar_Patwa_Resume.pdf")
    if not resume_file.exists():
        pytest.skip("Sujal_Kumar_Patwa_Resume.pdf not available for graph test")

    result = career_graph.invoke(
        {
            "filename": resume_file.name,
            "file_content": resume_file.read_bytes(),
            "selected_career": "",
            "job_description": SAMPLE_JD,
        }
    )

    assert "jd_analysis" in result
    assert result["jd_analysis"] is not None
    assert len(result["required_skills"]) > 0
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert result["match_percentage"] > 0
    print(f"\nJD Branch Match %: {result['match_percentage']}%")
    print(f"Matched ({len(result['matched_skills'])}): {result['matched_skills']}")


def test_career_graph_without_jd_branch():
    """Verify that career_graph routes to load_predefined_skills when job_description is None."""
    resume_file = Path("Sujal_Kumar_Patwa_Resume.pdf")
    if not resume_file.exists():
        pytest.skip("Sujal_Kumar_Patwa_Resume.pdf not available for graph test")

    result = career_graph.invoke(
        {
            "filename": resume_file.name,
            "file_content": resume_file.read_bytes(),
            "selected_career": "Python Developer",
            "job_description": None,
        }
    )

    # When no JD is provided, jd_analysis should be absent or None
    assert result.get("jd_analysis") is None
    assert len(result["required_skills"]) > 0
    assert "matched_skills" in result
    assert "missing_skills" in result
    print(f"\nCatalog Branch Match %: {result['match_percentage']}%")
