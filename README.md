# SkillBridge Career Agent — Starter (Phase 1)

First milestone:
1. Upload a PDF or DOCX resume in Streamlit.
2. Streamlit sends it to FastAPI.
3. FastAPI extracts text.
4. FastAPI optionally calls Groq to create a structured profile.
5. The profile is displayed in the UI.

## Requirements
- Python 3.10+
- A Groq API key for AI profile extraction (optional for the initial API health check)
- Internet access to install packages

## 1. Create and activate a virtual environment

From this folder:

### Windows PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
Then use `.\.venv\Scripts\python.exe` instead of `python`.

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure environment variables

Copy `.env.example` to `.env` and add your Groq key:
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
API_BASE_URL=http://127.0.0.1:8000
```

Do not commit `.env` or share your API key.

## 3. Run the backend

Open Terminal 1 in the project root:
```bash
uvicorn backend.main:app --reload
```

Check:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

The health endpoint should return `{"status":"ok","service":"skillbridge-api"}`.

## 4. Run the frontend

Open Terminal 2 in the project root and activate the same virtual environment, then:
```bash
streamlit run frontend/app.py
```

Streamlit should open a browser tab. Upload a PDF/DOCX resume and click **Analyze resume**.

## 5. Test without the UI

With the backend running:
```bash
python -m pytest
```

The automated tests cover the health endpoint and resume text extraction helpers. The Groq call is not made by these tests.

## Current limitations
- The first version processes text-based PDFs and DOCX files. Scanned PDFs need OCR, which we can add later.
- Resume information can be incomplete or misread. Review extracted fields before using them.
- The API does not save uploaded resumes to disk or a database.
- This is a local development starter, not a production deployment.
