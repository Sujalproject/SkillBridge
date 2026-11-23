import json
import logging
import re
import time
import traceback
from typing import Any

from fastapi import HTTPException
from groq import BadRequestError, Groq, RateLimitError

from backend.core.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

MAX_JD_CHARS = 10000


def _clean_and_dedup_skills(skills_list: list[Any]) -> list[str]:
    """Clean, split, and deduplicate extracted skill items into atomic tokens."""
    cleaned: list[str] = []
    for item in skills_list:
        if isinstance(item, dict):
            # If the LLM returned {"name": "Python", ...}
            name = item.get("name", "")
        elif isinstance(item, str):
            name = item
        else:
            continue

        for part in re.split(r"[,;•|/\n]+", name):
            s = part.strip()
            s = re.sub(r"^[-*●•\d.)\s]+", "", s).strip()
            if s and len(s) > 1 and s.lower() not in {"and", "&", "etc", "etc.", "required", "preferred"}:
                cleaned.append(s)

    return list(dict.fromkeys(cleaned))


def _extract_json_from_text(text: str) -> dict[str, Any]:
    """Extract and parse JSON object from text or markdown code block."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return json.loads(match.group(0))

    raise ValueError("No valid JSON object could be extracted from LLM output.")


def _extract_retry_delay(exc: Exception, default_delay: float = 6.0) -> float:
    """Parse suggested retry delay from Groq rate limit message."""
    match = re.search(r"try again in ([\d\.]+)s", str(exc), re.IGNORECASE)
    if match:
        try:
            return min(float(match.group(1)) + 1.0, 35.0)
        except ValueError:
            pass
    return default_delay


def extract_skills_from_jd(jd_text: str) -> dict[str, Any]:
    """Extract required skills, job title, and seniority from a Job Description using Groq LLM."""
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "GROQ_API_KEY is not configured. "
                "Add it to your .env file and restart the backend."
            ),
        )

    clean_text = jd_text[:MAX_JD_CHARS].strip()
    if len(clean_text) < 30:
        raise ValueError("Job description is too short to analyze.")

    client = Groq(api_key=GROQ_API_KEY)

    system_prompt = (
        "You are an expert Technical Recruiter and Job Description Intelligence Specialist. "
        "Your task is to analyze the given job description and extract the technical skills, "
        "tools, frameworks, and qualifications required for the role.\n\n"
        "Extraction Rules:\n"
        "- Extract individual, atomic technical skills (e.g. ['Python', 'SQL', 'Docker', 'FastAPI'], "
        "NEVER group multiple skills into a single comma-separated string).\n"
        "- Identify the specific job title (e.g. 'Senior AI Engineer', 'Backend Developer').\n"
        "- Classify mandatory skills (must-have/required) vs preferred skills (nice-to-have/plus).\n"
        "- Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "job_title": "Extracted Job Title",\n'
        '  "seniority_level": "Entry-level | Junior | Mid-level | Senior | Lead",\n'
        '  "mandatory_skills": ["Skill1", "Skill2"],\n'
        '  "preferred_skills": ["Skill3", "Skill4"],\n'
        '  "summary": "Brief 1-2 sentence overview of the role requirements"\n'
        "}\n"
        "Do not invent skills not mentioned or implied by the job responsibilities."
    )

    user_prompt = (
        "Analyze this Job Description and extract the technical requirements as a valid JSON object:\n\n"
        f"{clean_text}"
    )

    content: str | None = None

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            if not content or not content.strip():
                logger.warning("Groq returned empty content with json_object mode. Retrying in standard mode.")
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=2000,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nReturn raw JSON only."},
                        {"role": "user", "content": user_prompt + "\nOutput JSON:"},
                    ],
                )
                content = completion.choices[0].message.content
            if content and content.strip():
                break
        except RateLimitError as exc:
            delay = _extract_retry_delay(exc)
            logger.warning("Groq rate limit on JD extraction (attempt %d/3). Sleeping %.1fs...", attempt + 1, delay)
            time.sleep(delay)
            if attempt == 2:
                raise HTTPException(status_code=429, detail=f"Rate limit exceeded on Groq LLM: {exc}") from exc
        except BadRequestError as exc:
            logger.warning("Groq json_object mode failed (%s). Retrying in standard completion mode.", exc)
            try:
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=2000,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nReturn raw JSON only."},
                        {"role": "user", "content": user_prompt + "\nOutput JSON:"},
                    ],
                )
                content = completion.choices[0].message.content
                if content and content.strip():
                    break
            except Exception as retry_exc:
                traceback.print_exc()
                raise HTTPException(
                    status_code=502,
                    detail=f"Could not analyze job description with Groq LLM: {retry_exc}",
                ) from retry_exc
        except HTTPException:
            raise
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=502,
                detail=f"Could not analyze job description with LLM. Error type: {type(exc).__name__}",
            ) from exc

    if not content:
        raise HTTPException(status_code=502, detail="The LLM returned an empty response.")

    try:
        parsed = _extract_json_from_text(content)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse extracted JD JSON: {exc}",
        ) from exc

    mandatory = _clean_and_dedup_skills(parsed.get("mandatory_skills", []))
    preferred = _clean_and_dedup_skills(parsed.get("preferred_skills", []))

    # All unique required skills for matching
    all_skills = list(dict.fromkeys(mandatory + preferred))

    job_title = parsed.get("job_title") or "Custom Target Role"
    seniority = parsed.get("seniority_level") or "Not Specified"
    summary = parsed.get("summary") or ""

    return {
        "job_title": job_title,
        "seniority_level": seniority,
        "mandatory_skills": mandatory,
        "preferred_skills": preferred,
        "required_skills": all_skills,
        "summary": summary,
    }
