
from backend.services.skill_gap_service import analyze_skill_gap


def test_skill_gap():
    result = analyze_skill_gap(
        student_skills=["Python", "SQL", "Git"],
        required_skills=["Python", "SQL", "FastAPI", "Git", "Docker"],
    )

    assert result["matched_skills"] == ["git", "python", "sql"]
    assert result["missing_skills"] == ["docker", "fastapi"]
    assert result["match_percentage"] == 60


if __name__ == "__main__":
    print(
        analyze_skill_gap(
            student_skills=["Python", "SQL", "Git"],
            required_skills=["Python", "SQL", "FastAPI", "Git", "Docker"],
        )
    )
