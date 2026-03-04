"""Modern multi-page salary dashboard."""

import io
import json
import logging
import os
import re
import ast
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, SupportsFloat, SupportsIndex, TypedDict, cast

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import Input, Output, State, callback, dcc, html, dash_table
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Font, PatternFill

load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
N8N_AGENT_URL = os.getenv("N8N_AGENT_URL", "").strip()
DASHBOARD_API_URL = os.getenv("DASHBOARD_API_URL", "http://127.0.0.1:8007").rstrip("/")
JOBS_LIST_LIMIT = int(os.getenv("JOBS_LIST_LIMIT", "500"))

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
    "industry": "Үйл ажиллагааны чиглэл/Салбар",
    "function": "Чиг үүрэг",
    "job_level": "Албан тушаалын түвшин",
    "techpack_category": "Албан тушаал",
}

ALL_TITLES_VALUE = "__all__"
NUMBER_GROUP_SEPARATOR = os.getenv("NUMBER_GROUP_SEPARATOR", ",").strip() or ","

_MAIN_DATA_CACHE: Optional[pd.DataFrame] = None
_MAIN_DATA_CACHE_TS: float = 0.0
_JOBS_DATA_CACHE: Optional[pd.DataFrame] = None
_JOBS_DATA_CACHE_TS: float = 0.0
_JOBS_DATA_CACHE_KEY: tuple[object, ...] | None = None
_JOBS_FILTER_OPTIONS_CACHE: Optional[Dict[str, List[Dict[str, str]]]] = None
_JOBS_FILTER_OPTIONS_CACHE_TS: float = 0.0


class ExperienceBreakdownItem(TypedDict):
    experience_level: str
    min_salary: float
    max_salary: float


def _post_api_json(route_name: str, payload: Optional[Dict[str, object]] = None, timeout: tuple[int, int] = (4, 30)) -> Optional[Dict[str, object]]:
    url = f"{DASHBOARD_API_URL}/api/{route_name}"
    try:
        response = requests.post(url, json=payload or {}, timeout=timeout)
        if not response.ok:
            logger.warning("API %s returned %d: %s", route_name, response.status_code, response.text[:200])
            return None
        data = response.json() if response.content else {}
        return data if isinstance(data, dict) else None
    except (requests.RequestException, ValueError) as exc:
        logger.warning("API %s request failed: %s", route_name, exc)
        return None


def _post_api_bytes(route_name: str, payload: Optional[Dict[str, object]] = None, timeout: tuple[int, int] = (4, 60)) -> Optional[bytes]:
    url = f"{DASHBOARD_API_URL}/api/{route_name}"
    try:
        response = requests.post(url, json=payload or {}, timeout=timeout)
        if not response.ok:
            logger.warning("API %s (bytes) returned %d", route_name, response.status_code)
            return None
        return response.content
    except requests.RequestException as exc:
        logger.warning("API %s (bytes) request failed: %s", route_name, exc)
        return None


def _send_bytes_download(file_bytes: bytes, filename: str):
    return dcc.send_bytes(lambda buffer: buffer.write(file_bytes), filename)


def _load_data_main() -> pd.DataFrame:
    global _MAIN_DATA_CACHE, _MAIN_DATA_CACHE_TS

    now = time.time()
    if _MAIN_DATA_CACHE is not None and (now - _MAIN_DATA_CACHE_TS) < 45:
        return _MAIN_DATA_CACHE.copy()

    api_payload = _post_api_json("dashboard/main-data")
    if api_payload and isinstance(api_payload.get("items"), list):
        df = pd.DataFrame(cast(List[Dict[str, object]], api_payload["items"]))
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    else:
        df = pd.DataFrame()

    _MAIN_DATA_CACHE = df
    _MAIN_DATA_CACHE_TS = now
    return df.copy()


def _load_jobs_raw(
    limit: int = 10000,
    search: Optional[str] = None,
    source: Optional[str] = None,
    selected_function: Optional[str] = None,
    selected_industry: Optional[str] = None,
    selected_level: Optional[str] = None,
    selected_company: Optional[str] = None,
) -> pd.DataFrame:
    global _JOBS_DATA_CACHE, _JOBS_DATA_CACHE_TS, _JOBS_DATA_CACHE_KEY

    now = time.time()
    cache_key = (
        int(limit),
        (search or "").strip().lower(),
        source or "",
        selected_function or "",
        selected_industry or "",
        selected_level or "",
        selected_company or "",
    )
    if _JOBS_DATA_CACHE is not None and _JOBS_DATA_CACHE_KEY == cache_key and (now - _JOBS_DATA_CACHE_TS) < 45:
        return _JOBS_DATA_CACHE.head(limit).copy()

    payload: Dict[str, object] = {
        "limit": int(limit),
        "search": (search or "").strip() or None,
        "source": source,
        "selected_function": selected_function,
        "selected_industry": selected_industry,
        "selected_level": selected_level,
        "selected_company": selected_company,
    }
    api_payload = _post_api_json("dashboard/jobs-data", payload=payload)
    if api_payload and isinstance(api_payload.get("items"), list):
        df = pd.DataFrame(cast(List[Dict[str, object]], api_payload["items"]))
    else:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    _JOBS_DATA_CACHE = df
    _JOBS_DATA_CACHE_TS = now
    _JOBS_DATA_CACHE_KEY = cache_key
    return df.copy()


