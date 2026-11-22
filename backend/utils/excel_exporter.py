
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backend.schemas.roadmap import RoadmapExportRequest


def generate_roadmap_excel(roadmap: RoadmapExportRequest) -> BytesIO:
    """Generate a styled Excel workbook from the roadmap data."""

    wb = Workbook()

    # ── Styles ──────────────────────────────────────────────
    header_font = Font(name="Calibri", bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(
        start_color="2E86AB", end_color="2E86AB", fill_type="solid"
    )
    header_alignment = Alignment(
        horizontal="center", vertical="center", wrap_text=True
    )
    cell_alignment = Alignment(vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    title_font = Font(name="Calibri", bold=True, size=14, color="2E86AB")

    def style_header_row(ws, headers: list[str], row: int = 1) -> None:
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

    def style_data_cell(
        ws,
        row: int,
        col: int,
        value,
        is_link: bool = False,
        url: str = "",
    ) -> None:
        cell = ws.cell(row=row, column=col, value=value)
        cell.alignment = cell_alignment
        cell.border = thin_border
        if is_link and url:
            cell.hyperlink = url
            cell.font = Font(
                name="Calibri", color="0563C1", underline="single"
            )

    # ── Sheet 1: Learning Roadmap ───────────────────────────
    ws_plan = wb.active
    ws_plan.title = "Learning Roadmap"

    # Title row
    ws_plan.merge_cells("A1:F1")
    title_cell = ws_plan["A1"]
    title_cell.value = (
        f"SkillBridge Learning Roadmap — {roadmap.career}"
    )
    title_cell.font = title_font
    title_cell.alignment = Alignment(
        horizontal="center", vertical="center"
    )

    ws_plan.merge_cells("A2:F2")
    subtitle = ws_plan["A2"]
    subtitle.value = (
        f"Total estimated duration: {roadmap.total_estimated_weeks} weeks"
    )
    subtitle.font = Font(name="Calibri", italic=True, size=11)
    subtitle.alignment = Alignment(horizontal="center")

    # Headers on row 4
    plan_headers = [
        "Timeline",
        "Skill",
        "Est. Hours",
        "Difficulty",
        "Topics to Learn",
        "Hands-on Project",
    ]
    style_header_row(ws_plan, plan_headers, row=4)

    # Data rows
    for i, milestone in enumerate(roadmap.milestones):
        row = 5 + i
        topics_text = "\n".join(
            f"• {t}" for t in milestone.topics_to_learn
        )

        style_data_cell(ws_plan, row, 1, milestone.week_label)
        style_data_cell(ws_plan, row, 2, milestone.skill_name)
        style_data_cell(
            ws_plan, row, 3, f"{milestone.estimated_hours} hrs"
        )
        style_data_cell(ws_plan, row, 4, milestone.difficulty)
        style_data_cell(ws_plan, row, 5, topics_text)
        style_data_cell(ws_plan, row, 6, milestone.hands_on_project)

    # Column widths
    plan_widths = [16, 22, 12, 16, 45, 40]
    for idx, width in enumerate(plan_widths, 1):
        ws_plan.column_dimensions[get_column_letter(idx)].width = width

    # ── Sheet 2: Resource Directory ─────────────────────────
    ws_res = wb.create_sheet(title="Resource Directory")

    ws_res.merge_cells("A1:E1")
    res_title = ws_res["A1"]
    res_title.value = f"Curated Resources — {roadmap.career}"
    res_title.font = title_font
    res_title.alignment = Alignment(
        horizontal="center", vertical="center"
    )

    res_headers = [
        "Skill",
        "Resource Title",
        "Type",
        "Free / Paid",
        "Link",
    ]
    style_header_row(ws_res, res_headers, row=3)

    res_row = 4
    for milestone in roadmap.milestones:
        for resource in milestone.resources:
            style_data_cell(ws_res, res_row, 1, milestone.skill_name)
            style_data_cell(
                ws_res,
                res_row,
                2,
                resource.title,
                is_link=True,
                url=resource.url,
            )
            style_data_cell(ws_res, res_row, 3, resource.resource_type)
            style_data_cell(
                ws_res,
                res_row,
                4,
                "Free" if resource.is_free else "Paid",
            )
            style_data_cell(
                ws_res,
                res_row,
                5,
                resource.url,
                is_link=True,
                url=resource.url,
            )
            res_row += 1

    # Column widths
    res_widths = [22, 40, 18, 12, 50]
    for idx, width in enumerate(res_widths, 1):
        ws_res.column_dimensions[get_column_letter(idx)].width = width

    # ── Save to BytesIO ─────────────────────────────────────
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

