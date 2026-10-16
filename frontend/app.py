import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def fetch_careers() -> list[str]:
    """Fetch available careers from the backend."""
    response = requests.get(
        f"{API_BASE_URL}/careers",
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["careers"]


def display_items(items: list[str], empty_message: str) -> None:
    """Display a list of items or a helpful empty-state message."""
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.write(empty_message)


st.set_page_config(
    page_title="SkillBridge Career Agent",
    page_icon="🌉",
    layout="wide",
)

st.title("🌉 SkillBridge Career Agent")
st.caption(
    "Understand your current profile. Discover your next career-development steps."
)

with st.sidebar:
    st.header("About SkillBridge")
    st.write(
        "SkillBridge helps students compare their demonstrated skills with "
        "career goals and discover practical development steps."
    )
    st.info("Powered by a LangGraph career-analysis workflow")

st.subheader("1. Start your career analysis")
st.write("Upload a text-based PDF or DOCX resume. Maximum size: 5 MB.")

try:
    careers = fetch_careers()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to FastAPI. Start the backend first.")
    st.stop()
except requests.exceptions.Timeout:
    st.error("The backend timed out while loading careers. Please try again.")
    st.stop()
except requests.RequestException as exc:
    st.error(f"Could not load career options: {exc}")
    st.stop()

if not careers:
    st.warning("No careers are currently configured in the backend.")
    st.stop()

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"],
)

target_role = st.selectbox(
    "Choose your target career",
    careers,
)

if uploaded_file is not None:
    st.caption(
        f"Selected file: {uploaded_file.name} · "
        f"{uploaded_file.size:,} bytes"
    )

if st.button(
    "Analyze my career readiness",
    type="primary",
    disabled=uploaded_file is None,
):
    if uploaded_file is not None:
        try:
            with st.spinner(
                "Analyzing your resume, matching skills, and preparing results..."
            ):
                response = requests.post(
                    f"{API_BASE_URL}/career-agent/analyze",
                    data={"career": target_role},
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                            or "application/octet-stream",
                        )
                    },
                    timeout=120,
                )

            if response.ok:
                result = response.json()
                st.session_state["career_analysis"] = result
                st.success("Career analysis completed!")

            else:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text

                st.error(
                    f"Career analysis failed ({response.status_code}): {detail}"
                )

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to FastAPI. "
                "Check that the backend is running at "
                "http://127.0.0.1:8000."
            )
        except requests.exceptions.Timeout:
            st.error(
                "The analysis timed out. Check the backend logs and try again."
            )
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")

result = st.session_state.get("career_analysis")

if result:
    st.divider()
    st.header("2. Your career readiness dashboard")

    st.write(f"**Target career:** {result.get('career', 'Not specified')}")
    st.write(f"**Resume:** {result.get('filename', 'Not specified')}")

    percentage = result.get("match_percentage", 0)
    matched = result.get("matched_skills", [])
    missing = result.get("missing_skills", [])
    required = result.get("required_skills", [])
    profile = result.get("profile", {})
    skills = profile.get("skills", [])

    metric_col, matched_col, missing_col = st.columns(3)

    with metric_col:
        st.metric("Skill match", f"{percentage}%")
        st.progress(max(0, min(percentage, 100)) / 100)

    with matched_col:
        st.metric("Matched skills", len(matched))

    with missing_col:
        st.metric("Skills to develop", len(missing))

    st.divider()
    st.subheader("3. Your current profile")

    left, right = st.columns(2)

    with left:
        st.markdown("**Candidate**")
        st.write(profile.get("full_name") or "Name not found")
        st.write(profile.get("email") or "Email not found")

        st.markdown("**Education**")
        display_items(
            profile.get("education", []),
            "No education details extracted.",
        )

        st.markdown("**Experience**")
        display_items(
            profile.get("experience", []),
            "No experience details extracted.",
        )

    with right:
        st.markdown("**Skills extracted from your resume**")
        if skills:
            st.write(" · ".join(skills))
        else:
            st.info("No skills were extracted. Review your resume.")

        st.markdown("**Projects**")
        display_items(
            profile.get("projects", []),
            "No projects extracted.",
        )

        st.markdown("**Certifications**")
        display_items(
            profile.get("certifications", []),
            "No certifications extracted.",
        )

    st.markdown("**Profile summary**")
    st.write(profile.get("summary") or "No summary extracted.")

    if profile.get("target_role"):
        st.markdown("**Target role mentioned in resume**")
        st.write(profile["target_role"])

    st.divider()
    st.subheader("4. Skill-gap analysis")

    gap_left, gap_right = st.columns(2)

    with gap_left:
        st.markdown("**Skills you already have**")
        display_items(matched, "No direct skill matches found yet.")

    with gap_right:
        st.markdown("**Skills to develop**")
        display_items(missing, "All configured career skills matched!")

    with st.expander("View configured career skills"):
        st.write(required or "No required skills were returned.")

    with st.expander("View structured profile JSON"):
        st.json(profile)

    with st.expander("View complete API response"):
        st.json(result)

    st.warning(
        "This is a prototype. Review extracted information and career "
        "requirements before making career decisions. A skill-match score "
        "does not guarantee job readiness."
    )

st.divider()
st.caption(
    "SkillBridge prototype · Career requirements are loaded from the "
    "backend data file. Personalized roadmaps and progress tracking "
    "will be added in later stages."
)