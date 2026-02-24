"""Modern multi-page salary dashboard."""

import io
import json
import os
import re
import ast
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, SupportsFloat, SupportsIndex, TypedDict, cast

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import Input, Output, State, callback, dcc, html, dash_table
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import create_engine

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
N8N_AGENT_URL = os.getenv("N8N_AGENT_URL", "").strip()

COLORS = {
    "bg": "#f8fafc",
    "surface": "#ffffff",
    "text": "#0f172a",
    "muted": "#64748b",
    "primary": "#2563eb",
    "secondary": "#0ea5e9",
    "accent": "#10b981",
    "warning": "#f59e0b",
}

TYPE_LABELS = {
    "function": "Чиг үүрэг",
    "job_level": "Албан тушаалын түвшин",
    "industry": "Үйл ажиллагааны чиглэл/Салбар",
    "techpack_category": "Албан тушаал",
}

ALL_TITLES_VALUE = "__all__"
NUMBER_GROUP_SEPARATOR = os.getenv("NUMBER_GROUP_SEPARATOR", ",").strip() or ","

_MAIN_DATA_CACHE: Optional[pd.DataFrame] = None
_MAIN_DATA_CACHE_TS: float = 0.0
_JOBS_DATA_CACHE: Optional[pd.DataFrame] = None
_JOBS_DATA_CACHE_TS: float = 0.0


class ExperienceBreakdownItem(TypedDict):
    experience_level: str
    min_salary: float
    max_salary: float


def _engine():
    return create_engine(os.getenv("DATABASE_URI", "sqlite:///products.db"), pool_pre_ping=True)


def _load_data_main() -> pd.DataFrame:
    global _MAIN_DATA_CACHE, _MAIN_DATA_CACHE_TS

    now = time.time()
    if _MAIN_DATA_CACHE is not None and (now - _MAIN_DATA_CACHE_TS) < 45:
        return _MAIN_DATA_CACHE.copy()

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

    _MAIN_DATA_CACHE = df
    _MAIN_DATA_CACHE_TS = now
    return df.copy()


def _load_jobs_raw(limit: int = 10000) -> pd.DataFrame:
    global _JOBS_DATA_CACHE, _JOBS_DATA_CACHE_TS

    now = time.time()
    if _JOBS_DATA_CACHE is not None and (now - _JOBS_DATA_CACHE_TS) < 45:
        return _JOBS_DATA_CACHE.head(limit).copy()

    try:
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

        if df.empty:
            return pd.DataFrame()

        _JOBS_DATA_CACHE = df
        _JOBS_DATA_CACHE_TS = now
        return df.copy()
    except Exception:
        return pd.DataFrame()


def _first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _format_mnt(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f} ₮"


def _format_mnt_compact(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{(float(value) / 1_000_000):.1f}M ₮"


def _shorten_label(text: str, max_len: int = 10) -> str:
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= max_len else text[:max_len] + "..."


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font={"size": 16, "color": COLORS["muted"]})
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


def _experience_level_sort_key(level: str) -> float:
    if not level:
        return float("inf")
    match = re.search(r"\d+(?:\.\d+)?", str(level))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return float("inf")
    return float("inf")


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip().replace("\u00a0", " ").replace("₮", "").replace(" ", "")
        if not text:
            return None
        # Handle grouped numbers like 1,234,567 or 1.234.567
        if text.count(",") > 1 and "." not in text:
            text = text.replace(",", "")
        elif text.count(".") > 1 and "," not in text:
            text = text.replace(".", "")
        elif "," in text and "." not in text:
            text = text.replace(",", "")
        value = text
    if not isinstance(value, (str, bytes, bytearray, int, float)) and not hasattr(value, "__float__") and not hasattr(value, "__index__"):
        return None
    try:
        parsed = float(cast(SupportsFloat | SupportsIndex | str | bytes | bytearray, value))
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def _parse_experience_breakdown(raw_value: object) -> List[ExperienceBreakdownItem]:
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return []

    payload = raw_value
    if not isinstance(payload, (list, tuple)):
        text = str(payload).strip()
        if not text:
            return []
        candidates = [text, text.replace('""', '"'), re.sub(r",\s*([\]}])", r"\1", text.replace('""', '"'))]
        payload = None
        for candidate in candidates:
            try:
                payload = json.loads(candidate)
                break
            except (TypeError, ValueError):
                continue

    if not isinstance(payload, (list, tuple)):
        return []

    cleaned: List[ExperienceBreakdownItem] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        level = item.get("education_level") or item.get("experience_level") or item.get("level")
        min_salary = _to_float(item.get("min_salary"))
        max_salary = _to_float(item.get("max_salary"))
        if level is None or min_salary is None or max_salary is None:
            continue
        cleaned.append({"experience_level": str(level), "min_salary": min_salary, "max_salary": max_salary})

    cleaned.sort(key=lambda x: _experience_level_sort_key(x["experience_level"]))
    return cleaned


def _format_grouped_number(value: object) -> str:
    parsed = _to_float(value)
    if parsed is None:
        return ""
    text = f"{parsed:,.0f}"
    if NUMBER_GROUP_SEPARATOR == ".":
        return text.replace(",", ".")
    return text


def _format_jobs_cell_value(value: object) -> object:
    if isinstance(value, str):
        text = value.strip()
        if not text or text == "[]":
            return ""

        if text.startswith("[") or text.startswith("{"):
            parsed: object = value
            try:
                parsed = json.loads(text)
            except (TypeError, ValueError):
                try:
                    parsed = ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    parsed = value

            if parsed is not value:
                return _format_jobs_cell_value(parsed)

        return value

    if isinstance(value, list):
        if not value:
            return ""

        if all(isinstance(item, dict) for item in value):
            parts: List[str] = []
            for item in value:
                d = cast(Dict[str, object], item)
                name = str(d.get("name", "")).strip()
                details = str(d.get("details", d.get("description", ""))).strip()
                importance = str(d.get("importance", "")).strip()

                segment = ""
                if name and details:
                    segment = f"{name}: {details}"
                elif name:
                    segment = name
                elif details:
                    segment = details

                if importance:
                    segment = f"{segment} ({importance})" if segment else importance

                if segment:
                    parts.append(segment)

            if parts:
                return " ; ".join(parts)

        return " ; ".join(str(item) for item in value if str(item).strip())

    if isinstance(value, dict):
        d = cast(Dict[str, object], value)
        if "min" in d and "max" in d and len(d) <= 3:
            return f"min: {d.get('min')} / max: {d.get('max')}"
        return " ; ".join(f"{k}: {v}" for k, v in d.items())

    return value


def _format_experience_breakdown_for_table(raw_value: object) -> str:
    items = _parse_experience_breakdown(raw_value)
    if not items:
        return ""
    return " ; ".join(
        f"{item['experience_level']}: {_format_mnt(item['min_salary'])} - {_format_mnt(item['max_salary'])}" for item in items
    )


def _build_experience_breakdown_table(df: pd.DataFrame, is_all_selected: bool = False):
    if df.empty or "experience_salary_breakdown" not in df.columns:
        return [], []

    records: List[Dict[str, object]] = []
    for _, row in df.iterrows():
        title = row.get("title")
        for item in _parse_experience_breakdown(row.get("experience_salary_breakdown")):
            records.append(
                {
                    "Ажлын ангилал": title,
                    "Туршлага (жил)": item["experience_level"],
                    "Доод цалин": int(item["min_salary"]),
                    "Дээд цалин": int(item["max_salary"]),
                    "_order": _experience_level_sort_key(item["experience_level"]),
                }
            )

    if not records:
        return [], []

    exp_df = pd.DataFrame(records)
    if is_all_selected:
        exp_df = (
            exp_df.groupby("Туршлага (жил)", as_index=False)
            .agg(
                _order=("_order", "min"),
                **{
                    "Доод цалин": ("Доод цалин", "mean"),
                    "Дээд цалин": ("Дээд цалин", "mean"),
                },
            )
            .sort_values("_order")
        )
        exp_df["Доод цалин"] = exp_df["Доод цалин"].round().astype(int)
        exp_df["Дээд цалин"] = exp_df["Дээд цалин"].round().astype(int)
        exp_df = exp_df[["Туршлага (жил)", "Доод цалин", "Дээд цалин"]]
    else:
        exp_df = exp_df.sort_values(["Ажлын ангилал", "_order"]).drop(columns=["_order"])

    for col in ["Доод цалин", "Дээд цалин"]:
        if col in exp_df.columns:
            exp_df[col] = exp_df[col].apply(_format_grouped_number)

    cols = [{"name": col, "id": col} for col in exp_df.columns]
    return exp_df.to_dict("records"), cols


def _latest_per_title(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "created_at" in df.columns and df["created_at"].notna().any():
        ordered = df.sort_values("created_at")
    elif "year" in df.columns and "month" in df.columns:
        ordered = df.sort_values(["year", "month"])
    else:
        ordered = df.copy()
    return ordered.drop_duplicates(subset=["title"], keep="last")


def _safe_type_options(df: pd.DataFrame) -> List[Dict[str, str]]:
    if df.empty or "type" not in df.columns:
        return [{"label": label, "value": key} for key, label in TYPE_LABELS.items()]
    types = [t for t in df["type"].dropna().unique().tolist() if t in TYPE_LABELS]
    if not types:
        types = list(TYPE_LABELS.keys())
    return [{"label": TYPE_LABELS[t], "value": t} for t in types]


def _filter_by_type(df: pd.DataFrame, selected_type: str) -> pd.DataFrame:
    if df.empty or "type" not in df.columns:
        return df
    return df[df["type"] == selected_type].copy()


def _exclude_all_titles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "title" not in df.columns:
        return df
    return df[~df["title"].astype(str).str.startswith("All ")].copy()


def _normalize_title_selection(selected_titles: object, available_titles: List[str]) -> tuple[bool, List[str]]:
    available = [str(title) for title in available_titles if title is not None]
    available_set = set(available)

    if isinstance(selected_titles, str):
        requested = [selected_titles]
    elif isinstance(selected_titles, (list, tuple, set)):
        requested = [str(item) for item in selected_titles if item]
    else:
        requested = []

    if not requested or ALL_TITLES_VALUE in requested:
        return True, available

    cleaned = [title for title in requested if title in available_set and title != ALL_TITLES_VALUE]
    if not cleaned:
        return True, available
    return False, cleaned


def _build_kpi_cards(df: pd.DataFrame) -> List[html.Div]:
    if df.empty:
        return [html.Div(className="kpi-card", children=[html.Div("No data", className="kpi-label"), html.Div("N/A", className="kpi-value")])]

    total_jobs = int(df["job_count"].sum()) if "job_count" in df.columns else 0
    avg_salary = df["average_salary"].mean() if "average_salary" in df.columns else None
    min_salary = df["min_salary"].min() if "min_salary" in df.columns else None
    max_salary = df["max_salary"].max() if "max_salary" in df.columns else None

    return [
        html.Div(className="kpi-card", children=[html.Div("Нийт зар", className="kpi-label"), html.Div(f"{total_jobs:,}", className="kpi-value")]),
        html.Div(className="kpi-card", children=[html.Div("Дундаж цалин", className="kpi-label"), html.Div(_format_mnt_compact(avg_salary), className="kpi-value")]),
        html.Div(className="kpi-card", children=[html.Div("Хамгийн бага", className="kpi-label"), html.Div(_format_mnt_compact(min_salary), className="kpi-value")]),
        html.Div(className="kpi-card", children=[html.Div("Хамгийн их", className="kpi-label"), html.Div(_format_mnt_compact(max_salary), className="kpi-value")]),
    ]


def _apply_chart_style(fig: go.Figure):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": COLORS["text"]},
        transition={"duration": 300, "easing": "cubic-in-out"},
    )


