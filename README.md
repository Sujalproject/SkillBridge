<div align="center">

  <img src="frontend/images/SkillBridge%20Student%20Growth%20Logo.png" alt="SkillBridge Logo" width="90" style="border-radius: 18px;" />

  # 🌉 SkillBridge Career Agent

  **Agentic AI Career Intelligence, Semantic Skill Gap Analysis & Learning Roadmap Engine**

  [![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
  [![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
  [![Groq](https://img.shields.io/badge/Groq-Llama%20%2F%20GPT--OSS-F55036.svg)](https://groq.com)
  [![Tavily](https://img.shields.io/badge/Tavily-Live%20Search%20API-4F46E5.svg)](https://tavily.com)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

  <p align="center">
    Empowering students and job-seekers to bridge the gap between their current resume skills and target tech roles through state-of-the-art semantic matching, automated curriculum planning, and live web research.
  </p>

</div>

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Application Workflow](#-application-workflow)
- [Tech Stack](#-tech-stack)
- [Directory Structure](#-directory-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Clone & Set Up Virtual Environment](#1-clone--set-up-virtual-environment)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Start the Application](#3-start-the-application)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [License](#-license)

---

## ✨ Key Features

- **Multi-Format Resume Ingestion**: Fast, local text extraction from `.pdf` and `.docx` resumes using PyMuPDF and python-docx without saving sensitive files to disk.
- **LLM-Powered Profile Extraction**: Leverages Groq ultra-low latency inference to parse candidate identity, work experience, education, projects, and demonstrated technical proficiencies into structured Pydantic models.
- **Dual-Mode Target Benchmarking (Conditional Workflow)**:
  - *Standard Mode*: Benchmark against curated industry role standards loaded from the local career taxonomy catalog.
  - *Custom Job Description (JD) Mode*: Paste any arbitrary job posting text. The system automatically detects role seniority, extracts atomic required and preferred skills, and dynamically matches the candidate against that specific job.
- **LangGraph Conditional Routing**: Graph-based multi-agent execution with dynamic conditional edges that route analysis dynamically based on whether a JD was provided.
- **Domain-Agnostic Semantic Skill Gap Engine**: Evaluates candidate competencies across all engineering domains (Web, DevOps, Backend, Cloud, Data, AI) through a robust 4-stage pipeline:
  - *Stage 1 (Universal Normalization)*: Resolves standard technical acronyms and canonical aliases (`K8s` ➔ `Kubernetes`, `JS` ➔ `JavaScript`, `LLM` ➔ `Large Language Models`, `CI/CD` ➔ `CICD`).
  - *Stage 2 (Exact Set Matching)*: Fast deterministic match against normalized required benchmarks.
  - *Stage 3 (LLM Competency Evaluation)*: Groq-powered contextual reasoning using a 4-tier relationship scale (`exact_match`, `strong_evidence`, `related_but_insufficient`, `no_evidence`). Recognizes when a specific technology demonstrates a broader competency (e.g. `Docker` ➔ `Containerization`, `React` ➔ `Frontend Frameworks`, `PostgreSQL` ➔ `SQL`, `Terraform` ➔ `Infrastructure as Code`) without false-positive token guessing.
  - *Stage 4 (Display Name Preservation)*: Preserves the original Job Description or benchmark casing (`Containerization`, `REST APIs`, `FastAPI`) for clean UI presentation.
- **Personalized Learning Roadmap**: Formulates an actionable, week-by-week curriculum sequenced from foundational to advanced milestones, complete with estimated study hours, difficulty ratings, and hands-on capstone project prompts.
- **Live Web Research (Tavily)**: Dynamically verifies and fetches official documentation, top-rated tutorials, and free video courses for each missing skill.
- **Interactive Excel (.xlsx) Export**: Generates a downloadable, multi-tab styled Excel workbook complete with schedule timelines, study checklists, and clickable resource hyperlinks.
- **Modern Bento Grid Web Interface**: Handcrafted in vanilla HTML5, CSS3, and modern JavaScript—featuring obsidian dark mode, tactile glassmorphism, animated SVG progress rings, dual-mode tabs (Career Benchmark vs. Paste Job Description), search filters, and real-time backend status indicators.

---

## 🔄 Application Workflow

```mermaid
flowchart TD
    Start(["Candidate Uploads Resume\n+ Selects Target Role or Pastes Job Description"])
    
    Extract["1. Document Text Extraction\n(PyMuPDF / python-docx)"]
    Profile["2. Candidate Profile Parsing\n(Extracts atomic skills, experience, and education via Groq LLM)"]
    
    Branch{"Job Description\nProvided?"}
    
    JDSkills["3a. Dynamic JD Skill Extraction\n(Extracts mandatory & preferred skills via LLM)"]
    CatalogSkills["3b. Load Career Taxonomy\n(Fetches role standards from career_skills.json)"]
    
    GapEngine["4. Semantic Skill Gap Engine\n(Multi-stage exact, alias, and LLM competency matching)"]
    
    Dashboard["📊 Career Readiness Matrix\n(Match Percentage, Matched Skills, and Learning Priorities)"]
    Roadmap["🗺️ Personalized Learning Roadmap\n(Week-by-week study plan with verified Tavily web resources)"]
    Export["📥 Downloadable Excel Plan\n(Formatted .xlsx workbook with clickable links)"]
    
    Start --> Extract
    Extract --> Profile
    Profile --> Branch
    Branch -- "Yes (Custom JD)" --> JDSkills
    Branch -- "No (Standard Role)" --> CatalogSkills
    JDSkills --> GapEngine
    CatalogSkills --> GapEngine
    GapEngine --> Dashboard
    Dashboard --> Roadmap
    Roadmap --> Export
```

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com), [Uvicorn](https://www.uvicorn.org), [Pydantic v2](https://docs.pydantic.dev) |
| **Agentic Workflow** | [LangGraph](https://langchain-ai.github.io/langgraph/), [LangChain Core](https://python.langchain.com) |
| **LLM Provider** | [Groq](https://groq.com) (`openai/gpt-oss-20b`, `llama-3.3-70b-versatile`) |
| **Web Search & Research** | [Tavily Search API](https://tavily.com) |
| **Document Processing** | [PyMuPDF](https://pymupdf.readthedocs.io), [python-docx](https://python-docx.readthedocs.io), [openpyxl](https://openpyxl.readthedocs.io) |
| **Frontend Application** | Semantic HTML5, Modern CSS3 (Bento Grid & Glassmorphism), Vanilla JavaScript (ES6+) |
| **Testing & Quality** | [Pytest](https://pytest.org), [HTTPX](https://www.python-httpx.org) |

---

## 📁 Directory Structure

```text
skillbridge_starter/
├── backend/
│   ├── core/
│   │   ├── config.py              # Environment configuration & constraints
│   ├── graphs/
│   │   ├── career_graph.py        # LangGraph StateGraph compilation
│   │   ├── nodes.py               # Workflow node handlers
│   │   └── state.py               # Shared CareerState TypedDict definition
│   ├── routes/
│   │   ├── career.py              # Career roles query endpoints
│   │   ├── career_agent.py        # End-to-end resume diagnosis endpoint
│   │   ├── resume.py              # Standalone resume analysis endpoint
│   │   ├── roadmap.py             # Roadmap generation & Excel export endpoints
│   │   └── skill_gap.py           # Standalone skill gap analysis endpoint
│   ├── schemas/
│   │   ├── career.py              # Career Pydantic schemas
│   │   ├── resume.py              # CareerProfile & extraction schemas
│   │   ├── roadmap.py             # Milestone, Resource & Roadmap schemas
│   │   └── skill_gap.py           # Skill gap request & response schemas
│   ├── services/
│   │   ├── career_service.py      # Skill taxonomy queries
│   │   ├── jd_service.py          # LLM Job Description parsing & skill extraction
│   │   ├── resume_service.py      # LLM profile extraction service
│   │   ├── roadmap_service.py     # Tavily search & curriculum planner
│   │   └── semantic_skill_gap_service.py # 3-tier semantic matching engine
│   ├── utils/
│   │   ├── excel_exporter.py      # In-memory openpyxl workbook generator
│   │   └── resume_parser.py       # PDF/DOCX stream text extraction
│   └── main.py                    # FastAPI entrypoint & static mounting
├── data/
│   └── career_skills.json         # Benchmark skill taxonomy across tech roles
├── frontend/
│   ├── images/
│   │   └── SkillBridge Student Growth Logo.png
│   ├── app.js                     # Client UI controller & API integration
│   ├── index.html                 # Bento Grid single-page layout (with dual JD/Role modes)
│   └── styles.css                 # Custom design system & glassmorphism
├── tests/
│   ├── test_api.py                # Health & API route test suite
│   ├── test_jd_pipeline.py        # LangGraph conditional branch & JD parsing tests
│   ├── test_resume_parser.py      # Document parsing unit tests
│   └── test_sujal_pipeline.py     # End-to-end resume extraction verification
├── requirements.txt               # Pinned project dependencies
└── README.md                      # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed on your system.
- A **[Groq API Key](https://console.groq.com)** (free tier available).
- A **[Tavily API Key](https://tavily.com)** for live web search and learning resource curation.

---

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/skillbridge.git
cd skillbridge

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# Tavily Search API Configuration
TAVILY_API_KEY=your_tavily_api_key_here

# Backend Service Base URL
API_BASE_URL=http://127.0.0.1:8000
```

---

### 3. Start the Application

Run the FastAPI server:

```bash
uvicorn backend.main:app --reload --port 8000
```

Once started:
- 🌐 **Web Application**: Open [http://localhost:8000](http://localhost:8000)
- 📚 **Interactive Swagger API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Check**: Open [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status check |
| `GET` | `/careers` | Returns list of configured career paths |
| `GET` | `/careers/{name}/skills` | Returns required benchmark skills for a role |
| `POST` | `/career-agent/analyze` | Full LangGraph agent execution: conditional routing on optional `job_description` vs. role catalog, parses profile, and executes semantic skill gap analysis |
| `POST` | `/skills/analyze` | Standalone semantic skill gap diagnostic |
| `POST` | `/roadmap/generate` | Generates a sequenced, week-by-week curriculum with Tavily resources |
| `POST` | `/roadmap/export` | Generates and streams a formatted `.xlsx` workbook |

---

## 🧪 Testing

Execute the automated test suite with `pytest`:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
```

All tests cover:
- Health check and API route availability.
- Multi-format document text extraction (PDF & DOCX).
- Semantic skill gap matching (exact, alias, and LLM-evaluated equivalence).

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
