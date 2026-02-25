from __future__ import annotations

import os
import time
from io import BytesIO
from typing import Any, Dict, List, Optional, cast

import pandas as pd
from fastapi.responses import StreamingResponse
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import create_engine

from src.api.api_routes import register

_MAIN_CACHE: Optional[pd.DataFrame] = None
_MAIN_CACHE_TS: float = 0.0
_JOBS_CACHE: Optional[pd.DataFrame] = None
_JOBS_CACHE_TS: float = 0.0


def _engine():
    return create_engine(os.getenv("DATABASE_URI", "sqlite:///products.db"), pool_pre_ping=True)


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip().replace("\u00a0", " ").replace("₮", "").replace(" ", "")
        if not text:
            return None
        if text.count(",") > 1 and "." not in text:
            text = text.replace(",", "")
        elif text.count(".") > 1 and "," not in text:
            text = text.replace(".", "")
        elif "," in text and "." not in text:
            text = text.replace(",", "")
        value = text
    try:
        parsed = float(cast(str | int | float, value))
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def _json_ready_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []
    prepared = df.copy().astype(object)
    prepared = prepared.where(pd.notnull(prepared), "")

    datetime_cols = prepared.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns.tolist()
    for col in datetime_cols:
        prepared[col] = prepared[col].apply(lambda x: x.isoformat() if x else "")

    return cast(List[Dict[str, Any]], prepared.to_dict("records"))


def _load_main_df(refresh: bool = False) -> pd.DataFrame:
    global _MAIN_CACHE, _MAIN_CACHE_TS

    now = time.time()
    if not refresh and _MAIN_CACHE is not None and (now - _MAIN_CACHE_TS) < 45:
        return _MAIN_CACHE.copy()

    df = pd.read_sql("SELECT * FROM salary_calculation_output ORDER BY created_at DESC", _engine())

    for col in [
        "min_salary",
        "max_salary",
        "average_salary",
        "job_count",
        "zangia_count",
        "lambda_count",
        "year",
        "month",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    if "year" in df.columns and "month" in df.columns:
        df["period"] = df.apply(
            lambda x: f"{int(x['year'])}-{int(x['month']):02d}"
            if pd.notna(x["year"]) and pd.notna(x["month"])
            else None,
            axis=1,
        )

    for col in ["job_count", "zangia_count", "lambda_count"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    _MAIN_CACHE = df
    _MAIN_CACHE_TS = now
    return df.copy()


def _load_jobs_df(limit: int = 10000, refresh: bool = False) -> pd.DataFrame:
    global _JOBS_CACHE, _JOBS_CACHE_TS

    now = time.time()
    if not refresh and _JOBS_CACHE is not None and (now - _JOBS_CACHE_TS) < 45:
        return _JOBS_CACHE.head(limit).copy()

    engine = _engine()
    queries = [
        f"SELECT * FROM job_classification_output ORDER BY created_at DESC LIMIT {int(limit)}",
        f"SELECT * FROM job_classification_output ORDER BY id DESC LIMIT {int(limit)}",
        f"SELECT * FROM job_classification_output LIMIT {int(limit)}",
    ]

    df = pd.DataFrame()
    for query in queries:
        try:
            df = pd.read_sql(query, engine)
            if not df.empty:
                break
        except Exception:
            continue

    _JOBS_CACHE = df
    _JOBS_CACHE_TS = now
    return df.copy()


def _rows_to_excel_bytes(rows: List[Dict[str, Any]], sheet_name: str) -> bytes:
    df = pd.DataFrame(rows)

    for col in ["salary_min", "salary_max", "Доод цалин", "Дээд цалин", "Дундаж цалин"]:
        if col in df.columns:
            df[col] = df[col].apply(_to_float)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]

        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 55)

        money_cols = {"salary_min", "salary_max", "Доод цалин", "Дээд цалин", "Дундаж цалин"}
        for col_idx, cell in enumerate(ws[1], start=1):
            if str(cell.value) in money_cols:
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).number_format = '#,##0"₮"'
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")

    buffer.seek(0)
    return buffer.read()


@register(name="dashboard/main-data", method="POST", required_keys=[], optional_keys={"refresh": False})
async def dashboard_main_data_handler(data: dict):
    refresh = bool(data.get("refresh", False))
    df = _load_main_df(refresh=refresh)
    return {"items": _json_ready_records(df), "count": int(len(df))}


@register(name="dashboard/jobs-data", method="POST", required_keys=[], optional_keys={"limit": 10000, "refresh": False})
async def dashboard_jobs_data_handler(data: dict):
    limit = int(data.get("limit", 10000) or 10000)
    refresh = bool(data.get("refresh", False))
    df = _load_jobs_df(limit=limit, refresh=refresh)
    return {"items": _json_ready_records(df.head(limit)), "count": int(len(df))}


@register(name="download/dashboard-report", method="POST", required_keys=["rows"], optional_keys={"filename": "salary_report.xlsx"})
async def download_dashboard_report_handler(data: dict):
    rows = data.get("rows")
    if not isinstance(rows, list):
        rows = []
    filename = str(data.get("filename") or "salary_report.xlsx")
    excel_bytes = _rows_to_excel_bytes(cast(List[Dict[str, Any]], rows), "Salary_Report")
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@register(name="download/jobs-report", method="POST", required_keys=["rows"], optional_keys={"filename": "jobs_list.xlsx"})
async def download_jobs_report_handler(data: dict):
    rows = data.get("rows")
    if not isinstance(rows, list):
        rows = []
    filename = str(data.get("filename") or "jobs_list.xlsx")
    excel_bytes = _rows_to_excel_bytes(cast(List[Dict[str, Any]], rows), "Jobs_List")
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
