import json
import logging
import re
import time
import traceback
from typing import Any

from fastapi import HTTPException
from groq import BadRequestError, Groq, RateLimitError

from backend.core.config import GROQ_API_KEY, GROQ_MODEL
from backend.schemas.resume import CareerProfile

logger = logging.getLogger(__name__)

MAX_RESUME_CHARS = 10000


def _clean_and_split_skills(raw_skills: list[Any]) -> list[str]:
    """Ensure skills are individual, atomic skill names rather than bundled strings."""
    cleaned: list[str] = []
    for item in raw_skills:
        if not isinstance(item, str):
            continue
        # Split by comma, semicolon, bullet, vertical bar, or newline
        for part in re.split(r"[,;•|/\n]+", item):
            s = part.strip()
            # Strip leading bullets, dashes, or numbering
            s = re.sub(r"^[-*●•\d.)\s]+", "", s).strip()
            # Ignore noise tokens
            if s and len(s) > 1 and s.lower() not in {"and", "&", "etc", "etc."}:
                cleaned.append(s)
    # Deduplicate while preserving order
    return list(dict.fromkeys(cleaned))


def _extract_json_from_text(text: str) -> dict[str, Any]:
    """Extract and parse JSON object from text or markdown code block."""
    cleaned = text.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find the outermost { ... }
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


def analyze_resume_text(resume_text: str) -> CareerProfile:
    """Extract a structured candidate profile from raw resume text using Groq LLM."""
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "GROQ_API_KEY is not configured. "
                "Add it to your .env file and restart the backend."
            ),
        )

    client = Groq(api_key=GROQ_API_KEY)
    truncated_resume = resume_text[:MAX_RESUME_CHARS].strip()

    system_prompt = (
        "You are an expert AI resume parser. Extract factual career information from the resume. "
        "Return ONLY a valid JSON object with these exact keys:\n"
        "- full_name (string or null)\n"
        "- email (string or null)\n"
        "- education (list of strings)\n"
        "- skills (list of individual atomic skill strings; extract each technology, library, framework, or tool as its own separate string, e.g. ['Python', 'SQL', 'FastAPI'], NEVER combine multiple items into one string)\n"
        "- projects (list of strings)\n"
        "- experience (list of strings)\n"
        "- certifications (list of strings)\n"
        "- target_role (string or null)\n"
        "- summary (string or null)\n"
        "Use null for unknown scalar values and [] for unknown lists. "
        "Do not invent or infer credentials not present in the text."
    )

    user_prompt = (
        "Extract the candidate profile from this resume as a valid JSON object. "
        "Ensure all skills are split into individual, atomic strings.\n\n"
        "Resume Text:\n"
        f"{truncated_resume}"
    )

    content: str | None = None

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=2500,
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
                    max_tokens=2500,
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
            logger.warning("Groq rate limit on resume parsing (attempt %d/3). Sleeping %.1fs...", attempt + 1, delay)
            time.sleep(delay)
            if attempt == 2:
                raise HTTPException(status_code=429, detail=f"Rate limit exceeded on Groq LLM: {exc}") from exc
        except BadRequestError as exc:
            logger.warning("Groq json_object mode failed (%s). Retrying in standard completion mode.", exc)
            try:
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=2500,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nReturn raw JSON only."},
                        {"role": "user", "content": user_prompt + "\nOutput JSON:"},
                    ],
                )
                content = completion.choices[0].message.content
                if content and content.strip():
                    break
            except Exception as retry_exc:
                logger.error("Groq resume completion retry failed: %s", retry_exc, exc_info=True)
                raise HTTPException(
                    status_code=502,
                    detail=f"Could not analyze resume with Groq LLM. Error type: {type(retry_exc).__name__}",
                ) from retry_exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Groq resume analysis failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"Could not analyze the resume with the LLM. Error type: {type(exc).__name__}",
            ) from exc

    if not content:
        raise HTTPException(
            status_code=502,
            detail="The LLM returned an empty response.",
        )

    try:
        parsed = _extract_json_from_text(content)
        if "skills" in parsed and isinstance(parsed["skills"], list):
            parsed["skills"] = _clean_and_split_skills(parsed["skills"])
        return CareerProfile.model_validate(parsed)
    except Exception as parse_exc:
        logger.error("Failed to parse LLM profile response: %s", parse_exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse the LLM's profile response into valid JSON: {parse_exc}",
        ) from parse_exc