def _load_jobs_filter_options(refresh: bool = False) -> Dict[str, List[Dict[str, str]]]:
    global _JOBS_FILTER_OPTIONS_CACHE, _JOBS_FILTER_OPTIONS_CACHE_TS

    now = time.time()
    if not refresh and _JOBS_FILTER_OPTIONS_CACHE is not None and (now - _JOBS_FILTER_OPTIONS_CACHE_TS) < 300:
        return dict(_JOBS_FILTER_OPTIONS_CACHE)

    api_payload = _post_api_json("dashboard/jobs-filter-options", payload={"refresh": bool(refresh)})
    if not api_payload:
        return {
            "source_options": [],
            "function_options": [],
            "industry_options": [],
            "level_options": [],
            "company_options": [],
        }

    result = {
        "source_options": cast(List[Dict[str, str]], api_payload.get("source_options", [])),
        "function_options": cast(List[Dict[str, str]], api_payload.get("function_options", [])),
        "industry_options": cast(List[Dict[str, str]], api_payload.get("industry_options", [])),
        "level_options": cast(List[Dict[str, str]], api_payload.get("level_options", [])),
        "company_options": cast(List[Dict[str, str]], api_payload.get("company_options", [])),
    }
    _JOBS_FILTER_OPTIONS_CACHE = result
    _JOBS_FILTER_OPTIONS_CACHE_TS = now
    return dict(result)


def _first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _norm_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower().replace("_", " ")
    return re.sub(r"\s+", " ", text)


def _is_all_like(value: object) -> bool:
    return _norm_text(value) in {"", "all", "бүгд", "none", "null"}


def _normalize_optional_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return None if _is_all_like(cleaned) else cleaned


def _safe_selected_values(values: object) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [] if _is_all_like(values) else [values]
    if isinstance(values, (list, tuple, set)):
        cleaned = [str(v).strip() for v in values if not _is_all_like(v)]
        seen: set[str] = set()
        out: List[str] = []
        for item in cleaned:
            key = _norm_text(item)
            if key and key not in seen:
                seen.add(key)
                out.append(item)
        return out
    return []


_SEARCH_SYNONYM_GROUPS: Dict[str, List[str]] = {
    # Mongolian → English aliases
    "машин сургалтын инженер": ["machine learning engineer", "ml engineer", "ml", "ai engineer"],
    "ахлах машин сургалтын инженер": ["senior machine learning engineer", "senior ml engineer", "lead ml engineer"],
    "програм хангамжийн инженер": ["software engineer", "software developer", "swe", "dev"],
    "ахлах програм хангамжийн инженер": ["senior software engineer", "senior developer", "lead developer"],
    "бүтээгдэхүүний менежер": ["product manager", "pm", "product owner"],
    "төслийн менежер": ["project manager", "project lead"],
    "өгөгдлийн шинжээч": ["data analyst", "data analytics", "bi analyst"],
    "өгөгдлийн инженер": ["data engineer", "de", "etl engineer"],
    "өгөгдлийн шинжлэх ухаанч": ["data scientist", "ds"],
    "веб хөгжүүлэгч": ["web developer", "frontend developer", "front-end developer"],
    "систем админ": ["system administrator", "sysadmin", "sys admin", "it admin"],
    "чанарын инженер": ["qa engineer", "quality assurance", "test engineer", "tester"],
    "дизайнер": ["designer", "ui designer", "ux designer", "ui/ux designer"],
    "маркетинг менежер": ["marketing manager", "marketing lead"],
    "санхүүгийн шинжээч": ["financial analyst", "finance analyst"],
    "нягтлан бодогч": ["accountant", "accounting"],
    "хүний нөөцийн менежер": ["hr manager", "human resources manager"],
    # English → Mongolian aliases
    "machine learning engineer": ["машин сургалтын инженер", "ml engineer", "ml", "ai engineer"],
    "senior machine learning engineer": ["ахлах машин сургалтын инженер", "senior ml engineer", "lead ml engineer"],
    "software engineer": ["програм хангамжийн инженер", "software developer", "swe", "dev"],
    "product manager": ["бүтээгдэхүүний менежер", "pm", "product owner"],
    "data analyst": ["өгөгдлийн шинжээч", "bi analyst"],
    "data engineer": ["өгөгдлийн инженер", "etl engineer"],
    "data scientist": ["өгөгдлийн шинжлэх ухаанч", "ds"],
    "qa engineer": ["чанарын инженер", "quality assurance", "test engineer"],
    "project manager": ["төслийн менежер", "project lead"],
}


def _expand_search_tokens(search_text: str) -> List[str]:
    normalized = _norm_text(search_text)
    if not normalized:
        return []

    expanded: List[str] = []
    seen: set[str] = set()

    def _add(token: str) -> None:
        token_norm = _norm_text(token)
        if token_norm and token_norm not in seen:
            seen.add(token_norm)
            expanded.append(token_norm)

    for token in [part for part in normalized.split(" ") if part]:
        _add(token)

    return expanded


