from __future__ import annotations
from datetime import datetime
from typing import Dict

from src.service.email_service import _build_salary_excel, _build_excel, _send_email

from src.api.api_routes import register



def send_salary_report_email(to_email: str, type_filter: str = "function", subject: str | None = None) -> Dict[str, str]:
    resolved_subject = subject or "Salary Report"
    filename = f"salary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    excel_bytes = _build_salary_excel(type_filter=type_filter)
    _send_email(to_email, resolved_subject, excel_bytes, filename)
    return {"status": "sent", "to": to_email, "filename": filename}

def send_job_classification_email(to_email: str, subject: str | None = None) -> Dict[str, str]:
    resolved_subject = subject or "Job Classification Results"
    filename = f"job_classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    attachment = _build_excel()
    _send_email(to_email, resolved_subject, attachment, filename)
    return {"status": "sent", "to": to_email, "filename": filename}


@register(
    name="email/salary-report",
    method="POST",
    required_keys=["to_email"],
    optional_keys={"subject": None, "type": "function"},
)
async def email_salary_report_handler(data: dict):
    return send_salary_report_email(
        to_email=str(data["to_email"]),
        type_filter=str(data.get("type") or "function"),
        subject=str(data["subject"]) if data.get("subject") else None,
    )

@register(name="email/job-classifications", method="POST", required_keys=["to_email"], optional_keys={"subject": None})
async def email_job_classifications_handler(data: dict):
    return send_job_classification_email(
        to_email=str(data["to_email"]),
        subject=str(data["subject"]) if data.get("subject") else None,
    )

