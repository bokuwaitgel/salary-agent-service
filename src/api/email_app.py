from __future__ import annotations

import json
import os
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from io import BytesIO
from typing import List, Optional

import smtplib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from src.dependencies import get_classifier_output_repository
from schemas.base_classifier import JobClassificationOutput, JobRequirement, JobBenefit

load_dotenv()

app = FastAPI(title="Salary Agent Email API", version="1.0.0")


class EmailRequest(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    subject: Optional[str] = Field(None, description="Email subject")


def _format_requirements(requirements: List[object]) -> str:
    if not requirements:
        return ""
    formatted: List[str] = []
    for req in requirements:
        if isinstance(req, JobRequirement):
            importance = f" ({req.importance})" if req.importance else ""
            formatted.append(f"{req.name}: {req.details}{importance}")
        elif isinstance(req, dict):
            name = str(req.get("name", "")).strip()
            details = str(req.get("details", "")).strip()
            importance = str(req.get("importance", "")).strip()
            suffix = f" ({importance})" if importance else ""
            text = ": ".join(part for part in [name, details] if part)
            formatted.append(f"{text}{suffix}" if text else "")
        else:
            formatted.append(str(req))
    return ", ".join([item for item in formatted if item])


def _format_benefits(benefits: List[object]) -> str:
    if not benefits:
        return ""
    formatted: List[str] = []
    for benefit in benefits:
        if isinstance(benefit, JobBenefit):
            value = f" (Үнэлгээ: {benefit.monetary_value} MNT)" if benefit.monetary_value else ""
            formatted.append(f"{benefit.name}: {benefit.description}{value}")
        elif isinstance(benefit, dict):
            name = str(benefit.get("name", "")).strip()
            description = str(benefit.get("description", "")).strip()
            value = benefit.get("monetary_value")
            suffix = f" (Үнэлгээ: {value} MNT)" if value else ""
            text = ": ".join(part for part in [name, description] if part)
            formatted.append(f"{text}{suffix}" if text else "")
        else:
            formatted.append(str(benefit))
    return ", ".join([item for item in formatted if item])


def _enum_value(value: Optional[object]) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _coerce_list(value: object) -> List[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [value]
        return [value]
    return [value]

def _build_excel() -> bytes:
    classifications = get_classifier_output_repository().get_all()

    workbook = Workbook()
    sheet: Worksheet = workbook.active  # type: ignore
    sheet.title = "Job Classifications" 

    headers = [
        "Title",
        "Job Function",
        "Job Industry",
        "Job Level",
        "Job Techpack Category",
        "Experience Level",
        "Education Level",
        "Salary Min",
        "Salary Max",
        "Company",
        "Requirements",
        "Benefits",
    ]

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    sheet.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = sheet.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    body_alignment = Alignment(vertical="top", wrap_text=True)

    for item in classifications:
        # Handle requirements formatting
        formatted_requirements = _format_requirements(_coerce_list(item.requirements))
        
        # Handle benefits formatting
        formatted_benefits = _format_benefits(_coerce_list(item.benefits))
        
        sheet.append(
            [
                item.title,
                _enum_value(item.job_function),
                _enum_value(item.job_industry),
                _enum_value(item.job_level),
                _enum_value(item.job_techpack_category),
                _enum_value(item.experience_level),
                _enum_value(item.education_level),
                item.salary_min,
                item.salary_max,
                item.company_name or "",
                formatted_requirements,
                formatted_benefits,
            ]
        )

    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
        for cell in row:
            cell.alignment = body_alignment

    column_widths = {
        1: 28,
        2: 20,
        3: 24,
        4: 18,
        5: 28,
        6: 18,
        7: 18,
        8: 14,
        9: 14,
        10: 20,
        11: 40,
        12: 40,
    }

    for col_idx, width in column_widths.items():
        sheet.column_dimensions[chr(64 + col_idx)].width = width

    file_stream = BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)
    return file_stream.read()


def _send_email(to_email: str, subject: str, attachment: bytes, filename: str) -> None:
    sender_email = os.getenv("SENDER_EMAIL", "itgel6708@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    # Allow overriding recipients via env vars, but keep current defaults.
    receiver_emails = [to_email]
    # cc_emails = _parse_email_list(os.getenv("CC_EMAILS") or os.getenv("CC_EMAIL"), fallback=[])
     # Root container must be 'mixed' when there are attachments.
    msg = MIMEMultipart("mixed")
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = subject

    # Attach the Excel file.
    part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    part.set_payload(attachment)    
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)
    # Send the email via SMTP server.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

    


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/email/job-classifications")
async def email_job_classifications(request: EmailRequest) -> dict:


    subject = request.subject or "Job Classification Results"

    try:
        attachment = _build_excel()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_classifications_{timestamp}.xlsx"
        _send_email(request.to_email, subject, attachment, filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "sent", "to": request.to_email, "filename": filename}
