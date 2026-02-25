from __future__ import annotations

from datetime import datetime
from io import BytesIO

from fastapi.responses import StreamingResponse

from src.api.api_routes import register
from src.service.email_service import _build_salary_excel


def build_salary_report_stream(type_filter: str = "function") -> StreamingResponse:
    filename = f"salary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    excel_bytes = _build_salary_excel(type_filter=type_filter)
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@register(name="download/salary-report", method="POST", required_keys=[], optional_keys={"type": "function"})
async def download_salary_report_handler(data: dict):
    return build_salary_report_stream(type_filter=str(data.get("type") or "function"))