def _render_chat_messages(history: List[Dict[str, object]]) -> List[html.Div]:
    bubbles: List[html.Div] = []
    for item in history:
        role = item.get("role", "assistant")
        content = item.get("content", "")
        pending = bool(item.get("pending"))

        bubble_content: object = content
        if pending:
            bubble_content = html.Div(
                className="typing-indicator",
                children=[
                    html.Span(className="typing-dot"),
                    html.Span(className="typing-dot"),
                    html.Span(className="typing-dot"),
                ],
            )

        bubbles.append(
            html.Div(
                className=f"chat-row {'me' if role == 'user' else 'bot'}",
                children=[html.Div(bubble_content, className=f"chat-bubble {'me' if role == 'user' else 'bot'}")],
            )
        )
    return bubbles

def _extract_chat_text(payload: object) -> Optional[str]:
    if isinstance(payload, str):
        return payload.strip() or None

    if isinstance(payload, dict):
        for key in ["response", "answer", "message", "output", "result", "text", "content", "reply"]:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, (dict, list)):
                nested = _extract_chat_text(value)
                if nested:
                    return nested

        # Fallback: scan all values for nested payload styles (e.g., {"data": {...}})
        for value in payload.values():
            if isinstance(value, (dict, list, str)):
                nested = _extract_chat_text(value)
                if nested:
                    return nested

    if isinstance(payload, list):
        for item in payload:
            nested = _extract_chat_text(item)
            if nested:
                return nested

    return None


def _ask_main_api(message: str) -> Optional[str]:
    endpoints: List[tuple[str, Dict[str, str], tuple[int, int]]] = []

    if N8N_AGENT_URL:
        endpoints.append(
            (
                N8N_AGENT_URL,
                {
                    "session_id": "dashboard-session",
                    "message": message,
                    # Common n8n webhook field names for compatibility
                    "chatInput": message,
                    "query": message,
                },
                (5, 60),
            )
        )

    for url, body, timeout in endpoints:
        try:
            response = requests.post(url, json=body, timeout=timeout)
            if not response.ok:
                continue

            parsed: object
            try:
                parsed = response.json() if response.content else {}
            except ValueError:
                parsed = response.text

            text = _extract_chat_text(parsed)
            if text:
                return text

            fallback = response.text.strip()
            if fallback:
                return fallback
        except requests.RequestException:
            continue

    return None


def _navbar() -> html.Nav:
    return html.Nav(
        className="top-nav",
        children=[
            html.Div("Salary Agent", className="brand"),
            html.Div(
                className="nav-links",
                children=[
                    dcc.Link("Dashboard", href="/", className="nav-link"),
                    dcc.Link("Ажлын зарын жагсаалт", href="/jobs-list", className="nav-link"),
                ],
            ),
        ],
    )


