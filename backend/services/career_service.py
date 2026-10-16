
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAREER_SKILLS_FILE = PROJECT_ROOT / "data" / "career_skills.json"


def get_career_skills() -> dict[str, list[str]]:
    """Load career requirements from the JSON data file."""

    try:
        with CAREER_SKILLS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Career skills data file not found: {CAREER_SKILLS_FILE}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Career skills JSON is invalid: {exc}"
        ) from exc

    if not isinstance(data, dict) or not data:
        raise ValueError("Career skills data must be a non-empty JSON object.")

    for career, skills in data.items():
        if not isinstance(career, str) or not career.strip():
            raise ValueError("Each career must have a non-empty name.")

        if not isinstance(skills, list) or not skills:
            raise ValueError(
                f"Skills for '{career}' must be a non-empty list."
            )

        if not all(
            isinstance(skill, str) and skill.strip()
            for skill in skills
        ):
            raise ValueError(
                f"Every skill for '{career}' must be a non-empty string."
            )

    return {
        career: list(dict.fromkeys(
            skill.strip() for skill in skills
        ))
        for career, skills in data.items()
    }


def get_career_names() -> list[str]:
    """Return the available career names."""

    return sorted(get_career_skills().keys())


def get_required_skills(career: str) -> list[str]:
    """Return required skills for a specific career."""

    careers = get_career_skills()

    if career not in careers:
        raise ValueError(f"Unknown career: {career}")

    return careers[career]
