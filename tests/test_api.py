import io
import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "skillbridge-api"}


def test_list_careers_endpoint():
    response = client.get("/careers")
    assert response.status_code == 200
    data = response.json()
    assert "careers" in data
    assert len(data["careers"]) >= 30
    assert "Python Developer" in data["careers"]
    assert "AI Engineer" in data["careers"]


def test_career_skills_endpoint():
    response = client.get("/careers/Python%20Developer/skills")
    assert response.status_code == 200
    data = response.json()
    assert data["career"] == "Python Developer"
    assert "python" in data["required_skills"]
    assert len(data["required_skills"]) > 10


def test_career_skills_unknown():
    response = client.get("/careers/NonExistentCareerRole/skills")
    assert response.status_code == 404


def test_career_agent_analyze_no_file():
    response = client.post("/career-agent/analyze", data={"career": "Python Developer"})
    assert response.status_code == 422


def test_career_agent_analyze_empty_file():
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = client.post("/career-agent/analyze", data={"career": "Python Developer"}, files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_career_agent_analyze_invalid_extension():
    files = {"file": ("test.txt", b"Some regular text file content here.", "text/plain")}
    response = client.post("/career-agent/analyze", data={"career": "Python Developer"}, files=files)
    assert response.status_code == 415
    assert "pdf or docx" in response.json()["detail"].lower()


def test_career_agent_analyze_file_size_exceeded():
    files = {"file": ("large.pdf", b"A" * (5 * 1024 * 1024 + 100), "application/pdf")}
    response = client.post("/career-agent/analyze", data={"career": "Python Developer"}, files=files)
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_career_agent_analyze_no_career_or_jd():
    files = {"file": ("sample.pdf", b"%PDF-1.4 sample content with enough bytes for validation", "application/pdf")}
    response = client.post("/career-agent/analyze", data={"career": "", "job_description": ""}, files=files)
    assert response.status_code == 400
    assert "select a target career or paste a job description" in response.json()["detail"].lower()


def test_roadmap_generate_empty_skills():
    response = client.post("/roadmap/generate", json={"career": "Python Developer", "missing_skills": []})
    assert response.status_code == 200
    data = response.json()
    assert data["career"] == "Python Developer"
    assert data["total_estimated_weeks"] == 0
    assert data["milestones"] == []


def test_groq_model_configuration():
    from backend.core import config
    assert isinstance(config.GROQ_MODEL, str)
    assert len(config.GROQ_MODEL.strip()) > 0
    assert config.ALLOWED_EXTENSIONS == {".pdf", ".docx"}
    assert config.MAX_FILE_BYTES == 5 * 1024 * 1024
