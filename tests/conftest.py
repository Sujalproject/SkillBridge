import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import fitz  # PyMuPDF
import pytest
from docx import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_candidate_text() -> str:
    return (
        "Alex Rivera\n"
        "Email: alex.rivera@example.com\n"
        "Education: Bachelor of Science in Computer Science, Tech University\n\n"
        "Technical Skills:\n"
        "Python, SQL, PostgreSQL, Docker, Git, GitHub, FastAPI, LangGraph, LangChain, REST APIs, Linux\n\n"
        "Experience:\n"
        "Backend AI Developer at CloudScale Systems. Built scalable REST APIs with FastAPI and Docker containers.\n"
        "Implemented agentic workflows using LangGraph and Groq LLM inference.\n\n"
        "Projects:\n"
        "Career Intelligence Matcher: An agentic semantic search tool matching candidate skills with tech jobs.\n"
        "RAG Document Search: Built a retrieval-augmented generation pipeline using vector databases.\n"
    )


@pytest.fixture
def sample_docx_bytes(sample_candidate_text) -> bytes:
    buffer = io.BytesIO()
    doc = Document()
    for paragraph in sample_candidate_text.split("\n\n"):
        doc.add_paragraph(paragraph)
    doc.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_bytes(sample_candidate_text) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), sample_candidate_text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def make_mock_groq_completion(content_dict: dict):
    """Helper to build a mock Groq ChatCompletion object."""
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(content_dict)
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion
