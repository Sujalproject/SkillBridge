import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas.roadmap import RoadmapResponse
from backend.services.roadmap_service import _search_resources_for_skill, generate_roadmap
from tests.conftest import make_mock_groq_completion

MOCK_ROADMAP_JSON = {
    "career": "Python Developer",
    "total_estimated_weeks": 4,
    "milestones": [
        {
            "skill_name": "Docker",
            "week_label": "Week 1 - 2",
            "estimated_hours": 12,
            "difficulty": "Beginner",
            "topics_to_learn": ["Containers", "Images", "Docker Compose"],
            "hands_on_project": "Containerize a FastAPI service",
            "resources": [
                {
                    "title": "Docker Getting Started",
                    "url": "https://docs.docker.com/get-started/",
                    "resource_type": "Documentation",
                    "is_free": True,
                }
            ],
        }
    ],
}


def test_roadmap_empty_missing_skills():
    roadmap = generate_roadmap("Python Developer", [])
    assert roadmap.total_estimated_weeks == 0
    assert roadmap.milestones == []


@patch("backend.services.roadmap_service.TavilyClient")
def test_tavily_search_resources(mock_tavily_class):
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"title": "Docker Tutorial", "url": "https://example.com/docker"},
            {"title": "FastAPI Guide", "url": "https://example.com/fastapi"},
        ]
    }
    mock_tavily_class.return_value = mock_client

    with patch("backend.services.roadmap_service.TAVILY_API_KEY", "mock_key"):
        results = _search_resources_for_skill("Docker", "Python Developer")

    assert len(results) == 2
    assert results[0]["title"] == "Docker Tutorial"
    assert results[0]["url"] == "https://example.com/docker"


@patch("backend.services.roadmap_service.TavilyClient")
@patch("backend.services.roadmap_service.Groq")
def test_generate_roadmap_with_mocked_llm(mock_groq_class, mock_tavily_class):
    mock_tavily = MagicMock()
    mock_tavily.search.return_value = {"results": [{"title": "Docker Docs", "url": "https://docker.com"}]}
    mock_tavily_class.return_value = mock_tavily

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = make_mock_groq_completion(MOCK_ROADMAP_JSON)
    mock_groq_class.return_value = mock_groq

    with patch("backend.services.roadmap_service.GROQ_API_KEY", "mock_key"), \
         patch("backend.services.roadmap_service.TAVILY_API_KEY", "mock_key"):
        result = generate_roadmap(
            career="Python Developer",
            missing_skills=["Docker"],
            student_skills=["Python", "FastAPI"],
        )

    assert isinstance(result, RoadmapResponse)
    assert result.career == "Python Developer"
    assert result.total_estimated_weeks == 4
    assert len(result.milestones) == 1
    assert result.milestones[0].skill_name == "Docker"
    assert result.milestones[0].difficulty == "Beginner"
    assert len(result.milestones[0].resources) == 1


@patch("backend.services.roadmap_service.TavilyClient")
@patch("backend.services.roadmap_service.Groq")
def test_generate_roadmap_concurrent_tavily_searches(mock_groq_class, mock_tavily_class):
    mock_tavily = MagicMock()
    mock_tavily.search.side_effect = lambda query, **kwargs: {
        "results": [{"title": f"Resource for {query[:25]}", "url": "https://example.com"}]
    }
    mock_tavily_class.return_value = mock_tavily

    multi_milestone_json = {
        "career": "Cloud Engineer",
        "total_estimated_weeks": 8,
        "milestones": [
            {
                "skill_name": "Docker",
                "week_label": "Week 1 - 2",
                "estimated_hours": 12,
                "difficulty": "Beginner",
                "topics_to_learn": ["Containers"],
                "hands_on_project": "Dockerize app",
                "resources": [{"title": "Docker Tutorial", "url": "https://docker.com", "resource_type": "Tutorial", "is_free": True}],
            },
            {
                "skill_name": "Kubernetes",
                "week_label": "Week 3 - 4",
                "estimated_hours": 15,
                "difficulty": "Intermediate",
                "topics_to_learn": ["Pods", "Deployments"],
                "hands_on_project": "Deploy cluster",
                "resources": [{"title": "K8s Guide", "url": "https://kubernetes.io", "resource_type": "Documentation", "is_free": True}],
            },
        ],
    }
    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = make_mock_groq_completion(multi_milestone_json)
    mock_groq_class.return_value = mock_groq

    with patch("backend.services.roadmap_service.GROQ_API_KEY", "mock_key"), \
         patch("backend.services.roadmap_service.TAVILY_API_KEY", "mock_key"):
        result = generate_roadmap(
            career="Cloud Engineer",
            missing_skills=["Docker", "Kubernetes"],
            student_skills=["Linux"],
        )

    assert result.career == "Cloud Engineer"
    assert len(result.milestones) == 2
    assert mock_tavily.search.call_count == 2


@patch("backend.services.roadmap_service.TavilyClient")
@patch("backend.services.roadmap_service.Groq")
def test_generate_roadmap_tavily_failure_resilience(mock_groq_class, mock_tavily_class):
    mock_tavily = MagicMock()
    # Search raises an exception simulating rate limit or network issue
    mock_tavily.search.side_effect = RuntimeError("Tavily 429 Rate Limit Exceeded")
    mock_tavily_class.return_value = mock_tavily

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = make_mock_groq_completion(MOCK_ROADMAP_JSON)
    mock_groq_class.return_value = mock_groq

    with patch("backend.services.roadmap_service.GROQ_API_KEY", "mock_key"), \
         patch("backend.services.roadmap_service.TAVILY_API_KEY", "mock_key"):
        result = generate_roadmap(
            career="Python Developer",
            missing_skills=["Docker"],
            student_skills=["Python"],
        )

    # Verifies graceful degradation: roadmap generation completes despite Tavily error
    assert isinstance(result, RoadmapResponse)
    assert result.career == "Python Developer"
    assert len(result.milestones) == 1
