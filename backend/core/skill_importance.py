"""Explicit, auditable configuration for skill importance tiers across predefined roles.

Tiers:
- Critical (Tier 1, weight 3.0): Foundational core competencies essential to the role.
- Core (Tier 2, weight 2.0): Key frameworks, libraries, and primary technologies.
- Secondary (Tier 3, weight 1.0): Supporting tools, linters, and secondary skills.

For any role or skill without explicit validated configuration, default weight is 1.0
(equal weighting), ensuring no unverified assumptions are introduced.
"""

from typing import Any

ROLE_SKILL_IMPORTANCE: dict[str, dict[str, list[str]]] = {
    "Python Developer": {
        "critical": [
            "python",
            "python syntax and semantics",
            "data types and collections",
            "control flow",
            "functions and modules",
            "object-oriented programming",
            "exception handling",
            "data structures and algorithms",
        ],
        "core": [
            "fastapi",
            "django",
            "flask",
            "postgresql",
            "sql",
            "sqlalchemy",
            "rest api design",
            "pytest",
            "unit testing",
            "docker",
            "git",
            "asyncio and concurrency",
            "type hints",
        ],
    },
    "AI Engineer": {
        "critical": [
            "python",
            "machine learning",
            "deep learning",
            "large language models",
            "pytorch",
            "tensorflow",
            "retrieval-augmented generation",
            "vector databases",
        ],
        "core": [
            "scikit-learn",
            "langgraph",
            "langchain",
            "fastapi",
            "docker",
            "git",
            "data preprocessing",
            "feature engineering",
            "model evaluation and validation",
            "transformer architecture",
            "huggingface transformers",
            "fine-tuning (lora, qlora)",
            "mlops fundamentals",
        ],
    },
    "DevOps Engineer": {
        "critical": [
            "linux",
            "linux administration",
            "docker",
            "containerization",
            "kubernetes",
            "ci/cd",
            "ci/cd pipelines",
            "terraform",
            "infrastructure as code",
        ],
        "core": [
            "amazon web services",
            "google cloud",
            "microsoft azure",
            "git",
            "ansible",
            "helm",
            "prometheus",
            "grafana",
            "shell scripting",
            "bash",
            "python",
        ],
    },
    "Frontend Developer": {
        "critical": [
            "html",
            "css",
            "javascript",
            "typescript",
            "react",
            "responsive design",
        ],
        "core": [
            "next.js",
            "vue",
            "angular",
            "state management",
            "rest api consumption",
            "tailwind css",
            "jest",
            "git",
            "web performance",
            "browser apis",
            "dom",
        ],
    },
    "Data Scientist": {
        "critical": [
            "python",
            "sql",
            "statistics",
            "probability",
            "machine learning",
            "pandas",
            "numpy",
        ],
        "core": [
            "scikit-learn",
            "exploratory data analysis",
            "feature engineering",
            "data cleaning",
            "data visualization",
            "matplotlib",
            "seaborn",
            "model evaluation and validation",
            "git",
        ],
    },
}


def get_skill_importance(role: str, skill_norm: str) -> dict[str, Any]:
    """Retrieve the importance tier and numerical weight for a skill in a given role."""
    role_config = ROLE_SKILL_IMPORTANCE.get(role)
    if not role_config:
        return {"tier": "secondary", "weight": 1.0, "is_critical": False}

    critical_set = set(role_config.get("critical", []))
    core_set = set(role_config.get("core", []))

    if skill_norm in critical_set:
        return {"tier": "critical", "weight": 3.0, "is_critical": True}
    if skill_norm in core_set:
        return {"tier": "core", "weight": 2.0, "is_critical": False}

    return {"tier": "secondary", "weight": 1.0, "is_critical": False}