def _expand_search_alias_phrases(search_text: str) -> List[str]:
    normalized = _norm_text(search_text)
    if not normalized:
        return []

    aliases: List[str] = []
    seen: set[str] = set()

    for phrase, phrase_aliases in _SEARCH_SYNONYM_GROUPS.items():
        phrase_norm = _norm_text(phrase)
        if not phrase_norm or phrase_norm not in normalized:
            continue
        for alias in phrase_aliases:
            alias_norm = _norm_text(alias)
            if alias_norm and alias_norm not in seen:
                seen.add(alias_norm)
                aliases.append(alias_norm)

    return aliases


def _distinct_non_empty_values(df: pd.DataFrame, column_name: str) -> List[str]:
    if df.empty or column_name not in df.columns:
        return []
    values = df[column_name].dropna().astype(str).str.strip()
    values = values[values != ""]
    values = values[~values.map(_is_all_like)]
    return sorted(values.unique().tolist())


def _apply_main_dimension_filters(
    df: pd.DataFrame,
    selected_function: Optional[str] = None,
    selected_industry: Optional[str] = None,
    selected_level: Optional[str] = None,
    selected_category: Optional[str] = None,
    selected_year: Optional[str] = None,
    selected_month: Optional[str] = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()
    dimensions = [
        ("job_function", selected_function),
        ("industry", selected_industry),
        ("job_level", selected_level),
        ("techpack_category", selected_category),
        ("year", selected_year),
        ("month", selected_month),
    ]
    for col, value in dimensions:
        if col not in filtered.columns or not value or not str(value).strip() or _is_all_like(value):
            continue
        if col in {"year", "month"}:
            target_num = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(target_num):
                continue
            current_num = pd.to_numeric(filtered[col], errors="coerce")
            filtered = filtered[current_num == int(target_num)]
            continue

        target = str(value).strip().lower()
        current = filtered[col].fillna("").astype(str).str.strip().str.lower()
        filtered = filtered[current == target]

    return filtered


def _format_mnt(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f} ₮"


def _format_mnt_compact(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{(float(value) / 1_000_000):.1f}M ₮"


def _shorten_label(text: str, max_len: int = 28) -> str:
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
        autosize=True,
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": COLORS["text"]},
        transition={"duration": 300, "easing": "cubic-in-out"},
    )


def _render_chat_messages(history: List[Dict[str, object]]) -> List[html.Div]:
    bubbles: List[html.Div] = []
    for item in history:
        role = item.get("role", "assistant")
        content = item.get("content", "")
        pending = bool(item.get("pending"))

        if isinstance(content, (str, int, float)) or content is None:
            bubble_content: Any = content or ""
        else:
            bubble_content = str(content)

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
                    html.Div(
                        className="hero-top-row",
                        children=[
                            html.Div(
                                children=[
                                    html.H1("Цалингийн шинжилгээний dashboard", className="hero-title"),
                                    html.P("Мэдээллийн эх сурвалж: Zangia, Lambda Global, Paylab, Salary Statistics.", className="hero-subtitle"),
                                ],
                            ),
                            html.Button("💬 Chat", id="chat-toggle", className="chat-toggle-btn", n_clicks=0),
                        ],
                    ),
                ],
            ),
            dcc.Interval(id="interval-component", interval=5 * 60 * 1000, n_intervals=0),
            dcc.Download(id="excel-download"),
            dcc.Store(
                id="chat-store",
                data=[{"role": "assistant", "content": "Сайн байна уу 👋 Танд цалин, албан тушаалын түвшин, салбарын чиг хандлага болон ажлын зах зээлийн мэдээлэл өгч чадна."}],
            ),
            dcc.Store(id="chat-request"),
            dcc.Store(id="chat-open", data=True),
            dcc.Store(id="detail-table-raw", data=[]),
            html.Div(
                id="dashboard-split",
                className="dashboard-split",
                children=[
                    # ── LEFT: main dashboard content ──
                    html.Div(
                        id="dashboard-main",
                        className="dashboard-main",
                        children=[
                            html.Div(
                                className="card jobs-filter-card",
                                children=[
                                    html.Div("Өгөгдлийн сангаас хайлт ба шүүлтүүр", className="jobs-filter-section-title"),
                                    html.Div(
                                        className="jobs-filter-grid",
                                        children=[
                                            html.Div(
                                                children=[
                                                    html.Label("Салбар", className="field-label"),
                                                    dcc.Dropdown(id="main-industry", options=[], placeholder="Бүгд", clearable=True),
                                                ]
                                            ),
                                            html.Div(
                                                children=[
                                                    html.Label("Чиг үүрэг", className="field-label"),
                                                    dcc.Dropdown(id="main-function", options=[], placeholder="Бүгд", clearable=True),
                                                ]
                                            ),
                                            html.Div(
                                                children=[
                                                    html.Label("Албан тушаалын түвшин", className="field-label"),
                                                    dcc.Dropdown(id="main-level", options=[], placeholder="Бүгд", clearable=True),
                                                ]
                                            ),
                                            html.Div(
                                                children=[
                                                    html.Label("Албан тушаалын ангилал", className="field-label"),
                                                    dcc.Dropdown(id="main-category", options=[], placeholder="Бүгд", clearable=True),
                                                ]
                                            ),
                                            html.Div(
                                                children=[
                                                    html.Label("Он", className="field-label"),
                                                    dcc.Dropdown(id="main-year", options=[], placeholder="Бүгд", clearable=True),
                                                ]
                                            ),
                                            html.Div(
                                                children=[
                                                    html.Label("Сар", className="field-label"),
                                                    dcc.Dropdown(id="main-month", options=[], placeholder="Бүгд", clearable=True),
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
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="salary-bar", config={"responsive": True}, style={"height": "430px"})]),
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="salary-range", config={"responsive": True}, style={"height": "520px"})]),
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="count-bar", config={"responsive": True}, style={"height": "430px"})]),
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="trend-line", config={"responsive": True}, style={"height": "430px"})]),
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="source-pie", config={"responsive": True}, style={"height": "430px"})]),
                                        html.Div(className="card chart-card", children=[dcc.Graph(id="compare-chart", config={"responsive": True}, style={"height": "460px"})]),
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
                                                    page_action="none",
                                                    style_table={"overflowX": "auto", "overflowY": "auto", "maxHeight": "600px", "width": "100%"},
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
                        ],
                    ),
                    # ── RIGHT: chatbot side panel (hidden by default) ──
                    html.Div(
                        id="chat-panel",
                        className="chat-side-panel",
                        children=[
                            html.Div(
                                className="chat-panel-header",
                                children=[
                                    html.Div("AI Chat Assistant", className="chat-title"),
                                    html.Button("✕", id="chat-close", className="chat-close-btn", n_clicks=0),
                                ],
                            ),
                            html.Div(id="chat-output", className="chat-output", children=_render_chat_messages([{"role": "assistant", "content": "Сайн байна уу 👋 Танд цалин, албан тушаалын түвшин, салбарын чиг хандлага болон ажлын зах зээлийн мэдээлэл өгч чадна."}])),
                            html.Div(
                                className="chat-input-row",
                                children=[
                                    dcc.Input(id="chat-input", className="chat-input-line", type="text", placeholder="Асуултаа бичнэ үү...", debounce=False),
                                    html.Button("Илгээх", id="chat-send", className="btn-primary chat-send", n_clicks=0),
                                ],
                            ),
                        ],
                    ),
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
            dcc.Store(id="jobs-table-raw", data=[]),
            html.Div(
                className="card jobs-filter-card",
                children=[
                    html.Div("Өгөгдлийн сангаас хайлт ба шүүлтүүр", className="jobs-filter-section-title"),
                    html.Div(
                        className="jobs-filter-grid",
                        children=[
                            html.Div(children=[html.Label("Эх сурвалж", className="field-label"), dcc.Dropdown(id="jobs-source", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Функц", className="field-label"), dcc.Dropdown(id="jobs-function", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Салбар", className="field-label"), dcc.Dropdown(id="jobs-industry", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Түвшин", className="field-label"), dcc.Dropdown(id="jobs-level", options=[], placeholder="Бүгд", clearable=True)]),
                            html.Div(children=[html.Label("Компани", className="field-label"), dcc.Dropdown(id="jobs-company", options=[], placeholder="Бүгд", clearable=True)]),
                        ],
                    ),
                    html.Div(
                        className="jobs-search-row",
                        children=[
                            dcc.Input(
                                id="jobs-api-search",
                                type="text",
                                placeholder="Гарчиг, компани, requirement...",
                                className="jobs-search-input",
                                debounce=False,
                                style={"flex": "1"},
                            ),
                            html.Button("Хайх", id="jobs-api-search-btn", n_clicks=0, className="btn-primary"),
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
                        delay_show=300,
                        delay_hide=120,
                        children=[
                            html.Div(
                                className="section-header",
                                children=[
                                    html.Div(id="jobs-count", className="jobs-count", children="Нийт мөр: 0"),
                                    html.Button("Excel татах", id="download-jobs-excel", n_clicks=0, className="btn-primary"),
                                ],
                            ),
                            html.Div(
                                className="detail-filter-row",
                                children=[
                                    html.Div("Хүснэгтийн дотоод шүүлтүүр (одоогийн үр дүн)", className="jobs-filter-section-title"),
                                ],
                            ),
                            html.Div(
                                className="jobs-local-filter-row",
                                children=[
                                    dcc.Dropdown(
                                        id="jobs-local-source-filter",
                                        options=[],
                                        value=[],
                                        multi=True,
                                        placeholder="Хүснэгт дотор: Эх сурвалж",
                                        className="detail-title-filter",
                                    ),
                                    dcc.Dropdown(
                                        id="jobs-local-level-filter",
                                        options=[],
                                        value=[],
                                        multi=True,
                                        placeholder="Хүснэгт дотор: Түвшин",
                                        className="detail-title-filter",
                                    ),
                                    dcc.Input(
                                        id="jobs-local-search",
                                        type="text",
                                        value="",
                                        debounce=True,
                                        placeholder="Хүснэгт дотор хайх (одоогийн үр дүнгээс)...",
                                        className="detail-search-input",
                                    ),
                                ],
                            ),
                            dash_table.DataTable(
                                id="jobs-table",
                                page_action="native",
                                page_size=25,
                                sort_action="native",
                                filter_action="native",
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
                                style_cell_conditional=cast(
                                    Any,
                                    [
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
                                ),
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
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

app.layout = html.Div(
    className="app-root",
    children=[
        dcc.Location(id="url"),
        _navbar(),
        html.Div(className="top-nav-spacer"),
        html.Main(id="page-content", className="page-container"),
    ],
)


@callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: Optional[str]):
    if pathname == "/jobs-list":
        return _jobs_list_layout()
    return _dashboard_page_layout()


@callback(Output("chat-open", "data"), Input("chat-toggle", "n_clicks"), Input("chat-close", "n_clicks"), State("chat-open", "data"), prevent_initial_call=True)
def toggle_chat(toggle_clicks: int, close_clicks: int, is_open: Optional[bool]):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "chat-close":
        return False
    return not bool(is_open)


@callback(
    Output("chat-panel", "className"),
    Output("dashboard-main", "className"),
    Input("chat-open", "data"),
)
def set_chat_visibility(is_open: Optional[bool]):
    if is_open:
        return "chat-side-panel chat-side-panel--open", "dashboard-main dashboard-main--shrink"
    return "chat-side-panel", "dashboard-main"


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
    Output("jobs-table-raw", "data"),
    Input("jobs-api-search-btn", "n_clicks"),
    Input("jobs-interval", "n_intervals"),
    State("jobs-api-search", "value"),
    State("jobs-source", "value"),
    State("jobs-function", "value"),
    State("jobs-industry", "value"),
    State("jobs-level", "value"),
    State("jobs-company", "value"),
)
def update_jobs_list(
    n_clicks: int,
    n_intervals: int,
    api_search_text: Optional[str],
    source: Optional[str],
    selected_function: Optional[str],
    selected_industry: Optional[str],
    selected_level: Optional[str],
    selected_company: Optional[str],
):
    filter_options = _load_jobs_filter_options(refresh=(n_intervals == 0))

    source = _normalize_optional_filter(source)
    selected_function = _normalize_optional_filter(selected_function)
    selected_industry = _normalize_optional_filter(selected_industry)
    selected_level = _normalize_optional_filter(selected_level)
    selected_company = _normalize_optional_filter(selected_company)

    df = _load_jobs_raw(
        limit=JOBS_LIST_LIMIT,
        search=(api_search_text or "").strip(),
        source=source,
        selected_function=selected_function,
        selected_industry=selected_industry,
        selected_level=selected_level,
        selected_company=selected_company,
    )
    if df.empty:
        return (
            filter_options.get("source_options", []),
            filter_options.get("function_options", []),
            filter_options.get("industry_options", []),
            filter_options.get("level_options", []),
            filter_options.get("company_options", []),
            "Нийт мөр: 0",
            [],
            [],
            [],
        )

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

    source_options = filter_options.get("source_options", [])
    function_options = filter_options.get("function_options", [])
    industry_options = filter_options.get("industry_options", [])
    level_options = filter_options.get("level_options", [])
    company_options = filter_options.get("company_options", [])

    # Convert values for table rendering (human-readable).
    object_columns = view_df.select_dtypes(include=["object"]).columns.tolist()
    for col in object_columns:
        view_df[col] = view_df[col].map(_format_jobs_cell_value)

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
        view_df.to_dict("records"),
    )


@callback(
    Output("jobs-local-source-filter", "options"),
    Output("jobs-local-level-filter", "options"),
    Input("jobs-table-raw", "data"),
)
def update_jobs_local_filter_options(raw_rows: Optional[List[Dict[str, object]]]):
    if not raw_rows:
        return [], []

    df = pd.DataFrame(raw_rows)
    if df.empty:
        return [], []

    source_col = _first_existing_col(df, ["source_job", "source", "platform", "site_name", "website", "Эх сурвалж"])
    level_col = _first_existing_col(df, ["job_level", "level", "Түвшин"])

    def _options_for(column_name: Optional[str]) -> List[Dict[str, str]]:
        if not column_name or column_name not in df.columns:
            return []
        values: List[str] = []
        for value in df[column_name].dropna().tolist():
            if _is_all_like(value):
                continue
            cleaned = str(value).strip()
            if cleaned:
                values.append(cleaned)
        unique_sorted = sorted(set(values), key=lambda item: _norm_text(item))
        return [{"label": value, "value": value} for value in unique_sorted]

    return _options_for(source_col), _options_for(level_col)


@callback(
    Output("jobs-table", "data", allow_duplicate=True),
    Output("jobs-count", "children", allow_duplicate=True),
    Input("jobs-local-search", "value"),
    Input("jobs-local-source-filter", "value"),
    Input("jobs-local-level-filter", "value"),
    Input("jobs-table-raw", "data"),
    prevent_initial_call=True,
)
def filter_jobs_table_local(
    local_search: Optional[str],
    local_source_values: object,
    local_level_values: object,
    raw_rows: Optional[List[Dict[str, object]]],
):
    if not raw_rows:
        return [], "Нийт мөр: 0"

    df = pd.DataFrame(raw_rows)
    if df.empty:
        return [], "Нийт мөр: 0"

    source_col = _first_existing_col(df, ["source_job", "source", "platform", "site_name", "website", "Эх сурвалж"])
    level_col = _first_existing_col(df, ["job_level", "level", "Түвшин"])

    selected_sources = _safe_selected_values(local_source_values)
    selected_levels = _safe_selected_values(local_level_values)

    if source_col and selected_sources:
        source_norm = {_norm_text(value) for value in selected_sources}
        df = df[df[source_col].astype(str).map(_norm_text).isin(source_norm)]

    if level_col and selected_levels:
        level_norm = {_norm_text(value) for value in selected_levels}
        df = df[df[level_col].astype(str).map(_norm_text).isin(level_norm)]

    search_text = _norm_text(local_search)
    if search_text:
        tokens = _expand_search_tokens(search_text)
        alias_phrases = _expand_search_alias_phrases(search_text)
        preferred_cols = [
            "title",
            "job_title",
            "company_name",
            "job_function",
            "job_industry",
            "job_level",
            "source_job",
            "source",
            "platform",
            "description",
            "requirements",
            "requirement_reasoning",
            "benefits",
            "benefits_reasoning",
            "Тайлбар",
            "Албан тушаал",
            "Компани",
            "Салбар",
            "Түвшин",
            "Эх сурвалж",
        ]
        search_cols = [column for column in preferred_cols if column in df.columns] or list(df.columns)
        normalized_cols = {column: df[column].astype(str).map(_norm_text) for column in search_cols}

        base_mask = pd.Series(True, index=df.index)
        if tokens:
            for token in tokens:
                any_col_match = pd.Series(False, index=df.index)
                for column in search_cols:
                    any_col_match = any_col_match | normalized_cols[column].str.contains(token, regex=False, na=False)
                base_mask = base_mask & any_col_match

        alias_mask = pd.Series(False, index=df.index)
        if alias_phrases:
            for alias in alias_phrases:
                alias_match = pd.Series(False, index=df.index)
                for column in search_cols:
                    alias_match = alias_match | normalized_cols[column].str.contains(alias, regex=False, na=False)
                alias_mask = alias_mask | alias_match

        df = df[base_mask | alias_mask]

    filtered_rows = df.to_dict("records")
    return filtered_rows, f"Нийт мөр: {len(filtered_rows):,}"


@callback(
    Output("jobs-excel-download", "data"),
    Input("download-jobs-excel", "n_clicks"),
    State("jobs-table", "data"),
    prevent_initial_call=True,
)
def download_jobs_excel(n_clicks: int, table_data: Optional[List[Dict[str, object]]]):
    if not n_clicks or not table_data:
        return dash.no_update

    payload = {
        "rows": table_data,
        "filename": "jobs_list.xlsx",
    }
    excel_bytes = _post_api_bytes("download/jobs-report", payload=payload)
    if excel_bytes:
        return _send_bytes_download(excel_bytes, "jobs_list.xlsx")

    return dash.no_update


@callback(
    # --- filter options & values ---
    Output("main-industry", "options"),
    Output("main-function", "options"),
    Output("main-level", "options"),
    Output("main-category", "options"),
    Output("main-year", "options"),
    Output("main-month", "options"),
    Output("main-industry", "value"),
    Output("main-function", "value"),
    Output("main-level", "value"),
    Output("main-category", "value"),
    Output("main-year", "value"),
    Output("main-month", "value"),
    # --- dashboard charts & tables ---
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
    Input("main-industry", "value"),
    Input("main-function", "value"),
    Input("main-level", "value"),
    Input("main-category", "value"),
    Input("main-year", "value"),
    Input("main-month", "value"),
    Input("interval-component", "n_intervals"),
)
def update_dashboard(
    selected_industry: Optional[str],
    selected_function: Optional[str],
    selected_level: Optional[str],
    selected_category: Optional[str],
    selected_year: Optional[str],
    selected_month: Optional[str],
    n_intervals: int,
):
    # ── normalise raw filter values ──
    selected_industry = _normalize_optional_filter(selected_industry)
    selected_function = _normalize_optional_filter(selected_function)
    selected_level = _normalize_optional_filter(selected_level)
    selected_category = _normalize_optional_filter(selected_category)
    selected_year = _normalize_optional_filter(selected_year)
    selected_month = _normalize_optional_filter(selected_month)

    df = _exclude_all_titles(_load_data_main())

    # ── empty-data early return (filter defaults + empty charts) ──
    _empty_filters = ([], [], [], [], [], [], None, None, None, None, None, None)
    if df.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return (*_empty_filters, _build_kpi_cards(df), empty, empty, empty, empty, empty, empty, [], [], [], [], [], [], [])

    # ── cascading filter-option logic (single data load) ──
    industry_values = _distinct_non_empty_values(df, "industry")
    industry_options = [{"label": v, "value": v} for v in industry_values]
    if selected_industry and selected_industry not in industry_values:
        selected_industry = None

    df_industry = _apply_main_dimension_filters(df, selected_industry=selected_industry)
    function_values = _distinct_non_empty_values(df_industry, "job_function")
    function_options = [{"label": v, "value": v} for v in function_values]
    if selected_function and selected_function not in function_values:
        selected_function = None

    df_function = _apply_main_dimension_filters(
        df,
        selected_industry=selected_industry,
        selected_function=selected_function,
    )
    level_values = _distinct_non_empty_values(df_function, "job_level")
    level_options = [{"label": v, "value": v} for v in level_values]
    if selected_level and selected_level not in level_values:
        selected_level = None

    df_level = _apply_main_dimension_filters(
        df,
        selected_industry=selected_industry,
        selected_function=selected_function,
        selected_level=selected_level,
    )
    category_values = _distinct_non_empty_values(df_level, "techpack_category")
    category_options = [{"label": v, "value": v} for v in category_values]
    if selected_category and selected_category not in category_values:
        selected_category = None

    df_category = _apply_main_dimension_filters(
        df,
        selected_industry=selected_industry,
        selected_function=selected_function,
        selected_level=selected_level,
        selected_category=selected_category,
    )
    year_series = pd.to_numeric(df_category["year"], errors="coerce") if "year" in df_category.columns else pd.Series(dtype=float)
    year_values = sorted({int(v) for v in year_series.dropna().tolist()}, reverse=True)
    year_options = [{"label": str(v), "value": str(v)} for v in year_values]
    if selected_year and selected_year not in {str(v) for v in year_values}:
        selected_year = None

    df_year = _apply_main_dimension_filters(
        df,
        selected_industry=selected_industry,
        selected_function=selected_function,
        selected_level=selected_level,
        selected_category=selected_category,
        selected_year=selected_year,
    )
    month_series = pd.to_numeric(df_year["month"], errors="coerce") if "month" in df_year.columns else pd.Series(dtype=float)
    month_values = sorted({int(v) for v in month_series.dropna().tolist()})
    month_options = [{"label": f"{v:02d}", "value": str(v)} for v in month_values]
    if selected_month and selected_month not in {str(v) for v in month_values}:
        selected_month = None

    filter_results = (
        industry_options,
        function_options,
        level_options,
        category_options,
        year_options,
        month_options,
        selected_industry,
        selected_function,
        selected_level,
        selected_category,
        selected_year,
        selected_month,
    )

    # ── apply all validated filters for chart data ──
    df_all = _apply_main_dimension_filters(
        df,
        selected_function=selected_function,
        selected_industry=selected_industry,
        selected_level=selected_level,
        selected_category=selected_category,
        selected_year=selected_year,
        selected_month=selected_month,
    )
    if df_all.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return (*filter_results, _build_kpi_cards(df_all), empty, empty, empty, empty, empty, empty, [], [], [], [], [], [], [])

    df_latest = _latest_per_title(df_all)
    display_label = "Ажлын ангилал"
    is_all_selected = True
    df_selected = df_all.copy()
    df_selected_latest = df_latest.copy()

    # ── Build detail table from df_latest (all filtered titles, not 3-month restricted) ──
    _detail_df = df_latest.copy()
    if "experience_salary_breakdown" in _detail_df.columns:
        _detail_df["experience_salary_breakdown"] = _detail_df["experience_salary_breakdown"].apply(_format_experience_breakdown_for_table)
    _detail_df = _detail_df.rename(
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
    _wanted = ["Ажлын ангилал", "Доод цалин", "Дээд цалин", "Дундаж цалин", "Зарын тоо", "Zangia", "Lambda"]
    _detail_columns = [{"name": c, "id": c} for c in _wanted if c in _detail_df.columns]
    for _col in ["Доод цалин", "Дээд цалин", "Дундаж цалин", "Зарын тоо", "Zangia", "Lambda"]:
        if _col in _detail_df.columns:
            _detail_df[_col] = _detail_df[_col].apply(_format_grouped_number)
    _detail_data = _detail_df[[c["id"] for c in _detail_columns]].to_dict("records")
    _detail_title_options: List[Dict[str, str]] = []
    if "Ажлын ангилал" in _detail_df.columns:
        _detail_title_options = [
            {"label": str(t), "value": str(t)}
            for t in sorted(_detail_df["Ажлын ангилал"].dropna().astype(str).unique().tolist())
        ]

    # Filter to the latest 3 months of data for all charts except trend
    if "year" in df_selected_latest.columns and "month" in df_selected_latest.columns:
        _tmp = df_selected_latest.copy()
        _tmp["_y"] = pd.to_numeric(_tmp["year"], errors="coerce")
        _tmp["_m"] = pd.to_numeric(_tmp["month"], errors="coerce")
        _valid = _tmp.dropna(subset=["_y", "_m"])
        if not _valid.empty:
            _valid["_period"] = _valid["_y"] * 100 + _valid["_m"]
            latest_periods = sorted(_valid["_period"].unique(), reverse=True)[:3]
            _tmp_all = df_selected_latest.copy()
            _tmp_all["_period"] = (
                pd.to_numeric(_tmp_all["year"], errors="coerce") * 100
                + pd.to_numeric(_tmp_all["month"], errors="coerce")
            )
            df_selected_latest = _tmp_all[_tmp_all["_period"].isin(latest_periods)].drop(columns=["_period"]).copy()

    kpis = _build_kpi_cards(df_selected_latest)
    if df_selected_latest.empty:
        empty = _empty_figure("Өгөгдөл олдсонгүй")
        return (*filter_results, kpis, empty, empty, empty, empty, empty, empty, [], [], _detail_data, _detail_columns, _detail_data, _detail_title_options, [])

    bar_df = df_selected_latest.groupby("title", as_index=False).agg(
        average_salary=("average_salary", "mean")
    )
    bar_df["title_short"] = bar_df["title"].apply(_shorten_label)
    bar_df = bar_df.groupby("title_short", as_index=False).agg(
        average_salary=("average_salary", "mean")
    )
    bar_df = bar_df.sort_values(by="average_salary", ascending=False).head(5)
    bar_fig = px.bar(
        bar_df,
        y="title_short",
        x="average_salary",
        orientation="h",
        title=f"Сарын дундаж цалин ({display_label})",
        labels={"title_short": display_label, "average_salary": "Дундаж цалин (₮)"},
        color_discrete_sequence=[COLORS["primary"]],
    )
    bar_fig.update_layout(height=420, yaxis={"automargin": True, "categoryorder": "total ascending"})
    _apply_chart_style(bar_fig)

    range_df = df_selected_latest.groupby("title", as_index=False).agg(
        min_salary=("min_salary", "min"),
        max_salary=("max_salary", "max"),
        average_salary=("average_salary", "mean"),
    )
    range_df["title_short"] = range_df["title"].apply(_shorten_label)
    range_df = range_df.groupby("title_short", as_index=False).agg(
        min_salary=("min_salary", "min"),
        max_salary=("max_salary", "max"),
        average_salary=("average_salary", "mean"),
    )
    range_df = range_df.sort_values("average_salary", ascending=False).head(5)
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
            hovertemplate="%{y}<br>Доод: %{x:,.0f} ₮<extra></extra>",
        )
    )
    range_fig.add_trace(
        go.Scatter(
            x=range_df["average_salary"],
            y=range_df["title_short"],
            mode="markers",
            name="Дундаж",
            marker={"size": 10, "color": "#3b82f6", "symbol": "diamond"},
            hovertemplate="%{y}<br>Дундаж: %{x:,.0f} ₮<extra></extra>",
        )
    )
    range_fig.add_trace(
        go.Scatter(
            x=range_df["max_salary"],
            y=range_df["title_short"],
            mode="markers",
            name="Дээд",
            marker={"size": 9, "color": "#dc2626", "symbol": "circle"},
            hovertemplate="%{y}<br>Дээд: %{x:,.0f} ₮<extra></extra>",
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
        count_df = df_selected_latest.groupby("title", as_index=False).agg(job_count=("job_count", "sum"))
        count_df["title_short"] = count_df["title"].apply(_shorten_label)
        count_df = count_df.groupby("title_short", as_index=False).agg(job_count=("job_count", "sum"))
        count_df = count_df.sort_values(by="job_count", ascending=False).head(5)
        count_fig = px.bar(
            count_df,
            y="title_short",
            x="job_count",
            orientation="h",
            title=f"Ажлын байрны тоо ({display_label})",
            labels={"title_short": display_label, "job_count": "Ажлын байр"},
            color_discrete_sequence=[COLORS["warning"]],
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
    )
    compare_df["title_short"] = compare_df["title"].apply(_shorten_label)
    compare_df = (
        compare_df.groupby("title_short", as_index=False)
        .agg(min_salary=("min_salary", "min"), average_salary=("average_salary", "mean"), max_salary=("max_salary", "max"))
        .sort_values("average_salary", ascending=False)
        .head(5)
    )
    if compare_df.empty:
        compare_fig = _empty_figure("Харьцуулах өгөгдөл алга")
    else:
        compare_long = compare_df.melt(id_vars=["title_short"], value_vars=["min_salary", "average_salary", "max_salary"], var_name="metric", value_name="salary")
        compare_long["metric"] = compare_long["metric"].map({"min_salary": "Доод", "average_salary": "Дундаж", "max_salary": "Дээд"})
        compare_fig = px.bar(
            compare_long,
            x="title_short",
            y="salary",
            color="metric",
            barmode="group",
            title=f"Сонгосон ангиллуудын цалингийн харьцуулалт ({display_label})",
            labels={"title_short": display_label, "salary": "Цалин (₮)", "metric": "Үзүүлэлт"},
            color_discrete_map={"Доод": "#93c5fd", "Дундаж": COLORS["primary"], "Дээд": "#1d4ed8"},
        )
        compare_fig.update_traces(hovertemplate="%{fullData.name}: %{y:,.0f} ₮<extra></extra>")
        compare_fig.update_layout(xaxis_tickangle=-20)
        _apply_chart_style(compare_fig)

    experience_data, experience_columns = _build_experience_breakdown_table(df_selected_latest, is_all_selected=is_all_selected)

    return (
        *filter_results,
        kpis,
        bar_fig,
        range_fig,
        count_fig,
        trend_fig,
        source_fig,
        compare_fig,
        experience_data,
        experience_columns,
        _detail_data,
        _detail_columns,
        _detail_data,
        _detail_title_options,
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
        selected = {str(v) for v in selected_titles if v and not _is_all_like(v)}
        if selected:
            rows = [row for row in rows if str(row.get("Ажлын ангилал", "")) in selected]

    search_normalized = _norm_text(search_text)
    if search_normalized:
        tokens = [t for t in search_normalized.split(" ") if t]
        filtered: List[Dict[str, object]] = []
        for row in rows:
            row_text = _norm_text(" ".join(str(v) for v in row.values()))
            if all(token in row_text for token in tokens):
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

    payload = {
        "rows": table_data,
        "filename": "salary_report.xlsx",
    }
    excel_bytes = _post_api_bytes("download/dashboard-report", payload=payload)
    if excel_bytes:
        return _send_bytes_download(excel_bytes, "salary_report.xlsx")

    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True, port="8006")