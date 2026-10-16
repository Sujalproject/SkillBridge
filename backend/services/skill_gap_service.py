
def normalize_skill(skill: str) -> str:
    """Normalize a skill for comparison."""
    return skill.strip().lower()


def analyze_skill_gap(
    student_skills: list[str],
    required_skills: list[str],
) -> dict:
    """Compare student skills with the skills required for a role."""

    student = {normalize_skill(skill) for skill in student_skills if skill.strip()}
    required = {normalize_skill(skill) for skill in required_skills if skill.strip()}

    matched = sorted(student & required)
    missing = sorted(required - student)

    match_percentage = (
        round(len(matched) / len(required) * 100)
        if required
        else 0
    )

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": match_percentage,
    }
