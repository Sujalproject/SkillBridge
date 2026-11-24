
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
from typing import Any

from fastapi import HTTPException
from groq import Groq
from tavily import TavilyClient

from backend.core.config import GROQ_API_KEY, GROQ_MODEL
from backend.schemas.roadmap import RoadmapResponse

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()


MAX_ROADMAP_SKILLS = 8


def _search_resources_for_skill(skill: str, career: str) -> list[dict]:
    """Use Tavily to find learning resources for a single skill."""
    if not TAVILY_API_KEY:
        return []

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        query = f"learn {skill} tutorial documentation {career}"
        response = client.search(
            query=query,
            max_results=2,
            search_depth="basic",
            include_answer=False,
        )
        results = []
        seen_urls = set()
        for item in response.get("results", []):
            title = item.get("title", skill).strip()
            url = item.get("url", "").strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append({"title": title[:80], "url": url})
        return results
    except Exception as exc:
        logger.warning("Tavily search failed for '%s': %s", skill, exc)
        return []


def generate_roadmap(
    career: str,
    missing_skills: list[str],
    student_skills: list[str] | None = None,
) -> RoadmapResponse:
    """Generate a structured learning roadmap for the given missing skills."""

    if not missing_skills:
        return RoadmapResponse(
            career=career,
            total_estimated_weeks=0,
            milestones=[],
        )

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "GROQ_API_KEY is not configured. "
                "Add it to your .env file and restart the backend."
            ),
        )

    # Focus on the top missing skills to keep the roadmap actionable and within token limits
    skills_to_plan = missing_skills[:MAX_ROADMAP_SKILLS]

    # Step 1: Search resources concurrently for each priority skill via Tavily with bounded concurrency
    skill_resources: dict[str, list[dict]] = {s: [] for s in skills_to_plan}
    if TAVILY_API_KEY and skills_to_plan:
        max_workers = min(4, len(skills_to_plan))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_skill = {
                executor.submit(_search_resources_for_skill, skill, career): skill
                for skill in skills_to_plan
            }
            for future in as_completed(future_to_skill):
                skill = future_to_skill[future]
                try:
                    skill_resources[skill] = future.result()
                except Exception as exc:
                    logger.warning("Error fetching Tavily resources for '%s': %s", skill, exc)
                    skill_resources[skill] = []
    elif skills_to_plan:
        for skill in skills_to_plan:
            skill_resources[skill] = _search_resources_for_skill(skill, career)

    # Step 2: Build the LLM prompt concisely
    resource_context = ""
    for skill, resources in skill_resources.items():
        if resources:
            links = "; ".join(f"{r['title']}: {r['url']}" for r in resources)
            resource_context += f"- {skill}: {links}\n"
        else:
            resource_context += f"- {skill}: (suggest standard docs/tutorials)\n"

    student_skills_summary = (
        ", ".join(student_skills[:15]) if student_skills else "Beginner"
    )

    system_prompt = (
        "You are an expert career coach AI that outputs actionable, personalized learning roadmaps. "
        "Output ONLY valid JSON. Keep descriptions concise."
    )

    user_prompt = (
        f"Create a step-by-step learning roadmap for a '{career}'.\n"
        f"Candidate Background & Existing Skills: {student_skills_summary}\n"
        f"Missing skills to learn: {', '.join(skills_to_plan)}\n\n"
        f"Verified web resources:\n{resource_context}\n"
        "Return a JSON object conforming to this schema:\n"
        "{\n"
        f'  "career": "{career}",\n'
        '  "total_estimated_weeks": <integer>,\n'
        '  "milestones": [\n'
        "    {\n"
        '      "skill_name": "<skill>",\n'
        '      "week_label": "Week X - Y",\n'
        '      "estimated_hours": <integer>,\n'
        '      "difficulty": "Beginner | Intermediate | Advanced",\n'
        '      "topics_to_learn": ["topic 1", "topic 2"],\n'
        '      "hands_on_project": "<concise project description>",\n'
        '      "resources": [\n'
        "        {\n"
        '          "title": "<name>",\n'
        '          "url": "<url>",\n'
        '          "resource_type": "Documentation | Course | Video | Tutorial | Project",\n'
        '          "is_free": true\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        f"- Exactly {len(skills_to_plan)} milestones, one for each missing skill listed above.\n"
        "- Every element of milestones must be a valid JSON object (NEVER an empty string, null, or separator).\n"
        "- Adapt milestone content to candidate background: if the candidate already possesses prerequisite knowledge, skip basic syntax and accelerate into applied intermediate concepts; if the candidate is a beginner, provide foundational scaffolding.\n"
        "- Sequence milestones from foundational to advanced with non-overlapping sequential weeks.\n"
        "- Use the verified web resource URLs provided above where possible.\n"
        "- Keep each topic and project description concise."
    )

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=2500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content
        if not content:
            raise ValueError("The model returned an empty response.")

        parsed: dict[str, Any] = json.loads(content)

        # Robustness unwrapping & sanitization
        if "roadmap" in parsed and isinstance(parsed["roadmap"], dict):
            parsed = parsed["roadmap"]

        raw_milestones = parsed.get("milestones", [])
        if not isinstance(raw_milestones, list):
            raw_milestones = []

        clean_milestones = []
        for item in raw_milestones:
            if isinstance(item, dict) and item.get("skill_name"):
                # Clean resources
                raw_resources = item.get("resources", [])
                if isinstance(raw_resources, list):
                    item["resources"] = [
                        r for r in raw_resources if isinstance(r, dict)
                    ]
                else:
                    item["resources"] = []

                # Ensure estimated_hours is an int
                hours = item.get("estimated_hours", 10)
                if isinstance(hours, str):
                    digits = "".join(c for c in hours if c.isdigit())
                    item["estimated_hours"] = int(digits) if digits else 10
                elif not isinstance(hours, (int, float)) or hours < 1:
                    item["estimated_hours"] = 10
                else:
                    item["estimated_hours"] = int(hours)

                clean_milestones.append(item)

        parsed["milestones"] = clean_milestones
        parsed["career"] = parsed.get("career") or career
        if not parsed.get("total_estimated_weeks"):
            parsed["total_estimated_weeks"] = max(1, len(clean_milestones) * 2)

        return RoadmapResponse.model_validate(parsed)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Could not generate learning roadmap: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not generate the learning roadmap with the LLM. "
                f"Error type: {type(exc).__name__}"
            ),
        ) from exc

