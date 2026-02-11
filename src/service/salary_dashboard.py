"""
Dashboard for salary_calculation_output table.
Displays salary analysis with interactive charts and filters.

Run:
    python -m src.service.salary_dashboard
"""

import os
import io
import uuid
from typing import Dict, List, Optional

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from openpyxl.styles import Alignment, Font, PatternFill
from dash import Input, Output, State, callback, dcc, html, dash_table
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

N8N_AGENT_URL = os.getenv("N8N_AGENT_URL", "").strip()

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
    "function": "Чиг үүрэг",
    "job_level": "Түвшин",
    "industry": "Үйл ажиллагааны чиглэл/Салбар",
    "techpack_category": "Ангилал",
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _format_mnt(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f} ₮"


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


def _build_kpi_cards(df: pd.DataFrame) -> List[html.Div]:
    if df.empty:
        return [
            html.Div(
                [
                    html.H3("N/A", style={"color": COLORS["dark"], "margin": 0}),
                    html.P("No data", style={"color": COLORS["muted"], "margin": 0}),
                ],
                style=KPI_STYLE,
            )
        ]

    total_jobs = int(df["job_count"].sum()) if "job_count" in df.columns else 0
    avg_salary = df["average_salary"].mean() if "average_salary" in df.columns else None
    min_salary = df["min_salary"].min() if "min_salary" in df.columns else None
    max_salary = df["max_salary"].max() if "max_salary" in df.columns else None

    return [
        html.Div(
            [
                html.H3(_format_mnt(avg_salary), style={"color": COLORS["dark"], "margin": 0}),
                html.P("Дундаж цалин", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=KPI_STYLE,
        ),
        html.Div(
            [
                html.H3(_format_mnt(min_salary), style={"color": COLORS["dark"], "margin": 0}),
                html.P("Хамгийн бага", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=KPI_STYLE,
        ),
        html.Div(
            [
                html.H3(_format_mnt(max_salary), style={"color": COLORS["dark"], "margin": 0}),
                html.P("Хамгийн их", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=KPI_STYLE,
        ),
        html.Div(
            [
                html.H3(f"{total_jobs:,}", style={"color": COLORS["dark"], "margin": 0}),
                html.P("Нийт ажлын байр", style={"color": COLORS["muted"], "margin": 0}),
            ],
            style=KPI_STYLE,
        ),
    ]


def _render_chat(history: List[Dict[str, str]]) -> List[html.Div]:
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
        bubble_color = COLORS["primary"] if is_user else COLORS["card"]
        text_color = "white" if is_user else COLORS["text"]
        align = "flex-end" if is_user else "flex-start"
        items.append(
            html.Div(
                [
                    html.Div(
                        item.get("content", ""),
                        style={
                            "whiteSpace": "pre-wrap",
                            "lineHeight": "1.4",
                            "color": text_color,
                        },
                    )
                ],
                style={
                    "alignSelf": align,
                    "backgroundColor": bubble_color,
                    "padding": "10px 12px",
                    "borderRadius": "14px",
                    "marginBottom": "10px",
                    "maxWidth": "85%",
                    "maxHeight": "180px",
                    "overflowY": "auto",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
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
    style={"backgroundColor": COLORS["bg"], "padding": "32px", "fontFamily": "Arial, sans-serif"},
    children=[
        html.H1("💰 Salary Analysis Agent", style={"color": COLORS["dark"], "marginBottom": "24px"}),
        dcc.Interval(id="interval-component", interval=5 * 60 * 1000, n_intervals=0),
        dcc.Store(id="chat-store", data=[{"role": "assistant", "content": "Сайн байна уу! Танд юугаар туслах вэ?"}]),
        dcc.Store(id="chat-request"),
        dcc.Store(id="session-store", storage_type="session"),
        dcc.Download(id="excel-download"),
        html.Div(
            style={"display": "flex", "gap": "24px", "alignItems": "flex-start"},
            children=[
                html.Div(
                    style={"flex": "2", "minWidth": "640px"},
                    children=[
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.H2("Шүүлтүүр", style={"color": COLORS["dark"], "marginTop": 0}),
                                dcc.RadioItems(
                                    id="type-selector",
                                    options=_safe_type_options(_load_data_main()),
                                    value="function",
                                    inline=True,
                                    labelStyle={"marginRight": "16px", "color": COLORS["text"]},
                                ),
                                html.Div(style={"height": "12px"}),
                                dcc.Dropdown(id="title-filter", placeholder="Сонголт хийх"),
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
                                    children=[dcc.Graph(id="salary-bar")],
                                ),
                                html.Div(
                                    id="salary-range-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Graph(id="salary-range")],
                                ),
                                html.Div(
                                    id="count-bar-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Graph(id="count-bar")],
                                ),
                                html.Div(
                                    id="trend-line-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Graph(id="trend-line")],
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
                                    children=[dcc.Graph(id="source-pie")],
                                ),
                                html.Div(
                                    id="avg-scatter-card",
                                    className="card",
                                    style=CARD_STYLE,
                                    children=[dcc.Graph(id="avg-scatter")],
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
                                dash_table.DataTable(
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
                            ],
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1", "maxWidth": "460px"},
                    children=[
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.H2("💬 Chatbot", style={"color": COLORS["dark"], "marginTop": 0}),
                                html.P(
                                    "Ажлын байрны цалингийн талаар асуулт асууж, шинжилгээ авах боломжтой чатбот.",
                                    style={"color": COLORS["muted"], "marginTop": 0},
                                ),
                                html.Div(
                                    id="chat-output",
                                    children=_render_chat(
                                        [{"role": "assistant", "content": "Сайн байна уу! Танд юугаар туслах вэ?"}]
                                    ),
                                    style={
                                        "flex": "1",
                                        "minHeight": "360px",
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
                                        "height": "40px",
                                        "padding": "10px",
                                        "borderRadius": "8px",
                                        "border": f"1px solid {COLORS['muted']}40",
                                        "marginBottom": "10px",
                                    },
                                ),
                                dcc.Textarea(
                                    id="chat-input",
                                    placeholder="Асуумаар зүйлээ бичнэ үү...",
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
                                        "height": "44px",
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
        return [], None

    df = _load_data_main()
    df = _filter_by_type(df, selected_type)
    df = _exclude_all_titles(df)
    df = _latest_per_title(df)
    if df.empty:
        return [], None
    options = [
        {"label": title, "value": title}
        for title in sorted(df["title"].dropna().unique().tolist())
    ]
    return options, (options[0]["value"] if options else None)


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
    Output("avg-scatter", "figure"),
    Output("detail-table", "data"),
    Output("detail-table", "columns"),
    Input("type-selector", "value"),
    Input("title-filter", "value"),
    Input("interval-component", "n_intervals"),
)
def update_charts(selected_type: str, selected_title: Optional[str], n_intervals: int):
    if not selected_type:
        empty = _empty_figure("No data available")
        return _build_kpi_cards(pd.DataFrame()), empty, empty, empty, empty, empty, empty, [], []

    df_all = _load_data_main()
    df_all = _filter_by_type(df_all, selected_type)
    df_all = _exclude_all_titles(df_all)
    if df_all.empty:
        empty = _empty_figure("No data available")
        return _build_kpi_cards(df_all), empty, empty, empty, empty, empty, empty, [], []

    df_latest = _latest_per_title(df_all)

    display_label = TYPE_LABELS.get(selected_type, "Төрөл")

    if selected_title and selected_title in df_all["title"].values:
        df_selected = df_all[df_all["title"] == selected_title].copy()
        df_selected_latest = df_latest[df_latest["title"] == selected_title].copy()
    else:
        df_selected = df_all.copy()
        df_selected_latest = df_latest.copy()

    kpis = _build_kpi_cards(df_selected_latest)

    bar_df = df_latest.groupby("title", as_index=False)["average_salary"].mean()
    bar_df["title_short"] = bar_df["title"].apply(_shorten_label)
    bar_fig = px.bar(
        bar_df,
        y="title_short",
        x="average_salary",
        orientation="h",
        title=f"{display_label} - Дундаж цалин",
        labels={"title_short": display_label, "average_salary": "Дундаж цалин (₮)"},
        color_discrete_sequence=[COLORS["primary"]],
        hover_data={"title": True, "title_short": False, "average_salary": True},
    )
    bar_fig.update_layout(
        height=460,
        margin={"l": 120, "r": 20, "t": 50, "b": 40},
        yaxis={"automargin": True, "categoryorder": "total ascending"},
    )

    range_df = df_latest.groupby("title", as_index=False).agg(
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
        title=f"{display_label} - Цалингийн хүрээ",
        barmode="group",
        height=460,
        margin={"l": 120, "r": 20, "t": 50, "b": 40},
        xaxis_title="₮",
        yaxis={"automargin": True, "categoryorder": "total ascending"},
    )

    if "job_count" in df_latest.columns:
        count_df = df_latest.groupby("title", as_index=False)["job_count"].sum()
        count_df["title_short"] = count_df["title"].apply(_shorten_label)
        count_fig = px.bar(
            count_df,
            y="title_short",
            x="job_count",
            orientation="h",
            title=f"{display_label} - Ажлын байрны тоо",
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
        count_fig = _empty_figure("No count data")

    if "period" in df_selected.columns and df_selected["period"].notna().any():
        trend_df = df_selected.groupby("period", as_index=False)["average_salary"].mean()
        trend_fig = px.line(
            trend_df,
            x="period",
            y="average_salary",
            markers=True,
            title=f"{display_label} - Цаг хугацааны тренд",
            labels={"period": "Сар", "average_salary": "Дундаж цалин (₮)"},
        )
        trend_fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 60})
    else:
        trend_fig = _empty_figure("No time series data")

    if "zangia_count" in df_latest.columns and "lambda_count" in df_latest.columns:
        source_total = {
            "Zangia": int(df_latest["zangia_count"].sum()),
            "Lambda Global": int(df_latest["lambda_count"].sum()),
        }
        source_fig = px.pie(
            names=list(source_total.keys()),
            values=list(source_total.values()),
            hole=0.45,
            title="Эх сурвалжийн харьцаа",
            color_discrete_sequence=[COLORS["primary"], COLORS["accent"]],
        )
        source_fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
    else:
        source_fig = _empty_figure("No source data")

    if "period" in df_all.columns and df_all["period"].notna().any():
        avg_scatter_df = df_all.groupby(["period", "title"], as_index=False)["average_salary"].mean()
        avg_scatter = px.scatter(
            avg_scatter_df,
            x="period",
            y="average_salary",
            color="title",
            title=f"Дундаж цалингийн чиг хандлага ({display_label})",
            labels={"period": "Он-Сар", "average_salary": "Дундаж цалин (₮)", "title": display_label},
        )
        avg_scatter.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 60})
    else:
        avg_scatter = _empty_figure("No time series data")

    table_df = df_latest.copy()
    table_df = table_df.rename(
        columns={
            "title": "Ажлын ангилал",
            "min_salary": "Доод цалин",
            "max_salary": "Дээд цалин",
            "average_salary": "Дундаж цалин",
            "job_count": "Зарын тоо",
            "zangia_count": "Zangia",
            "lambda_count": "Lambda",
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
        ]
        if col in table_df.columns
    ]
    table_data = table_df[ [c["id"] for c in table_columns] ].to_dict("records")

    return kpis, bar_fig, range_fig, count_fig, trend_fig, source_fig, avg_scatter, table_data, table_columns


@callback(
    Output("salary-bar-card", "className"),
    Output("salary-range-card", "className"),
    Output("count-bar-card", "className"),
    Output("trend-line-card", "className"),
    Output("source-pie-card", "className"),
    Output("avg-scatter-card", "className"),
    Output("table-card", "className"),
    Input("salary-bar", "loading_state"),
    Input("salary-range", "loading_state"),
    Input("count-bar", "loading_state"),
    Input("trend-line", "loading_state"),
    Input("source-pie", "loading_state"),
    Input("avg-scatter", "loading_state"),
    Input("detail-table", "loading_state"),
)
def update_loading_skeleton(*states):
    def _cls(state):
        if state and state.get("is_loading"):
            return "card skeleton"
        return "card"

    return tuple(_cls(state) for state in states)


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
    history: List[Dict[str, str]],
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
    # Remove 'pending' key for rendering
    clean_history: List[Dict[str, str]] = [{k: v for k, v in item.items() if k != "pending" and isinstance(v, str)} for item in updated_history]
    return updated_history, _render_chat(clean_history), "", request_payload

    request_payload = {"session_id": session_value, "message": message.strip()}
    # Remove 'pending' key for rendering
    clean_history = [{k: v for k, v in item.items() if k != "pending"} for item in updated_history]
    return updated_history, _render_chat(clean_history), "", request_payload


@callback(
    Output("chat-store", "data", allow_duplicate=True),
    Output("chat-output", "children", allow_duplicate=True),
    Input("chat-request", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def fetch_chat_response(request_payload: Optional[Dict[str, str]], history: List[Dict[str, str]]):
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
    