def _dashboard_page_layout() -> html.Div:
    return html.Div(
        className="page",
        children=[
            html.Div(
                className="hero",
                children=[
                    html.H1("Цалингийн шинжилгээний dashboard", className="hero-title"),
                    html.P("Мэдээллийн эх сурвалж: Zangia, Lambda Global, Paylab, Salary Statistics.", className="hero-subtitle"),
                ],
            ),
            dcc.Interval(id="interval-component", interval=5 * 60 * 1000, n_intervals=0),
            dcc.Download(id="excel-download"),
            dcc.Store(
                id="chat-store",
                data=[{"role": "assistant", "content": "Сайн байна уу 👋 Цалингийн мэдээллээр туслая."}],
            ),
            dcc.Store(id="chat-request"),
            dcc.Store(id="chat-open", data=False),
            dcc.Store(id="detail-table-raw", data=[]),
            html.Div(
                className="panel card",
                children=[
                    html.Div("Filters", className="panel-title"),
                    html.Div(
                        className="filter-grid",
                        children=[
                            html.Div(
                                children=[
                                    html.Label("Ангиллын төрөл", className="field-label"),
                                    dcc.Dropdown(
                                        id="type-selector",
                                        options=[{"label": label, "value": key} for key, label in TYPE_LABELS.items()],
                                        value="function",
                                        clearable=False,
                                    ),
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Label("Сонголт", className="field-label"),
                                    dcc.Dropdown(id="title-filter", placeholder="Нэг эсвэл олон ангилал", multi=True, clearable=True),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Loading(
                type="dot",
                color=COLORS["primary"],
                children=html.Div(id="kpi-container", className="kpi-grid"),
            ),
            dcc.Loading(
                type="circle",
                color=COLORS["primary"],
                children=html.Div(
                    className="chart-grid",
                    children=[
                        html.Div(className="card", children=[dcc.Graph(id="salary-bar")]),
                        html.Div(className="card", children=[dcc.Graph(id="salary-range")]),
                        html.Div(className="card", children=[dcc.Graph(id="count-bar")]),
                        html.Div(className="card", children=[dcc.Graph(id="trend-line")]),
                        html.Div(className="card", children=[dcc.Graph(id="source-pie")]),
                        html.Div(className="card", children=[dcc.Graph(id="compare-chart")]),
                    ],
                ),
            ),
            dcc.Loading(
                type="default",
                color=COLORS["primary"],
                children=html.Div(
                    className="table-grid",
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.H3("Туршлагаар цалингийн хүснэгт", className="section-title"),
                                dash_table.DataTable(
                                    id="experience-breakdown-table",
                                    page_size=8,
                                    style_table={"overflowX": "auto", "width": "100%"},
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "8px",
                                        "fontFamily": "Inter, Arial",
                                        "fontSize": "12px",
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "minWidth": "110px",
                                        "maxWidth": "220px",
                                    },
                                    style_data={"lineHeight": "16px"},
                                    style_header={"backgroundColor": "#e2e8f0", "fontWeight": "bold"},
                                ),
                            ],
                        ),
                        html.Div(
                            className="card",
                            children=[
                                html.Div(
                                    className="section-header",
                                    children=[
                                        html.H3("Дэлгэрэнгүй хүснэгт", className="section-title"),
                                        html.Button("Excel татах", id="download-excel", n_clicks=0, className="btn-primary"),
                                    ],
                                ),
                                html.Div(
                                    className="detail-filter-row",
                                    children=[
                                        dcc.Dropdown(
                                            id="detail-title-filter",
                                            options=[],
                                            value=[],
                                            multi=True,
                                            placeholder="Хүснэгтийн дотоод шүүлтүүр: Ажлын ангилал",
                                            className="detail-title-filter",
                                        ),
                                        dcc.Input(
                                            id="detail-search",
                                            type="text",
                                            value="",
                                            placeholder="Хүснэгт дотор хайх...",
                                            className="detail-search-input",
                                        ),
                                    ],
                                ),
                                dash_table.DataTable(
                                    id="detail-table",
                                    page_size=10,
                                    style_table={"overflowX": "auto", "width": "100%"},
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "8px",
                                        "fontFamily": "Inter, Arial",
                                        "fontSize": "12px",
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "minWidth": "110px",
                                        "maxWidth": "240px",
                                    },
                                    style_data={"lineHeight": "16px"},
                                    style_header={"backgroundColor": "#dbeafe", "fontWeight": "bold"},
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            html.Button("💬", id="chat-toggle", className="chat-widget-toggle", n_clicks=0),
            html.Div(
                id="chat-panel",
                className="chat-widget-panel",
                style={"display": "none"},
                children=[
                    html.Div("AI Chat Assistant", className="chat-title"),
                    html.Div(id="chat-output", className="chat-output", children=_render_chat_messages([{"role": "assistant", "content": "Сайн байна уу 👋"}])),
                    dcc.Input(id="chat-input", className="chat-input-line", type="text", placeholder="Асуултаа бичнэ үү...", debounce=False),
                    html.Button("Илгээх", id="chat-send", className="btn-primary chat-send", n_clicks=0),
                ],
            ),
        ],
    )


def _jobs_list_layout() -> html.Div:
    return html.Div(
        className="page",
        children=[
            html.Div(
                className="hero",
                children=[
                    html.H2("Ажлын зарын жагсаалт", className="hero-title"),
                    html.P("Шинэчлэгдсэн, шүүх боломжтой ажлын зарын жагсаалт (beta).", className="hero-subtitle"),
                ],
            ),
            dcc.Interval(id="jobs-interval", interval=120000, n_intervals=0),
            dcc.Download(id="jobs-excel-download"),
            html.Div(
                className="card jobs-filter-card",
                children=[
                    html.Div(
                        className="jobs-filter-grid",
                        children=[
                            html.Div(
                                children=[
                                    html.Label("Хайлт", className="field-label"),
                                    dcc.Input(
                                        id="jobs-search",
                                        type="text",
                                        placeholder="Гарчиг, компани, requirement...",
                                        className="jobs-search-input",
                                    ),
                                ]
                            ),
                            html.Div(children=[html.Label("Эх сурвалж", className="field-label"), dcc.Dropdown(id="jobs-source", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Функц", className="field-label"), dcc.Dropdown(id="jobs-function", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Салбар", className="field-label"), dcc.Dropdown(id="jobs-industry", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Түвшин", className="field-label"), dcc.Dropdown(id="jobs-level", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Компани", className="field-label"), dcc.Dropdown(id="jobs-company", options=[], placeholder="Бүгд", clearable=True)]),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    dcc.Loading(
                        id="jobs-list-loading",
                        type="circle",
                        color=COLORS["primary"],
                        className="jobs-list-loading",
                        children=[
                            html.Div(
                                className="section-header",
                                children=[
                                    html.Div(id="jobs-count", className="jobs-count", children="Нийт мөр: 0"),
                                    html.Button("Excel татах", id="download-jobs-excel", n_clicks=0, className="btn-primary"),
                                ],
                            ),
                            dash_table.DataTable(
                                id="jobs-table",
                                page_action="none",
                                sort_action="native",
                                filter_action="none",
                                style_table={"overflowX": "auto", "overflowY": "visible", "maxHeight": "none"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "8px",
                                    "fontFamily": "Inter, Arial",
                                    "maxWidth": "420px",
                                    "whiteSpace": "pre-line",
                                    "wordBreak": "break-word",
                                    "height": "auto",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"column_id": "salary_min"},
                                        "minWidth": "130px",
                                        "width": "130px",
                                        "maxWidth": "130px",
                                        "whiteSpace": "nowrap",
                                        "textAlign": "right",
                                    },
                                    {
                                        "if": {"column_id": "salary_max"},
                                        "minWidth": "130px",
                                        "width": "130px",
                                        "maxWidth": "130px",
                                        "whiteSpace": "nowrap",
                                        "textAlign": "right",
                                    },
                                ],
                                style_header={
                                    "backgroundColor": "#dbeafe",
                                    "fontWeight": "bold",
                                    "whiteSpace": "pre-line",
                                    "wordBreak": "break-word",
                                },
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


app = dash.Dash(
    __name__,
    title="Salary Analysis Agent",
    suppress_callback_exceptions=True,
    assets_folder=str(ASSETS_DIR),
)
server = app.server

app.layout = html.Div(
    className="app-root",
    children=[
        dcc.Location(id="url"),
        _navbar(),
        html.Main(id="page-content", className="page-container"),
    ],
)


@callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: Optional[str]):
    if pathname == "/jobs-list":
        return _jobs_list_layout()
    return _dashboard_page_layout()


@callback(Output("chat-open", "data"), Input("chat-toggle", "n_clicks"), State("chat-open", "data"), prevent_initial_call=True)
def toggle_chat(n_clicks: int, is_open: Optional[bool]):
    return not bool(is_open)


@callback(Output("chat-panel", "style"), Input("chat-open", "data"))
def set_chat_visibility(is_open: Optional[bool]):
    base = {
        "position": "fixed",
        "right": "24px",
        "bottom": "88px",
        "width": "380px",
        "maxWidth": "calc(100vw - 24px)",
        "display": "none",
        "zIndex": 1200,
    }
    if is_open:
        base["display"] = "flex"
        base["flexDirection"] = "column"
    return base


@callback(
    Output("chat-store", "data"),
    Output("chat-output", "children"),
    Output("chat-input", "value"),
    Output("chat-request", "data"),
    Output("chat-send", "disabled"),
    Output("chat-input", "disabled"),
    Input("chat-send", "n_clicks"),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def chat_respond(n_clicks: int, n_submit: Optional[int], message: Optional[str], history: Optional[List[Dict[str, object]]]):
    history = history or []
    has_pending = any(bool(item.get("pending")) for item in history)

    if has_pending:
        return history, _render_chat_messages(history), message or "", None, True, True

    if not message or not message.strip():
        return history, _render_chat_messages(history), "", None, False, False

    user_message = message.strip()
    updated = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": "...", "pending": True},
    ]
    request_payload = {"id": uuid.uuid4().hex, "message": user_message}
    return updated, _render_chat_messages(updated), "", request_payload, True, True


@callback(
    Output("chat-store", "data", allow_duplicate=True),
    Output("chat-output", "children", allow_duplicate=True),
    Output("chat-send", "disabled", allow_duplicate=True),
    Output("chat-input", "disabled", allow_duplicate=True),
    Input("chat-request", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def fetch_chat_response(request_payload: Optional[Dict[str, str]], history: Optional[List[Dict[str, object]]]):
    history = history or []
    if not request_payload or not request_payload.get("message"):
        return history, _render_chat_messages(history), False, False

    answer = _ask_main_api(request_payload["message"])
    message = answer if answer else "Уучлаарай, одоогоор хариу авах боломжгүй байна."

    updated: List[Dict[str, object]] = []
    replaced = False
    for item in history:
        if bool(item.get("pending")) and not replaced:
            updated.append({"role": "assistant", "content": message})
            replaced = True
            continue
        clean_item = {k: v for k, v in item.items() if k != "pending"}
        updated.append(clean_item)

    if not replaced:
        updated.append({"role": "assistant", "content": message})

    return updated, _render_chat_messages(updated), False, False


@callback(
    Output("jobs-source", "options"),
    Output("jobs-function", "options"),
    Output("jobs-industry", "options"),
    Output("jobs-level", "options"),
    Output("jobs-company", "options"),
    Output("jobs-count", "children"),
    Output("jobs-table", "data"),
    Output("jobs-table", "columns"),
    Input("jobs-search", "value"),
    Input("jobs-source", "value"),
    Input("jobs-function", "value"),
    Input("jobs-industry", "value"),
    Input("jobs-level", "value"),
    Input("jobs-company", "value"),
    Input("jobs-interval", "n_intervals"),
)
def update_jobs_list(
    search: Optional[str],
    source: Optional[str],
    selected_function: Optional[str],
    selected_industry: Optional[str],
    selected_level: Optional[str],
    selected_company: Optional[str],
    n_intervals: int,
):
    df = _load_jobs_raw(limit=10000)
    if df.empty:
        return [], [], [], [], [], "Нийт мөр: 0", [], []

    source_col = _first_existing_col(df, ["source_job", "source", "platform", "site_name", "website"])
    function_col = _first_existing_col(df, ["job_function"])
    industry_col = _first_existing_col(df, ["job_industry"])
    level_col = _first_existing_col(df, ["job_level"])
    company_col = _first_existing_col(df, ["company_name"])

    # Show requested job_classification_output columns.
    requested_columns = [
        "title",
        "source_job",
        "company_name",
        "job_level",
        "experience_level",
        "education_level",
        "salary_min",
        "salary_max",
        "requirement_reasoning",
        "requirements",
        "benefits_reasoning",
        "benefits",
        "job_function",
        "job_industry",
        "job_techpack_category",
    ]
    ordered_cols = [c for c in requested_columns if c in df.columns]
    if not ordered_cols:
        ordered_cols = df.columns.tolist()
    view_df = df[ordered_cols].copy()

    def _option_list(frame: pd.DataFrame, col: Optional[str]) -> List[Dict[str, str]]:
        if not col or col not in frame.columns:
            return []
        return [
            {"label": str(v), "value": str(v)}
            for v in sorted(frame[col].dropna().astype(str).unique().tolist())
            if str(v).strip()
        ]

    source_options = _option_list(view_df, source_col)
    function_options = _option_list(view_df, function_col)
    industry_options = _option_list(view_df, industry_col)
    level_options = _option_list(view_df, level_col)
    company_options = _option_list(view_df, company_col)

    def _eq_filter(frame: pd.DataFrame, col: Optional[str], value: Optional[str]) -> pd.DataFrame:
        if not value or not col or col not in frame.columns:
            return frame
        return frame[frame[col].astype(str) == str(value)]

    view_df = _eq_filter(view_df, source_col, source)
    view_df = _eq_filter(view_df, function_col, selected_function)
    view_df = _eq_filter(view_df, industry_col, selected_industry)
    view_df = _eq_filter(view_df, level_col, selected_level)
    view_df = _eq_filter(view_df, company_col, selected_company)

    # Convert values for table rendering (human-readable).
    for col in view_df.columns:
        view_df[col] = view_df[col].map(_format_jobs_cell_value)

    if search and search.strip():
        q = search.strip().lower()
        mask = pd.Series([False] * len(view_df), index=view_df.index)
        for col in view_df.columns:
            mask = mask | view_df[col].astype(str).str.lower().str.contains(q, na=False)
        view_df = view_df[mask]

    for col in ["salary_min", "salary_max"]:
        if col in view_df.columns:
            view_df[col] = view_df[col].apply(_format_grouped_number)

    header_map = {
        "title": "Гарчиг",
        "job_function": "Функц",
        "job_industry": "Салбар",
        "job_techpack_category": "Techpack",
        "job_level": "Түвшин",
        "experience_level": "Туршлага",
        "education_level": "Боловсрол",
        "salary_min": "Мин цалин",
        "salary_max": "Макс цалин",
        "company_name": "Компани",
        "requirement_reasoning": "Requirement reasoning",
        "requirements": "Requirements",
        "benefits_reasoning": "Benefits reasoning",
        "benefits": "Benefits",
        "source_job": "Эх сурвалж",
    }

    columns = [{"name": header_map.get(col, col), "id": col} for col in view_df.columns]
    count_text = f"Нийт мөр: {len(view_df):,}"
    return (
        source_options,
        function_options,
        industry_options,
        level_options,
        company_options,
        count_text,
        view_df.to_dict("records"),
        columns,
    )


@callback(
    Output("jobs-excel-download", "data"),
    Input("download-jobs-excel", "n_clicks"),
    State("jobs-table", "data"),
    prevent_initial_call=True,
)
def download_jobs_excel(n_clicks: int, table_data: Optional[List[Dict[str, object]]]):
    if not n_clicks or not table_data:
        return dash.no_update

    df = pd.DataFrame(table_data)
    if df.empty:
        return dash.no_update

    for col in ["salary_min", "salary_max"]:
        if col in df.columns:
            df[col] = df[col].apply(_to_float)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Jobs_List")
        ws = writer.sheets["Jobs_List"]

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

        for col_idx, cell in enumerate(ws[1], start=1):
            if cell.value in {"salary_min", "salary_max"}:
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).number_format = "#,##0\"₮\""
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")

    buffer.seek(0)
    return dcc.send_bytes(buffer.read(), "jobs_list.xlsx")


@callback(
    Output("title-filter", "options"),
    Output("title-filter", "value"),
    Input("type-selector", "value"),
    Input("interval-component", "n_intervals"),
)
def update_title_options(selected_type: str, n_intervals: int):
    if not selected_type:
        return [], []
    df = _exclude_all_titles(_filter_by_type(_load_data_main(), selected_type))
    df = _latest_per_title(df)
    if df.empty:
        return [], []
    options = [{"label": "Бүгд", "value": ALL_TITLES_VALUE}] + [{"label": title, "value": title} for title in sorted(df["title"].dropna().unique().tolist())]
    return options, [ALL_TITLES_VALUE]


@callback(
    Output("kpi-container", "children"),
    Output("salary-bar", "figure"),
    Output("salary-range", "figure"),
    Output("count-bar", "figure"),
    Output("trend-line", "figure"),
    Output("source-pie", "figure"),
    Output("compare-chart", "figure"),
    Output("experience-breakdown-table", "data"),
    Output("experience-breakdown-table", "columns"),
    Output("detail-table", "data"),
    Output("detail-table", "columns"),
    Output("detail-table-raw", "data"),
    Output("detail-title-filter", "options"),
    Output("detail-title-filter", "value"),
    Input("type-selector", "value"),
    Input("title-filter", "value"),
    Input("interval-component", "n_intervals"),
)
def update_dashboard(selected_type: str, selected_title: object, n_intervals: int):
    if not selected_type:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return _build_kpi_cards(pd.DataFrame()), empty, empty, empty, empty, empty, empty, [], [], [], [], [], [], []

    df_all = _exclude_all_titles(_filter_by_type(_load_data_main(), selected_type))
    if df_all.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return _build_kpi_cards(df_all), empty, empty, empty, empty, empty, empty, [], [], [], [], [], [], []

    df_latest = _latest_per_title(df_all)
    display_label = TYPE_LABELS.get(selected_type, "Төрөл")
    available_titles = df_all["title"].dropna().astype(str).unique().tolist()
    is_all_selected, selected_titles = _normalize_title_selection(selected_title, available_titles)

    if is_all_selected:
        df_selected = df_all.copy()
        df_selected_latest = df_latest.copy()
    else:
        df_selected = df_all[df_all["title"].isin(selected_titles)].copy()
        df_selected_latest = df_latest[df_latest["title"].isin(selected_titles)].copy()

    kpis = _build_kpi_cards(df_selected_latest)
    if df_selected_latest.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return kpis, empty, empty, empty, empty, empty, empty, [], [], [], [], [], [], []

    bar_df = df_selected_latest.groupby("title", as_index=False)["average_salary"].mean()
    bar_df["title_short"] = bar_df["title"].apply(_shorten_label)
    bar_fig = px.bar(
        bar_df,
        y="title_short",
        x="average_salary",
        orientation="h",
        title=f"Сарын дундаж цалин ({display_label})",
        labels={"title_short": display_label, "average_salary": "Дундаж цалин (₮)"},
        color_discrete_sequence=[COLORS["primary"]],
        hover_data={"title": True, "title_short": False, "average_salary": True},
    )
    bar_fig.update_layout(height=420, yaxis={"automargin": True, "categoryorder": "total ascending"})
    _apply_chart_style(bar_fig)

    range_df = df_selected_latest.groupby("title", as_index=False).agg(
        min_salary=("min_salary", "min"),
        max_salary=("max_salary", "max"),
        average_salary=("average_salary", "mean"),
    )
    range_df = range_df.sort_values("average_salary", ascending=False)
    range_df["title_short"] = range_df["title"].apply(_shorten_label)
    range_fig = go.Figure()

    line_x: List[float | None] = []
    line_y: List[str | None] = []
    for _, row in range_df.iterrows():
        line_x.extend([float(row["min_salary"]), float(row["max_salary"]), None])
        line_y.extend([str(row["title_short"]), str(row["title_short"]), None])

    range_fig.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            line={"color": "#94a3b8", "width": 2},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    range_fig.add_trace(
        go.Scatter(
            x=range_df["min_salary"],
            y=range_df["title_short"],
            mode="markers",
            name="Доод",
            marker={"size": 9, "color": "#5b8a3c", "symbol": "circle"},
            customdata=range_df[["title"]],
            hovertemplate="%{customdata[0]}<br>Доод: %{x:,.0f} ₮<extra></extra>",
        )
    )
    range_fig.add_trace(
        go.Scatter(
            x=range_df["average_salary"],
            y=range_df["title_short"],
            mode="markers",
            name="Дундаж",
            marker={"size": 10, "color": "#3b82f6", "symbol": "diamond"},
            customdata=range_df[["title"]],
            hovertemplate="%{customdata[0]}<br>Дундаж: %{x:,.0f} ₮<extra></extra>",
        )
    )
    range_fig.add_trace(
        go.Scatter(
            x=range_df["max_salary"],
            y=range_df["title_short"],
            mode="markers",
            name="Дээд",
            marker={"size": 9, "color": "#dc2626", "symbol": "circle"},
            customdata=range_df[["title"]],
            hovertemplate="%{customdata[0]}<br>Дээд: %{x:,.0f} ₮<extra></extra>",
        )
    )

    range_fig.update_layout(
        title=f"Цалингийн хүрээ (Доод • Дундаж ◆ Дээд •)",
        height=520,
        xaxis_title="₮",
        yaxis={"automargin": True, "categoryorder": "array", "categoryarray": range_df["title_short"].tolist()[::-1]},
        margin={"l": 280, "r": 24, "t": 60, "b": 45},
    )
    _apply_chart_style(range_fig)

    if "job_count" in df_selected_latest.columns:
        count_df = df_selected_latest.groupby("title", as_index=False)["job_count"].sum()
        count_df["title_short"] = count_df["title"].apply(_shorten_label)
        count_fig = px.bar(
            count_df,
            y="title_short",
            x="job_count",
            orientation="h",
            title=f"Ажлын байрны тоо ({display_label})",
            labels={"title_short": display_label, "job_count": "Ажлын байр"},
            color_discrete_sequence=[COLORS["warning"]],
            hover_data={"title": True, "title_short": False, "job_count": True},
        )
        count_fig.update_layout(height=420, yaxis={"automargin": True, "categoryorder": "total ascending"})
        _apply_chart_style(count_fig)
    else:
        count_fig = _empty_figure("Зарын тооны өгөгдөл алга")

    if "period" in df_selected.columns and df_selected["period"].notna().any():
        trend_df = df_selected.groupby("period", as_index=False)["average_salary"].mean()
        trend_df["period_date"] = pd.to_datetime(trend_df["period"].astype(str) + "-01", errors="coerce")
        trend_df = trend_df[trend_df["period_date"].notna()].copy().sort_values("period_date")
        trend_df["average_salary_m"] = trend_df["average_salary"] / 1_000_000

        trend_fig = px.line(
            trend_df,
            x="period_date",
            y="average_salary_m",
            markers=True,
            title="Дундаж цалингийн динамик, сараар",
            labels={"period_date": "Сар", "average_salary_m": "Дундаж цалин (сая ₮)"},
        )
        trend_fig.update_traces(
            hovertemplate="%{x|%b %Y}<br>Дундаж цалин: %{y:.2f} сая ₮<extra></extra>"
        )
        trend_fig.update_xaxes(tickformat="%b %Y")
        trend_fig.update_yaxes(tickformat=",.2f")
        _apply_chart_style(trend_fig)
    else:
        trend_fig = _empty_figure("Цаг хугацааны өгөгдөл алга")

    if "zangia_count" in df_selected_latest.columns and "lambda_count" in df_selected_latest.columns:
        source_total = {"Zangia": int(df_selected_latest["zangia_count"].sum()), "Lambda Global": int(df_selected_latest["lambda_count"].sum())}
        source_fig = px.pie(names=list(source_total.keys()), values=list(source_total.values()), hole=0.55, title="Мэдээллийн эх сурвалжийн харьцаа", color_discrete_sequence=[COLORS["primary"], COLORS["secondary"]])
        _apply_chart_style(source_fig)
    else:
        source_fig = _empty_figure("Эх сурвалжийн өгөгдөл алга")

    compare_df = (
        df_selected_latest.groupby("title", as_index=False)
        .agg(min_salary=("min_salary", "min"), average_salary=("average_salary", "mean"), max_salary=("max_salary", "max"))
        .sort_values("average_salary", ascending=False)
        .head(12)
    )
    if compare_df.empty:
        compare_fig = _empty_figure("Харьцуулах өгөгдөл алга")
    else:
        compare_df["title_short"] = compare_df["title"].apply(_shorten_label)
        compare_long = compare_df.melt(id_vars=["title"], value_vars=["min_salary", "average_salary", "max_salary"], var_name="metric", value_name="salary")
        compare_long["metric"] = compare_long["metric"].map({"min_salary": "Доод", "average_salary": "Дундаж", "max_salary": "Дээд"})
        compare_long = compare_long.merge(compare_df[["title", "title_short"]], on="title", how="left")
        compare_fig = px.bar(
            compare_long,
            x="title_short",
            y="salary",
            color="metric",
            barmode="group",
            title=f"Сонгосон ангиллуудын цалингийн харьцуулалт ({display_label})",
            labels={"title_short": display_label, "salary": "Цалин (₮)", "metric": "Үзүүлэлт"},
            color_discrete_map={"Доод": "#93c5fd", "Дундаж": COLORS["primary"], "Дээд": "#1d4ed8"},
            custom_data=["title"],
        )
        compare_fig.update_traces(hovertemplate="%{customdata[0]}<br>%{fullData.name}: %{y:,.0f} ₮<extra></extra>")
        compare_fig.update_layout(xaxis_tickangle=-20)
        _apply_chart_style(compare_fig)

    experience_data, experience_columns = _build_experience_breakdown_table(df_selected_latest, is_all_selected=is_all_selected)

    table_df = df_selected_latest.copy()
    if "experience_salary_breakdown" in table_df.columns:
        table_df["experience_salary_breakdown"] = table_df["experience_salary_breakdown"].apply(_format_experience_breakdown_for_table)

    table_df = table_df.rename(
        columns={
            "title": "Ажлын ангилал",
            "min_salary": "Доод цалин",
            "max_salary": "Дээд цалин",
            "average_salary": "Дундаж цалин",
            "job_count": "Зарын тоо",
            "zangia_count": "Zangia",
            "lambda_count": "Lambda",
            "experience_salary_breakdown": "Туршлагаар цалин",
        }
    )
    wanted = ["Ажлын ангилал", "Доод цалин", "Дээд цалин", "Дундаж цалин", "Зарын тоо", "Zangia", "Lambda"]
    table_columns = [{"name": c, "id": c} for c in wanted if c in table_df.columns]

    for col in ["Доод цалин", "Дээд цалин", "Дундаж цалин", "Зарын тоо", "Zangia", "Lambda"]:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(_format_grouped_number)

    table_data = table_df[[c["id"] for c in table_columns]].to_dict("records")

    title_options: List[Dict[str, str]] = []
    if "Ажлын ангилал" in table_df.columns:
        title_options = [
            {"label": str(t), "value": str(t)}
            for t in sorted(table_df["Ажлын ангилал"].dropna().astype(str).unique().tolist())
        ]

    return (
        kpis,
        bar_fig,
        range_fig,
        count_fig,
        trend_fig,
        source_fig,
        compare_fig,
        experience_data,
        experience_columns,
        table_data,
        table_columns,
        table_data,
        title_options,
        [],
    )


@callback(
    Output("detail-table", "data", allow_duplicate=True),
    Input("detail-table-raw", "data"),
    Input("detail-title-filter", "value"),
    Input("detail-search", "value"),
    prevent_initial_call=True,
)
def filter_detail_table_rows(
    raw_data: Optional[List[Dict[str, object]]],
    selected_titles: Optional[List[str]],
    search_text: Optional[str],
):
    rows = raw_data or []

    if selected_titles:
        selected = {str(v) for v in selected_titles if v}
        rows = [row for row in rows if str(row.get("Ажлын ангилал", "")) in selected]

    if search_text and search_text.strip():
        q = search_text.strip().lower()
        filtered: List[Dict[str, object]] = []
        for row in rows:
            text = " ".join(str(v) for v in row.values()).lower()
            if q in text:
                filtered.append(row)
        rows = filtered

    return rows


@callback(
    Output("excel-download", "data"),
    Input("download-excel", "n_clicks"),
    State("detail-table", "data"),
    prevent_initial_call=True,
)
def download_excel(n_clicks: int, table_data: List[Dict[str, object]]):
    if not table_data:
        return dash.no_update

    df = pd.DataFrame(table_data)
    for col in ["Доод цалин", "Дээд цалин", "Дундаж цалин", "Зарын тоо", "Zangia", "Lambda"]:
        if col in df.columns:
            df[col] = df[col].apply(_to_float)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Salary_Report")
        ws = writer.sheets["Salary_Report"]

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
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 40)

        money_cols = {"Доод цалин", "Дээд цалин", "Дундаж цалин"}
        for col_idx, cell in enumerate(ws[1], start=1):
            if cell.value in money_cols:
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).number_format = "#,##0\"₮\""
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")

    buffer.seek(0)
    return dcc.send_bytes(buffer.read(), "salary_report.xlsx")


if __name__ == "__main__":
    app.run(debug=True, port="8006")

r'''

# ── Database helper ─────────────────────────────────────────────────────────


def _engine():
    return create_engine(
        os.getenv("DATABASE_URI", "sqlite:///products.db"),
        pool_pre_ping=True,
    )


def _load_data_main() -> pd.DataFrame:
    """Load salary calculation output data from database."""
    engine = _engine()
    query = "SELECT * FROM salary_calculation_output ORDER BY created_at DESC"
    df = pd.read_sql(query, engine)

    # Ensure numeric columns are properly typed
    numeric_cols = [
        "min_salary",
        "max_salary",
        "average_salary",
        "job_count",
        "zangia_count",
        "lambda_count",
        "year",
        "month",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    # Create period column for time-based analysis
    if "year" in df.columns and "month" in df.columns:
        df["period"] = df.apply(
            lambda x: f"{int(x['year'])}-{int(x['month']):02d}"
            if pd.notna(x["year"]) and pd.notna(x["month"])
            else None,
            axis=1,
        )

    # Fill NaN counts with 0 for accurate aggregations
    count_cols = ["job_count", "zangia_count", "lambda_count"]
    for col in count_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    return df


def _load_all_of_raw_data() -> pd.DataFrame:
    """Load all raw job data from database for detailed analysis."""
    engine = _engine()
    query = "SELECT * FROM job_classification_output ORDER BY created_at DESC"
    df = pd.read_sql(query, engine)
    return df


# ── Colors & Styles ─────────────────────────────────────────────────────────

COLORS = {
    "bg": "#F5F7FA",
    "card": "#FFFFFF",
    "primary": "#3B82F6",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "danger": "#EF4444",
    "dark": "#1E293B",
    "text": "#334155",
    "muted": "#94A3B8",
}

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "16px",
    "padding": "24px",
    "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)",
    "marginBottom": "24px",
}

KPI_STYLE = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "16px",
    "padding": "24px",
    "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)",
    "textAlign": "center",
    "flex": "1",
    "minWidth": "200px",
    "border": f"1px solid {COLORS['muted']}20",
}

TYPE_LABELS = {
    "function": "Ажлын ангилал",
    "job_level": "Албан тушаалын түвшин",
    "industry": "Ажлын чиглэл",
    "techpack_category": "Ажлын байрын төрөл",
}

ALL_TITLES_VALUE = "__all__"


class ExperienceBreakdownItem(TypedDict):
    experience_level: str
    min_salary: float
    max_salary: float


# ── Helpers ─────────────────────────────────────────────────────────────────


def _format_mnt(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f} ₮"


def _format_mnt_compact(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{(float(value) / 1_000_000):.1f}M MNT"


def _shorten_label(text: str, max_len: int = 28) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16, "color": COLORS["muted"]},
    )
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


def _experience_level_sort_key(level: str) -> float:
    if not level:
        return float("inf")
    match = re.search(r"\d+(?:\.\d+)?", str(level))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return float("inf")
    return float("inf")


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None

    if not isinstance(value, (str, bytes, bytearray, int, float)) and not hasattr(value, "__float__") and not hasattr(value, "__index__"):
        return None

    try:
        parsed = float(cast(SupportsFloat | SupportsIndex | str | bytes | bytearray, value))
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def _parse_experience_breakdown(raw_value: object) -> List[ExperienceBreakdownItem]:
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return []

    payload = raw_value
    if not isinstance(payload, (list, tuple)):
        text = str(payload).strip()
        if not text:
            return []

        candidates = [text]
        candidates.append(text.replace('""', '"'))
        candidates.append(re.sub(r",\s*([\]}])", r"\1", text.replace('""', '"')))

        payload = None
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                payload = parsed
                break
            except (TypeError, ValueError):
                continue

    if not isinstance(payload, (list, tuple)):
        return []

    cleaned: List[ExperienceBreakdownItem] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        typed_item = item if isinstance(item, dict) else {}
        level = typed_item.get("education_level") or typed_item.get("experience_level") or typed_item.get("level")
        min_salary = _to_float(typed_item.get("min_salary"))
        max_salary = _to_float(typed_item.get("max_salary"))
        if level is None or min_salary is None or max_salary is None:
            continue
        cleaned.append(
            {
                "experience_level": str(level),
                "min_salary": min_salary,
                "max_salary": max_salary,
            }
        )

    cleaned.sort(key=lambda x: _experience_level_sort_key(x["experience_level"]))
    return cleaned


def _format_experience_breakdown_for_table(raw_value: object) -> str:
    items = _parse_experience_breakdown(raw_value)
    if not items:
        return ""
    parts = [
        f"{item['experience_level']}: {_format_mnt(item['min_salary'])} - {_format_mnt(item['max_salary'])}"
        for item in items
    ]
    return " ; ".join(parts)


def _build_experience_breakdown_table(df: pd.DataFrame, is_all_selected: bool = False):
    if df.empty or "experience_salary_breakdown" not in df.columns:
        return [], []

    records: List[Dict[str, object]] = []
    for _, row in df.iterrows():
        title = row.get("title")
        for item in _parse_experience_breakdown(row.get("experience_salary_breakdown")):
            records.append(
                {
                    "Ажлын ангилал": title,
                    "Туршлага (жил)": item["experience_level"],
                    "Доод цалин": int(item["min_salary"]),
                    "Дээд цалин": int(item["max_salary"]),
                    "_order": _experience_level_sort_key(item["experience_level"]),
                }
            )

    if not records:
        return [], []

    exp_df = pd.DataFrame(records)

    if is_all_selected:
        exp_df = (
            exp_df.groupby("Туршлага (жил)", as_index=False)
            .agg(
                _order=("_order", "min"),
                **{
                    "Доод цалин": ("Доод цалин", "mean"),
                    "Дээд цалин": ("Дээд цалин", "mean"),
                },
            )
            .sort_values("_order")
        )
        exp_df["Доод цалин"] = exp_df["Доод цалин"].round().astype(int)
        exp_df["Дээд цалин"] = exp_df["Дээд цалин"].round().astype(int)
        exp_df = exp_df[["Туршлага (жил)", "Доод цалин", "Дээд цалин"]]
    else:
        exp_df = exp_df.sort_values(["Ажлын ангилал", "_order"]).drop(columns=["_order"])

    columns = [{"name": col, "id": col} for col in exp_df.columns]
    return exp_df.to_dict("records"), columns


def _latest_per_title(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "created_at" in df.columns and df["created_at"].notna().any():
        df_sorted = df.sort_values("created_at")
    elif "year" in df.columns and "month" in df.columns:
        df_sorted = df.sort_values(["year", "month"])
    else:
        df_sorted = df.copy()

    return df_sorted.drop_duplicates(subset=["title"], keep="last")


def _safe_type_options(df: pd.DataFrame) -> List[Dict[str, str]]:
    if df.empty or "type" not in df.columns:
        return [{"label": label, "value": key} for key, label in TYPE_LABELS.items()]
    types = [t for t in df["type"].dropna().unique().tolist() if t in TYPE_LABELS]
    if not types:
        types = list(TYPE_LABELS.keys())
    return [{"label": TYPE_LABELS[t], "value": t} for t in types]


def _filter_by_type(df: pd.DataFrame, selected_type: str) -> pd.DataFrame:
    if df.empty or "type" not in df.columns:
        return df
    return df[df["type"] == selected_type].copy()


def _exclude_all_titles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "title" not in df.columns:
        return df
    return df[~df["title"].astype(str).str.startswith("All ")].copy()


def _normalize_title_selection(selected_titles: object, available_titles: List[str]) -> tuple[bool, List[str]]:
    available = [str(title) for title in available_titles if title is not None]
    available_set = set(available)

    if isinstance(selected_titles, str):
        requested = [selected_titles]
    elif isinstance(selected_titles, (list, tuple, set)):
        requested = [str(item) for item in selected_titles if item]
    else:
        requested = []

    if not requested or ALL_TITLES_VALUE in requested:
        return True, available

    cleaned = [title for title in requested if title in available_set and title != ALL_TITLES_VALUE]
    if not cleaned:
        return True, available

    return False, cleaned


def _build_kpi_cards(df: pd.DataFrame) -> List[html.Div]:
    salary_kpi_style = {
        **KPI_STYLE,
        "backgroundColor": "#EAF4E3",
        "border": "1px solid #D8E8CC",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    }
    count_kpi_style = {
        **KPI_STYLE,
        "backgroundColor": "#EEF2F7",
        "border": "1px solid #DEE5EF",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    }

    if df.empty:
        return [
            html.Div(
                [
                    html.H3("N/A", style={"color": COLORS["dark"], "margin": 0}),
                    html.P("No data", style={"color": COLORS["muted"], "margin": 0}),
                ],
                style=salary_kpi_style,
            )
        ]

    total_jobs = int(df["job_count"].sum()) if "job_count" in df.columns else 0
    avg_salary = df["average_salary"].mean() if "average_salary" in df.columns else None
    min_salary = df["min_salary"].min() if "min_salary" in df.columns else None
    max_salary = df["max_salary"].max() if "max_salary" in df.columns else None

    return [
        html.Div(
            [
                html.H3(_format_mnt_compact(avg_salary), style={"color": "#D97706", "margin": 0, "fontWeight": "800"}),
                html.P("Сарын дундаж цалин", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=salary_kpi_style,
        ),
        html.Div(
            [
                html.H3(_format_mnt_compact(min_salary), style={"color": "#D97706", "margin": 0, "fontWeight": "800"}),
                html.P("Хамгийн бага цалин", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=salary_kpi_style,
        ),
        html.Div(
            [
                html.H3(_format_mnt_compact(max_salary), style={"color": "#D97706", "margin": 0, "fontWeight": "800"}),
                html.P("Хамгийн өндөр цалин", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=salary_kpi_style,
        ),
        html.Div(
            [
                html.H3(f"{total_jobs:,}", style={"color": COLORS["dark"], "margin": 0}),
                html.P("Хамрагдсан ажлын байр", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=count_kpi_style,
        ),
    ]


def _render_chat(history: List[Dict[str, object]]) -> List[html.Div]:
    if not history:
        return [
            html.Div(
                "Chat history is empty. Start a conversation.",
                style={"color": COLORS["muted"], "fontStyle": "italic"},
            )
        ]
    items = []
    for item in history:
        is_user = item.get("role") == "user"
        is_pending = bool(item.get("pending"))
        bubble_color = COLORS["primary"] if is_user else COLORS["card"]
        text_color = "white" if is_user else COLORS["text"]
        align = "flex-end" if is_user else "flex-start"
        role_label = "Та" if is_user else "AI туслах"
        content = item.get("content", "")

        if is_pending and not is_user:
            content_component = html.Div(
                [
                    html.Span(className="typing-dot"),
                    html.Span(className="typing-dot"),
                    html.Span(className="typing-dot"),
                ],
                className="typing-indicator",
            )
        else:
            content_component = html.Div(
                str(content),
                style={
                    "whiteSpace": "pre-wrap",
                    "lineHeight": "1.4",
                    "color": text_color,
                },
            )

        items.append(
            html.Div(
                [
                    html.Small(
                        role_label,
                        style={
                            "display": "block",
                            "fontWeight": "bold",
                            "marginBottom": "4px",
                            "color": "#E2E8F0" if is_user else COLORS["muted"],
                        },
                    ),
                    content_component,
                ],
                style={
                    "alignSelf": align,
                    "backgroundColor": bubble_color,
                    "padding": "10px 12px",
                    "borderRadius": "14px",
                    "marginBottom": "10px",
                    "maxWidth": "85%",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
                    "border": "1px solid #E2E8F0" if not is_user else "none",
                },
            )
        )
    return items


# ── App ─────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    title="Salary Analysis Agent",
    suppress_callback_exceptions=True,
)
server = app.server

# ── Layout ──────────────────────────────────────────────────────────────────

app.layout = html.Div(
    className="dashboard-root",
    style={"backgroundColor": COLORS["bg"], "padding": "32px", "fontFamily": "Arial, sans-serif"},
    children=[
        html.H1("Цалингийн шинжилгээний систем", style={"color": COLORS["dark"], "marginBottom": "8px"}),
        html.Div(
            style={**CARD_STYLE, "padding": "14px 18px", "marginBottom": "20px"},
            children=[
                html.Div(
                    "Мэдээллийн эх сурвалж: Zangia, Lambda Global, Paylab, Salary Statistics.",
                    style={"color": COLORS["text"]},
                ),
            ],
        ),
        dcc.Interval(id="interval-component", interval=5 * 60 * 1000, n_intervals=0),
        dcc.Store(id="chat-store", data=[{"role": "assistant", "content": "Сайн байна уу! Танд юугаар туслах вэ?"}]),
        dcc.Store(id="chat-request"),
        dcc.Store(id="session-store", storage_type="session"),
        dcc.Store(id="chat-widget-open", data=False),
        dcc.Download(id="excel-download"),
        html.Div(
            className="dashboard-shell",
            style={"display": "flex", "gap": "24px", "alignItems": "flex-start"},
            children=[
                html.Div(
                    className="dashboard-main",
                    style={"flex": "1", "minWidth": "640px"},
                    children=[
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.H2("Шүүлтүүр", style={"color": COLORS["dark"], "marginTop": 0}),
                                html.Label(
                                    "Шүүлтүүрийн төрөл",
                                    style={"display": "block", "color": COLORS["text"], "marginBottom": "8px", "fontWeight": "bold"},
                                ),
                                dcc.Dropdown(
                                    id="type-selector",
                                    options=_safe_type_options(_load_data_main()),
                                    value="function",
                                    clearable=False,
                                ),
                                html.Div(style={"height": "12px"}),
                                html.Label(
                                    "Сонголт (харьцуулах бол олон утга сонгоно)",
                                    style={"display": "block", "color": COLORS["text"], "marginBottom": "8px", "fontWeight": "bold"},
                                ),
                                dcc.Dropdown(
                                    id="title-filter",
                                    placeholder="Нэг эсвэл хэд хэдэн ангилал сонгох",
                                    multi=True,
                                    clearable=True,
                                ),
                            ],
                        ),
                        html.Div(
                            id="experience-breakdown-table-card",
                            className="card",
                            style={**CARD_STYLE, "marginTop": "-4px"},
                            children=[
                                html.H3("Туршлагаар цалингийн хүснэгт", style={"color": COLORS["dark"], "marginTop": 0}),
                                dcc.Loading(
                                    type="dot",
                                    color=COLORS["primary"],
                                    children=dash_table.DataTable(
                                        id="experience-breakdown-table",
                                        page_size=8,
                                        style_table={"overflowX": "auto"},
                                        style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Arial"},
                                        style_header={
                                            "backgroundColor": COLORS["secondary"],
                                            "color": "white",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ),
                            ],
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "24px"},
                            id="kpi-container",
                        ),
                        html.Div(
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "24px"},
                            children=[
                                html.Div(
                                    id="salary-bar-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="salary-bar"))],
                                ),
                                html.Div(
                                    id="salary-range-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="salary-range"))],
                                ),
                                html.Div(
                                    id="count-bar-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="count-bar"))],
                                ),
                                html.Div(
                                    id="trend-line-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="trend-line"))],
                                ),
                            ],
                        ),
                        html.Div(
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "24px", "marginTop": "24px"},
                            children=[
                                html.Div(
                                    id="source-pie-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="source-pie"))],
                                ),
                                html.Div(
                                    id="compare-chart-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Loading(type="circle", color=COLORS["primary"], children=dcc.Graph(id="compare-chart"))],
                                ),
                            ],
                        ),
                        html.Div(
                            id="table-card",
                            className="card",
                            style={**CARD_STYLE, "marginTop": "24px"},
                            children=[
                                html.H3("Дэлгэрэнгүй хүснэгт", style={"color": COLORS["dark"], "marginTop": 0}),
                                html.Button(
                                    "Excel татах",
                                    id="download-excel",
                                    type="button",
                                    style={
                                        "marginBottom": "12px",
                                        "padding": "8px 14px",
                                        "backgroundColor": COLORS["secondary"],
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "8px",
                                        "cursor": "pointer",
                                    },
                                ),
                                dcc.Loading(
                                    type="dot",
                                    color=COLORS["primary"],
                                    children=dash_table.DataTable(
                                        id="detail-table",
                                        page_size=10,
                                        style_table={"overflowX": "auto"},
                                        style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Arial"},
                                        style_header={
                                            "backgroundColor": COLORS["primary"],
                                            "color": "white",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ),
                                html.H4("Сонгосон мөрүүд", style={"color": COLORS["dark"], "marginTop": "16px", "marginBottom": "8px"}),
                                html.Div(
                                    id="selected-detail-summary",
                                    style={"color": COLORS["muted"], "marginBottom": "8px"},
                                    children="Мөр сонгоогүй байна.",
                                ),
                                dash_table.DataTable(
                                    id="selected-detail-table",
                                    page_size=5,
                                    style_table={"overflowX": "auto"},
                                    style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Arial"},
                                    style_header={
                                        "backgroundColor": "#E2E8F0",
                                        "color": COLORS["dark"],
                                        "fontWeight": "bold",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Button("💬", id="chat-widget-toggle", type="button", className="chat-widget-toggle", n_clicks=0),
        html.Div(
            id="chat-widget-panel",
            className="chat-widget-panel",
            style={"display": "none"},
            children=[
                html.Div(
                    className="chat-widget-header",
                    children=[
                        html.H2("💬 Chatbot", style={"color": COLORS["dark"], "margin": 0, "fontSize": "18px"}),
                        html.P(
                            "Цалингийн мэдээлэл дээр суурилсан AI туслах.",
                            style={"color": COLORS["muted"], "margin": "4px 0 0 0", "fontSize": "13px"},
                        ),
                    ],
                ),
                html.Div(
                    style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginBottom": "10px"},
                    children=[
                        html.Button("Дундаж цалин хэд вэ?", id="quick-q-salary", n_clicks=0, type="button", className="chat-chip-btn"),
                        html.Button("Хамгийн өндөр цалинтай ангилал", id="quick-q-top", n_clicks=0, type="button", className="chat-chip-btn"),
                        html.Button("Сарын чиг хандлага", id="quick-q-trend", n_clicks=0, type="button", className="chat-chip-btn"),
                    ],
                ),
                html.Div(
                    id="chat-output",
                    className="chat-output",
                    children=_render_chat(
                        [{"role": "assistant", "content": "Сайн байна уу! Танд юугаар туслах вэ?"}]
                    ),
                    style={
                        "flex": "1",
                        "minHeight": "260px",
                        "maxHeight": "340px",
                        "overflowY": "auto",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "4px",
                        "padding": "8px",
                        "backgroundColor": "#F8FAFC",
                        "borderRadius": "12px",
                        "border": f"1px solid {COLORS['muted']}20",
                    },
                ),
                html.Div(style={"height": "12px"}),
                dcc.Input(
                    id="chat-session",
                    placeholder="session_id",
                    type="text",
                    style={
                        "width": "100%",
                        "height": "38px",
                        "padding": "8px 10px",
                        "borderRadius": "8px",
                        "border": f"1px solid {COLORS['muted']}40",
                        "marginBottom": "10px",
                    },
                ),
                dcc.Textarea(
                    id="chat-input",
                    placeholder="Та асуух зүйлээ энд бичнэ үү...",
                    style={
                        "width": "100%",
                        "height": "70px",
                        "padding": "10px",
                        "borderRadius": "8px",
                        "border": f"1px solid {COLORS['muted']}40",
                        "resize": "none",
                        "overflowY": "hidden",
                    },
                ),
                html.Button(
                    "Send",
                    id="chat-send",
                    type="button",
                    style={
                        "marginTop": "12px",
                        "width": "100%",
                        "height": "42px",
                        "padding": "10px",
                        "backgroundColor": COLORS["primary"],
                        "color": "white",
                        "border": "none",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                    },
                ),
            ],
        ),
    ],
)


@callback(
    Output("title-filter", "options"),
    Output("title-filter", "value"),
    Input("type-selector", "value"),
    Input("interval-component", "n_intervals"),
)
def update_title_options(selected_type: str, n_intervals: int):
    if not selected_type:
        return [], []

    df = _load_data_main()
    df = _filter_by_type(df, selected_type)
    df = _exclude_all_titles(df)
    df = _latest_per_title(df)
    if df.empty:
        return [], []
    options = [{"label": "Бүгд", "value": ALL_TITLES_VALUE}] + [
        {"label": title, "value": title}
        for title in sorted(df["title"].dropna().unique().tolist())
    ]
    return options, [ALL_TITLES_VALUE]


@callback(
    Output("session-store", "data"),
    Output("chat-session", "value"),
    Input("interval-component", "n_intervals"),
    State("session-store", "data"),
    prevent_initial_call=False,
)
def ensure_session_id(n_intervals: int, session_id: Optional[str]):
    if session_id:
        return session_id, session_id
    new_id = f"session-{uuid.uuid4().hex[:12]}"
    return new_id, new_id


@callback(
    Output("kpi-container", "children"),
    Output("salary-bar", "figure"),
    Output("salary-range", "figure"),
    Output("count-bar", "figure"),
    Output("trend-line", "figure"),
    Output("source-pie", "figure"),
    Output("compare-chart", "figure"),
    Output("experience-breakdown-table", "data"),
    Output("experience-breakdown-table", "columns"),
    Output("detail-table", "data"),
    Output("detail-table", "columns"),
    Input("type-selector", "value"),
    Input("title-filter", "value"),
    Input("interval-component", "n_intervals"),
)
def update_charts(selected_type: str, selected_title: object, n_intervals: int):
    if not selected_type:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return _build_kpi_cards(pd.DataFrame()), empty, empty, empty, empty, empty, empty, [], [], [], []

    df_all = _load_data_main()
    df_all = _filter_by_type(df_all, selected_type)
    df_all = _exclude_all_titles(df_all)
    if df_all.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return _build_kpi_cards(df_all), empty, empty, empty, empty, empty, empty, [], [], [], []

    df_latest = _latest_per_title(df_all)

    display_label = TYPE_LABELS.get(selected_type, "Төрөл")

    available_titles = df_all["title"].dropna().astype(str).unique().tolist()
    is_all_selected, selected_titles = _normalize_title_selection(selected_title, available_titles)

    if not is_all_selected:
        df_selected = df_all[df_all["title"].isin(selected_titles)].copy()
        df_selected_latest = df_latest[df_latest["title"].isin(selected_titles)].copy()
    else:
        df_selected = df_all.copy()
        df_selected_latest = df_latest.copy()

    kpis = _build_kpi_cards(df_selected_latest)

    chart_df_latest = df_selected_latest.copy()
    if chart_df_latest.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return kpis, empty, empty, empty, empty, empty, empty, [], [], [], []

    bar_df = chart_df_latest.groupby("title", as_index=False)["average_salary"].mean()
    bar_df["title_short"] = bar_df["title"].apply(_shorten_label)
    bar_fig = px.bar(
        bar_df,
        y="title_short",
        x="average_salary",
        orientation="h",
        title=f"Сарын дундаж цалин ({display_label})",
        labels={"title_short": display_label, "average_salary": "Дундаж цалин (₮)"},
        color_discrete_sequence=[COLORS["primary"]],
        hover_data={"title": True, "title_short": False, "average_salary": True},
    )
    bar_fig.update_layout(
        height=460,
        margin={"l": 120, "r": 20, "t": 50, "b": 40},
        yaxis={"automargin": True, "categoryorder": "total ascending"},
    )

    range_df = chart_df_latest.groupby("title", as_index=False).agg(
        min_salary=("min_salary", "min"),
        max_salary=("max_salary", "max"),
        average_salary=("average_salary", "mean"),
    )
    range_df["title_short"] = range_df["title"].apply(_shorten_label)
    range_fig = go.Figure()
    range_fig.add_bar(y=range_df["title_short"], x=range_df["min_salary"], name="Min", orientation="h", hovertext=range_df["title"])
    range_fig.add_bar(y=range_df["title_short"], x=range_df["max_salary"], name="Max", orientation="h", hovertext=range_df["title"])
    range_fig.add_trace(
        go.Scatter(
            y=range_df["title_short"],
            x=range_df["average_salary"],
            mode="markers",
            name="Average",
            marker={"size": 10, "color": COLORS["secondary"]},
            hovertext=range_df["title"],
        )
    )
    range_fig.update_layout(
        title=f"Цалингийн хүрээ ({display_label})",
        barmode="group",
        height=460,
        margin={"l": 120, "r": 20, "t": 50, "b": 40},
        xaxis_title="₮",
        yaxis={"automargin": True, "categoryorder": "total ascending"},
    )

    if "job_count" in chart_df_latest.columns:
        count_df = chart_df_latest.groupby("title", as_index=False)["job_count"].sum()
        count_df["title_short"] = count_df["title"].apply(_shorten_label)
        count_fig = px.bar(
            count_df,
            y="title_short",
            x="job_count",
            orientation="h",
            title=f"Ажлын байрны тоо ({display_label})",
            labels={"title_short": display_label, "job_count": "Ажлын байр"},
            color_discrete_sequence=[COLORS["accent"]],
            hover_data={"title": True, "title_short": False, "job_count": True},
        )
        count_fig.update_layout(
            height=460,
            margin={"l": 120, "r": 20, "t": 50, "b": 40},
            yaxis={"automargin": True, "categoryorder": "total ascending"},
        )
    else:
        count_fig = _empty_figure("Зарын тооны өгөгдөл алга")

    if "period" in df_selected.columns and df_selected["period"].notna().any():
        trend_df = df_selected.groupby("period", as_index=False)["average_salary"].mean()
        trend_fig = px.line(
            trend_df,
            x="period",
            y="average_salary",
            markers=True,
            title="Дундаж цалингийн динамик, сараар",
            labels={"period": "Сар", "average_salary": "Дундаж цалин (₮)"},
        )
        trend_fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 60})
    else:
        trend_fig = _empty_figure("Цаг хугацааны өгөгдөл алга")

    if "zangia_count" in chart_df_latest.columns and "lambda_count" in chart_df_latest.columns:
        source_total = {
            "Zangia": int(chart_df_latest["zangia_count"].sum()),
            "Lambda Global": int(chart_df_latest["lambda_count"].sum()),
        }
        source_fig = px.pie(
            names=list(source_total.keys()),
            values=list(source_total.values()),
            hole=0.45,
            title="Мэдээллийн эх сурвалжийн харьцаа",
            color_discrete_sequence=[COLORS["primary"], COLORS["accent"]],
        )
        source_fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
    else:
        source_fig = _empty_figure("Эх сурвалжийн өгөгдөл алга")

    compare_df = chart_df_latest.groupby("title", as_index=False).agg(
        min_salary=("min_salary", "min"),
        average_salary=("average_salary", "mean"),
        max_salary=("max_salary", "max"),
    )
    compare_df = compare_df.sort_values("average_salary", ascending=False)

    if len(compare_df) > 12:
        compare_df = compare_df.head(12)

    if not compare_df.empty:
        compare_long = compare_df.melt(
            id_vars=["title"],
            value_vars=["min_salary", "average_salary", "max_salary"],
            var_name="metric",
            value_name="salary",
        )
        compare_long["metric"] = compare_long["metric"].map(
            {
                "min_salary": "Доод",
                "average_salary": "Дундаж",
                "max_salary": "Дээд",
            }
        )
        compare_fig = px.bar(
            compare_long,
            x="title",
            y="salary",
            color="metric",
            barmode="group",
            title=f"Сонгосон ангиллуудын цалингийн харьцуулалт ({display_label})",
            labels={"title": display_label, "salary": "Цалин (₮)", "metric": "Үзүүлэлт"},
            color_discrete_map={
                "Доод": "#93C5FD",
                "Дундаж": COLORS["primary"],
                "Дээд": "#1E3A8A",
            },
        )
        compare_fig.update_layout(margin={"l": 20, "r": 20, "t": 58, "b": 95}, xaxis_tickangle=-20)
    else:
        compare_fig = _empty_figure("Харьцуулах өгөгдөл алга")

    experience_table_data, experience_table_columns = _build_experience_breakdown_table(
        chart_df_latest,
        is_all_selected=is_all_selected,
    )

    table_df = chart_df_latest.copy()
    if "experience_salary_breakdown" in table_df.columns:
        table_df["experience_salary_breakdown"] = table_df["experience_salary_breakdown"].apply(_format_experience_breakdown_for_table)
    table_df = table_df.rename(
        columns={
            "title": "Ажлын ангилал",
            "min_salary": "Доод цалин",
            "max_salary": "Дээд цалин",
            "average_salary": "Дундаж цалин",
            "job_count": "Зарын тоо",
            "zangia_count": "Zangia",
            "lambda_count": "Lambda",
            "experience_salary_breakdown": "Туршлагаар цалин",
        }
    )
    table_columns = [
        {"name": col, "id": col}
        for col in [
            "Ажлын ангилал",
            "Доод цалин",
            "Дээд цалин",
            "Дундаж цалин",
            "Зарын тоо",
            "Zangia",
            "Lambda",
            "Туршлагаар цалин",
        ]
        if col in table_df.columns
    ]
    table_data = table_df[ [c["id"] for c in table_columns] ].to_dict("records")

    for fig in [bar_fig, range_fig, count_fig, trend_fig, source_fig, compare_fig]:
        fig.update_layout(transition={"duration": 300, "easing": "cubic-in-out"})

    return (
        kpis,
        bar_fig,
        range_fig,
        count_fig,
        trend_fig,
        source_fig,
        compare_fig,
        experience_table_data,
        experience_table_columns,
        table_data,
        table_columns,
    )


@callback(
    Output("salary-bar-card", "className"),
    Output("salary-range-card", "className"),
    Output("count-bar-card", "className"),
    Output("trend-line-card", "className"),
    Output("source-pie-card", "className"),
    Output("compare-chart-card", "className"),
    Output("experience-breakdown-table-card", "className"),
    Output("table-card", "className"),
    Input("salary-bar", "loading_state"),
    Input("salary-range", "loading_state"),
    Input("count-bar", "loading_state"),
    Input("trend-line", "loading_state"),
    Input("source-pie", "loading_state"),
    Input("compare-chart", "loading_state"),
    Input("experience-breakdown-table", "loading_state"),
    Input("detail-table", "loading_state"),
)
def update_loading_skeleton(*states):
    def _cls(state):
        if state and state.get("is_loading"):
            return "card skeleton"
        return "card"

    return tuple(_cls(state) for state in states)


@callback(
    Output("selected-detail-summary", "children"),
    Output("selected-detail-table", "data"),
    Output("selected-detail-table", "columns"),
    Input("detail-table", "data"),
    Input("detail-table", "selected_rows"),
)
def update_selected_detail_table(
    table_data: Optional[List[Dict[str, object]]],
    selected_rows: Optional[List[int]],
):
    if not table_data:
        return "Өгөгдөл алга.", [], []

    selected_rows = selected_rows or []
    if not selected_rows:
        return "Мөр сонгоогүй байна.", [], []

    selected_items = [table_data[idx] for idx in selected_rows if 0 <= idx < len(table_data)]
    if not selected_items:
        return "Сонголт олдсонгүй.", [], []

    columns = [{"name": col, "id": col} for col in selected_items[0].keys()]
    avg_salary_values: List[float] = []
    for item in selected_items:
        parsed = _to_float(item.get("Дундаж цалин"))
        if parsed is not None:
            avg_salary_values.append(parsed)
    avg_text = ""
    if avg_salary_values:
        avg_text = f" · Сонгосон мөрүүдийн дундаж: {_format_mnt(sum(avg_salary_values) / len(avg_salary_values))}"

    return f"Сонгосон мөрийн тоо: {len(selected_items)}{avg_text}", selected_items, columns


@callback(
    Output("chat-widget-open", "data"),
    Input("chat-widget-toggle", "n_clicks"),
    State("chat-widget-open", "data"),
    prevent_initial_call=True,
)
def toggle_chat_widget(n_clicks: int, is_open: Optional[bool]):
    return not bool(is_open)


@callback(
    Output("chat-widget-panel", "style"),
    Input("chat-widget-open", "data"),
)
def update_chat_widget_visibility(is_open: Optional[bool]):
    base_style = {
        "position": "fixed",
        "right": "24px",
        "bottom": "90px",
        "width": "400px",
        "maxWidth": "calc(100vw - 24px)",
        "display": "none",
        "flexDirection": "column",
        "zIndex": 1100,
    }
    if bool(is_open):
        base_style["display"] = "flex"
    return base_style


@callback(
    Output("excel-download", "data"),
    Input("download-excel", "n_clicks"),
    State("detail-table", "data"),
    prevent_initial_call=True,
)
def download_excel(n_clicks: int, table_data: List[Dict[str, object]]):
    if not table_data:
        return dash.no_update

    df = pd.DataFrame(table_data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Salary_Report")
        ws = writer.sheets["Salary_Report"]

        header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
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
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 40)

        money_cols = {"Доод цалин", "Дээд цалин", "Дундаж цалин"}
        for col_idx, cell in enumerate(ws[1], start=1):
            if cell.value in money_cols:
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).number_format = "#,##0\"₮\""
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="right")
            if cell.value in {"Зарын тоо", "Zangia", "Lambda"}:
                for row in range(2, ws.max_row + 1):
                    ws.cell(row=row, column=col_idx).alignment = Alignment(horizontal="center")
    buffer.seek(0)

    return dcc.send_bytes(buffer.read(), "salary_report.xlsx")


@callback(
    Output("chat-input", "value", allow_duplicate=True),
    Input("quick-q-salary", "n_clicks"),
    Input("quick-q-top", "n_clicks"),
    Input("quick-q-trend", "n_clicks"),
    prevent_initial_call=True,
)
def apply_quick_question(n_salary: int, n_top: int, n_trend: int):
    triggered = ctx.triggered_id
    if triggered == "quick-q-salary":
        return "Дундаж цалин хэд байна вэ?"
    if triggered == "quick-q-top":
        return "Хамгийн өндөр дундаж цалинтай ангиллыг хэлээч."
    if triggered == "quick-q-trend":
        return "Сүүлийн саруудын дундаж цалингийн чиг хандлагыг тайлбарлаач."
    return ""


@callback(
    Output("chat-send", "disabled"),
    Output("chat-input", "disabled"),
    Output("quick-q-salary", "disabled"),
    Output("quick-q-top", "disabled"),
    Output("quick-q-trend", "disabled"),
    Output("chat-send", "children"),
    Input("chat-store", "data"),
)
def set_chat_loading_state(history: Optional[List[Dict[str, object]]]):
    history = history or []
    is_loading = any(bool(item.get("pending")) for item in history if isinstance(item, dict))
    send_text = "Хариу бичиж байна..." if is_loading else "Send"
    return is_loading, is_loading, is_loading, is_loading, is_loading, send_text


@callback(
    Output("chat-store", "data"),
    Output("chat-output", "children"),
    Output("chat-input", "value"),
    Output("chat-request", "data"),
    Input("chat-send", "n_clicks"),
    State("chat-input", "value"),
    State("chat-session", "value"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def handle_chat(
    n_clicks: int,
    message: Optional[str],
    session_id: Optional[str],
    history: List[Dict[str, object]],
):
    if not message or not message.strip():
        return history, _render_chat(history), "", None

    if not N8N_AGENT_URL:
        error_history = history + [
            {"role": "assistant", "content": "Agent тохируулагдаагүй байна."}
        ]
        return error_history, _render_chat(error_history), "", None

    session_value = session_id or f"session-{uuid.uuid4().hex[:12]}"
    updated_history = history + [
        {"role": "user", "content": message.strip()},
        {"role": "assistant", "content": "...", "pending": True},
    ]

    request_payload = {"session_id": session_value, "message": message.strip()}
    return updated_history, _render_chat(updated_history), "", request_payload


@callback(
    Output("chat-store", "data", allow_duplicate=True),
    Output("chat-output", "children", allow_duplicate=True),
    Input("chat-request", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def fetch_chat_response(request_payload: Optional[Dict[str, str]], history: List[Dict[str, object]]):
    if not request_payload:
        return history, _render_chat(history)

    def _extract_text(payload: Dict[str, object], fallback: str) -> str:
        text = payload.get("output") or payload.get("result") or payload.get("message")
        if text:
            return str(text)
        data = payload.get("data")
        if isinstance(data, dict):
            nested = data.get("output") or data.get("result") or data.get("message")
            if nested:
                return str(nested)
        if isinstance(data, str):
            return data
        return fallback

    response_text = "Уучлаарай, хариу авахад алдаа гарлаа."
    last_error = None
    for _ in range(2):
        try:
            response = requests.post(
                N8N_AGENT_URL,
                json=request_payload,
                timeout=(5, 60),
            )
            if response.ok:
                try:
                    payload = response.json()
                    response_text = _extract_text(payload, response.text)
                except ValueError:
                    response_text = response.text
            else:
                response_text = f"Алдаа: {response.status_code}"
            last_error = None
            break
        except requests.RequestException as exc:
            last_error = exc

    if last_error is not None:
        response_text = "Сүлжээний алдаа. Дахин оролдоно уу."

    updated_history = []
    pending_replaced = False
    for item in history:
        if item.get("pending") and not pending_replaced:
            updated_history.append({"role": "assistant", "content": response_text})
            pending_replaced = True
        else:
            updated_history.append({k: v for k, v in item.items() if k != "pending"})

    if not pending_replaced:
        updated_history.append({"role": "assistant", "content": response_text})

    return updated_history, _render_chat(updated_history)


if __name__ == "__main__":
    app.run(debug=True, port="8006")
    
'''
