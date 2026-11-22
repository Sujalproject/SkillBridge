
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.resume import router as resume_router
from backend.routes.skill_gap import router as skill_gap_router
from backend.routes.career import router as career_router
from backend.routes.career_agent import router as career_agent_router
from backend.routes.roadmap import router as roadmap_router

app = FastAPI(
    title="SkillBridge API",
    description="API for SkillBridge Career Agent",
    version="0.1.0",
)

# Allow all origins for local development and direct HTML/JS frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skillbridge-api"}

app.include_router(career_agent_router)
app.include_router(resume_router)
app.include_router(skill_gap_router)
app.include_router(career_router)
app.include_router(roadmap_router)

# Mount frontend directory for static assets and serving HTML
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")