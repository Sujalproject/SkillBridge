import json
import logging
import re
import traceback
from typing import Any

from fastapi import HTTPException
from groq import BadRequestError, Groq

from backend.core.config import GROQ_API_KEY, GROQ_MODEL
from backend.schemas.resume import CareerProfile

logger = logging.getLogger(__name__)

MAX_RESUME_CHARS = 10000


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
        "- skills (list of strings)\n"
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
        "Keep each list entry concise.\n\n"
        "Resume Text:\n"
        f"{truncated_resume}"
    )

    content: str | None = None

    # Attempt 1: Call Groq with json_object mode and max_tokens
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
    except BadRequestError as exc:
        # If Groq server-side json_object validation trips, retry in standard mode
        logger.warning("Groq json_object mode failed (%s). Retrying in standard completion mode.", exc)
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system_prompt + "\nReturn raw JSON only."},
                    {"role": "user", "content": user_prompt + "\nOutput JSON:"},
                ],
            )
            content = completion.choices[0].message.content
        except Exception as retry_exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=502,
                detail=f"Could not analyze resume with Groq LLM: {retry_exc}",
            ) from retry_exc
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
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
        return CareerProfile.model_validate(parsed)
    except Exception as parse_exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse the LLM's profile response into valid JSON: {parse_exc}",
        ) from parse_exc
