
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.resume import router as resume_router
from backend.routes.skill_gap import router as skill_gap_router
from backend.routes.career import router as career_router
from backend.routes.career_agent import router as career_agent_router
app = FastAPI(
    title="SkillBridge API",
    description="API for SkillBridge Career Agent",
    version="0.1.0",
)

# Local development only. Tighten allowed origins before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to SkillBridge Career Agent API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skillbridge-api"}

app.include_router(career_agent_router)
app.include_router(resume_router)
app.include_router(skill_gap_router)
app.include_router(career_router)