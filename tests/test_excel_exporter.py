import io
import sys
from pathlib import Path

import openpyxl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas.roadmap import LearningResource, RoadmapExportRequest, SkillMilestone
from backend.utils.excel_exporter import generate_roadmap_excel


def test_excel_exporter_generation():
    request = RoadmapExportRequest(
        career="Python Developer",
        total_estimated_weeks=6,
        milestones=[
            SkillMilestone(
                skill_name="Docker",
                week_label="Week 1 - 2",
                estimated_hours=12,
                difficulty="Beginner",
                topics_to_learn=["Containers", "Images", "Compose"],
                completed_topics=["Containers", "Images"],
                hands_on_project="Containerize FastAPI app",
                resources=[
                    LearningResource(
                        title="Docker Docs",
                        url="https://docs.docker.com",
                        resource_type="Documentation",
                        is_free=True,
                    )
                ],
            )
        ],
    )

    buffer = generate_roadmap_excel(request)
    assert buffer is not None
    assert buffer.getbuffer().nbytes > 0

    wb = openpyxl.load_workbook(io.BytesIO(buffer.getvalue()))
    assert "Learning Roadmap" in wb.sheetnames
    assert "Resource Directory" in wb.sheetnames

    # Verify Sheet 1
    ws_plan = wb["Learning Roadmap"]
    assert "Python Developer" in ws_plan["A1"].value
    assert ws_plan["B5"].value == "Docker"
    assert ws_plan["C5"].value == "12 hrs"
    topics_cell = ws_plan["E5"].value
    # Assert completed topics have checkmark [✓] and incomplete have [ ]
    assert "[✓] Containers" in topics_cell
    assert "[✓] Images" in topics_cell
    assert "[ ] Compose" in topics_cell

    # Verify Sheet 2
    ws_res = wb["Resource Directory"]
    assert ws_res["A4"].value == "Docker"
    assert ws_res["B4"].value == "Docker Docs"
    assert ws_res["B4"].hyperlink is not None
    assert ws_res["B4"].hyperlink.target == "https://docs.docker.com"
