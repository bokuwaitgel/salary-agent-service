"""
Plotly Dash dashboard for salary analysis.

Reads from the database (job_category_salary / job_level_salary tables)
and renders interactive charts.  Data is keyed by month+year so each
time you add a new batch the trend graphs update automatically.

Run:
    python -m src.service.dashboard
"""

import io
import os
import tempfile

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import ClientsideFunction, Input, Output, State, callback, dcc, html
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.service.report import generate_salary_report

load_dotenv()

# ── DB helper ───────────────────────────────────────────────────────────────

def _engine():
    return create_engine(
        os.getenv("DATABASE_URI", "sqlite:///products.db"),
        pool_pre_ping=True,
    )


def _read_table(table: str) -> pd.DataFrame:
    engine = _engine()
    df = pd.read_sql_table(table, engine)
    return df


def _load_data():
    cat = _read_table("job_category_salary")
    lvl = _read_table("job_level_salary")
    # Build a period label for trend axes
    for df in (cat, lvl):
        if "year" in df.columns and "month" in df.columns:
            df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    return cat, lvl


# ── Colour palette ──────────────────────────────────────────────────────────

COLORS = {
    "bg": "#F7F9FC",
    "card": "#FFFFFF",
    "primary": "#2E75B6",
    "secondary": "#548235",
    "accent": "#ED7D31",
    "dark": "#1F4E79",
    "text": "#333333",
    "muted": "#888888",
}

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "12px",
    "padding": "20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "marginBottom": "20px",
}

KPI_STYLE = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "12px",
    "padding": "24px 16px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "textAlign": "center",
    "flex": "1",
    "minWidth": "160px",
}

# ── App ─────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    title="Цалингийн Судалгаа",
    suppress_callback_exceptions=True,
)

# Inject CSS keyframes for the custom loading spinner
app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @keyframes spin {
                0%   { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            ._dash-loading {
                transition: opacity 0.3s ease;
            }
            .download-btn-loading {
                animation: pulse 1.2s ease-in-out infinite;
                pointer-events: none;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>'''

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "fontFamily": "Segoe UI, sans-serif"},
    children=[
        # Header
        html.Div(
            style={
                "background": f"linear-gradient(135deg, {COLORS['dark']}, {COLORS['primary']})",
                "padding": "28px 40px",
                "color": "white",
            },
            children=[
                html.H1("Цалингийн Судалгааны Dashboard", style={"margin": 0, "fontSize": "28px"}),
                html.P("Ажлын ангилал болон албан тушаалын түвшингээр", style={"margin": "4px 0 0", "opacity": 0.8}),
            ],
        ),

        # Controls
        html.Div(
            style={"padding": "20px 40px 0", "display": "flex", "gap": "20px", "flexWrap": "wrap", "alignItems": "flex-end"},
            children=[
                html.Div([
                    html.Label("Өгөгдлийн төрөл", style={"fontWeight": "bold", "marginBottom": "4px", "display": "block"}),
                    dcc.Dropdown(
                        id="data-type",
                        options=[
                            {"label": "Ажлын ангилал", "value": "category"},
                            {"label": "Албан тушаалын түвшин", "value": "level"},
                        ],
                        value="category",
                        clearable=False,
                        style={"width": "260px"},
                    ),
                ]),
                html.Div([
                    html.Label("Он-Сар", style={"fontWeight": "bold", "marginBottom": "4px", "display": "block"}),
                    dcc.Dropdown(id="period-filter", placeholder="Бүгд", style={"width": "200px"}),
                ]),
                html.Div(
                    style={"position": "relative", "display": "inline-flex", "alignItems": "center"},
                    children=[
                        html.Button(
                            id="download-excel-btn",
                            n_clicks=0,
                            children=[
                                html.Span("📥 Excel татах", id="download-btn-text"),
                            ],
                            style={
                                "backgroundColor": COLORS["secondary"],
                                "color": "white",
                                "border": "none",
                                "borderRadius": "8px",
                                "padding": "10px 24px",
                                "fontSize": "14px",
                                "fontWeight": "bold",
                                "cursor": "pointer",
                                "boxShadow": "0 2px 6px rgba(0,0,0,0.12)",
                                "transition": "all 0.3s ease",
                                "display": "inline-flex",
                                "alignItems": "center",
                                "gap": "8px",
                            },
                        ),
                        dcc.Download(id="download-excel"),
                        # Hidden store to track loading state
                        dcc.Store(id="download-loading-state", data=False),
                    ],
                ),
            ],
        ),

        # KPI row (with loading spinner)
        dcc.Loading(
            id="loading-kpi",
            type="circle",
            color=COLORS["primary"],
            children=html.Div(id="kpi-row", style={"padding": "20px 40px", "display": "flex", "gap": "16px", "flexWrap": "wrap"}),
        ),

        # Main content (with loading overlay)
        dcc.Loading(
            id="loading-charts",
            type="default",
            color=COLORS["primary"],
            overlay_style={"visibility": "visible", "opacity": 0.4, "backgroundColor": "white"},
            custom_spinner=html.Div([
                html.Div(style={
                    "width": "48px", "height": "48px",
                    "border": f"4px solid {COLORS['bg']}",
                    "borderTop": f"4px solid {COLORS['primary']}",
                    "borderRadius": "50%",
                    "animation": "spin 0.8s linear infinite",
                }),
                html.Div("Өгөгдөл ачааллаж байна...", style={
                    "marginTop": "12px", "color": COLORS["dark"],
                    "fontWeight": "600", "fontSize": "14px",
                }),
            ], style={"display": "flex", "flexDirection": "column", "alignItems": "center", "padding": "40px"}),
            children=html.Div(
                style={"padding": "0 40px 40px"},
                children=[
                    # Row 1: salary comparison + job count
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                        children=[
                            html.Div(dcc.Graph(id="salary-bar"), style=CARD_STYLE),
                            html.Div(dcc.Graph(id="job-count-bar"), style=CARD_STYLE),
                        ],
                    ),
                    # Row 2: source pie + salary range
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                        children=[
                            html.Div(dcc.Graph(id="source-pie"), style=CARD_STYLE),
                            html.Div(dcc.Graph(id="salary-range"), style=CARD_STYLE),
                        ],
                    ),
                    # Row 3: trend over time (full width)
                    html.Div(dcc.Graph(id="trend-line"), style=CARD_STYLE),
                    # Row 4: trend job count over time
                    html.Div(dcc.Graph(id="trend-job-count"), style=CARD_STYLE),
                    # Row 5: data table
                    html.Div(id="data-table-container", style=CARD_STYLE),
                ],
            ),
        ),
    ],
)


# ── Callbacks ───────────────────────────────────────────────────────────────

@callback(
    Output("period-filter", "options"),
    Input("data-type", "value"),
)
def update_period_options(data_type):
    cat, lvl = _load_data()
    df = cat if data_type == "category" else lvl
    if "period" not in df.columns or df.empty:
        return []
    periods = sorted(df["period"].dropna().unique())
    return [{"label": p, "value": p} for p in periods]


@callback(
    Output("kpi-row", "children"),
    Output("salary-bar", "figure"),
    Output("job-count-bar", "figure"),
    Output("source-pie", "figure"),
    Output("salary-range", "figure"),
    Output("trend-line", "figure"),
    Output("trend-job-count", "figure"),
    Output("data-table-container", "children"),
    Input("data-type", "value"),
    Input("period-filter", "value"),
)
def update_dashboard(data_type, period):
    cat_all, lvl_all = _load_data()
    df_all = cat_all if data_type == "category" else lvl_all
    name_col = "job_category" if data_type == "category" else "job_level"
    label = "Ажлын ангилал" if data_type == "category" else "Албан тушаалын түвшин"

    # Filter by period for snapshot views
    if period and "period" in df_all.columns:
        df = df_all[df_all["period"] == period].copy()
    else:
        # latest period
        if "period" in df_all.columns and not df_all.empty:
            latest = df_all["period"].max()
            df = df_all[df_all["period"] == latest].copy()
        else:
            df = df_all.copy()

    # ── KPI cards ───────────────────────────────────────────────────────
    total_items = len(df)
    total_jobs = int(df["job_count"].sum()) if not df.empty else 0
    avg_salary = int(df["average_salary"].mean()) if not df.empty else 0
    max_salary = int(df["max_salary"].max()) if not df.empty else 0
    min_salary = int(df["min_salary"].min()) if not df.empty else 0

    def kpi_card(title, value):
        return html.Div(style=KPI_STYLE, children=[
            html.Div(value, style={"fontSize": "26px", "fontWeight": "bold", "color": COLORS["dark"]}),
            html.Div(title, style={"fontSize": "13px", "color": COLORS["muted"], "marginTop": "4px"}),
        ])

    kpis = [
        kpi_card(f"Нийт {label}", str(total_items)),
        kpi_card("Нийт зарын тоо", f"{total_jobs:,}"),
        kpi_card("Дундаж цалин", f"{avg_salary:,}₮"),
        kpi_card("Хамгийн өндөр", f"{max_salary:,}₮"),
        kpi_card("Хамгийн бага", f"{min_salary:,}₮"),
    ]

    empty_fig = go.Figure()
    empty_fig.update_layout(template="plotly_white", annotations=[
        dict(text="Өгөгдөл байхгүй", xref="paper", yref="paper", showarrow=False, font_size=16)
    ])

    if df.empty:
        return kpis, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, html.P("Өгөгдөл байхгүй")

    # ── Salary comparison bar ───────────────────────────────────────────
    df_sorted = df.sort_values("average_salary", ascending=True)
    salary_bar = go.Figure()
    salary_bar.add_trace(go.Bar(
        y=df_sorted[name_col], x=df_sorted["min_salary"],
        name="Доод", orientation="h", marker_color=COLORS["secondary"],
    ))
    salary_bar.add_trace(go.Bar(
        y=df_sorted[name_col], x=df_sorted["average_salary"],
        name="Дундаж", orientation="h", marker_color=COLORS["primary"],
    ))
    salary_bar.add_trace(go.Bar(
        y=df_sorted[name_col], x=df_sorted["max_salary"],
        name="Дээд", orientation="h", marker_color="#C00000",
    ))
    salary_bar.update_layout(
        title="Цалингийн харьцуулалт",
        barmode="group",
        template="plotly_white",
        xaxis_title="₮",
        height=max(400, len(df) * 45),
        margin=dict(l=10, r=10, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # ── Job count bar ───────────────────────────────────────────────────
    df_jc = df.sort_values("job_count", ascending=True)
    job_bar = px.bar(
        df_jc, y=name_col, x="job_count", orientation="h",
        title="Ажлын зарын тоо",
        color_discrete_sequence=[COLORS["accent"]],
        template="plotly_white",
        height=max(400, len(df) * 45),
    )
    job_bar.update_layout(
        xaxis_title="Зарын тоо", yaxis_title="",
        margin=dict(l=10, r=10, t=40, b=30),
    )

    # ── Source pie ──────────────────────────────────────────────────────
    zangia_total = int(df["source_zangia"].sum()) if "source_zangia" in df.columns else 0
    lambda_total = int(df["source_lambda"].sum()) if "source_lambda" in df.columns else 0
    source_pie = px.pie(
        names=["Zangia", "Lambda Global"],
        values=[zangia_total, lambda_total],
        title="Эх сурвалжийн харьцаа",
        color_discrete_sequence=[COLORS["primary"], COLORS["accent"]],
        template="plotly_white",
        hole=0.4,
    )
    source_pie.update_layout(margin=dict(l=10, r=10, t=40, b=30))

    # ── Salary range (min-max) ──────────────────────────────────────────
    df_range = df.sort_values("average_salary", ascending=True)
    range_fig = go.Figure()
    for _, row in df_range.iterrows():
        range_fig.add_trace(go.Scatter(
            x=[row["min_salary"], row["max_salary"]],
            y=[row[name_col], row[name_col]],
            mode="lines+markers",
            marker=dict(size=10, color=[COLORS["secondary"], "#C00000"]),
            line=dict(color=COLORS["muted"], width=2),
            showlegend=False,
            hovertemplate=f"{row[name_col]}<br>Доод: {row['min_salary']:,.0f}₮<br>Дээд: {row['max_salary']:,.0f}₮<extra></extra>",
        ))
        range_fig.add_trace(go.Scatter(
            x=[row["average_salary"]],
            y=[row[name_col]],
            mode="markers",
            marker=dict(size=12, color=COLORS["primary"], symbol="diamond"),
            showlegend=False,
            hovertemplate=f"Дундаж: {row['average_salary']:,.0f}₮<extra></extra>",
        ))
    range_fig.update_layout(
        title="Цалингийн хүрээ (Доод ● Дундаж ◆ Дээд ●)",
        template="plotly_white",
        xaxis_title="₮",
        height=max(400, len(df) * 45),
        margin=dict(l=10, r=10, t=40, b=30),
    )

    # ── Trend: average salary over time ─────────────────────────────────
    if "period" in df_all.columns and df_all["period"].nunique() > 0:
        trend_df = (
            df_all.groupby(["period", name_col])["average_salary"]
            .mean()
            .reset_index()
            .sort_values("period")
        )
        trend_fig = px.line(
            trend_df, x="period", y="average_salary", color=name_col,
            title="Дундаж цалингийн чиг хандлага (Он-Сар)",
            markers=True,
            template="plotly_white",
        )
        trend_fig.update_layout(
            xaxis_title="Он-Сар", yaxis_title="Дундаж цалин (₮)",
            legend_title=label,
            height=450,
            margin=dict(l=10, r=10, t=40, b=30),
        )
    else:
        trend_fig = empty_fig

    # ── Trend: job count over time ──────────────────────────────────────
    if "period" in df_all.columns and df_all["period"].nunique() > 0:
        trend_jc = (
            df_all.groupby(["period", name_col])["job_count"]
            .sum()
            .reset_index()
            .sort_values("period")
        )
        trend_jc_fig = px.bar(
            trend_jc, x="period", y="job_count", color=name_col,
            title="Ажлын зарын тооны чиг хандлага (Он-Сар)",
            template="plotly_white",
            barmode="stack",
        )
        trend_jc_fig.update_layout(
            xaxis_title="Он-Сар", yaxis_title="Зарын тоо",
            legend_title=label,
            height=450,
            margin=dict(l=10, r=10, t=40, b=30),
        )
    else:
        trend_jc_fig = empty_fig

    # ── Data table ──────────────────────────────────────────────────────
    display_cols = [name_col, "min_salary", "max_salary", "average_salary",
                    "job_count", "source_zangia", "source_lambda"]
    header_map = {
        name_col: label,
        "min_salary": "Доод цалин",
        "max_salary": "Дээд цалин",
        "average_salary": "Дундаж цалин",
        "job_count": "Зарын тоо",
        "source_zangia": "Zangia",
        "source_lambda": "Lambda",
    }
    table_header = html.Tr([html.Th(header_map.get(c, c), style={
        "padding": "10px 14px", "backgroundColor": COLORS["primary"],
        "color": "white", "textAlign": "left", "fontWeight": "600",
    }) for c in display_cols])

    table_rows = []
    for i, (_, row) in enumerate(df.sort_values("average_salary", ascending=False).iterrows()):
        bg = "#F7F9FC" if i % 2 == 0 else "white"
        cells = []
        for c in display_cols:
            val = row[c]
            if c in ("min_salary", "max_salary", "average_salary") and pd.notna(val):
                val = f"{int(val):,}₮"
            elif c in ("job_count", "source_zangia", "source_lambda") and pd.notna(val):
                val = f"{int(val):,}"
            cells.append(html.Td(val, style={"padding": "8px 14px"}))
        table_rows.append(html.Tr(cells, style={"backgroundColor": bg}))

    table = html.Table(
        [html.Thead(table_header), html.Tbody(table_rows)],
        style={
            "width": "100%", "borderCollapse": "collapse",
            "fontSize": "14px", "borderRadius": "8px", "overflow": "hidden",
        },
    )
    table_block = html.Div([
        html.H3("Дэлгэрэнгүй хүснэгт", style={"color": COLORS["dark"], "marginBottom": "12px"}),
        table,
    ])

    return kpis, salary_bar, job_bar, source_pie, range_fig, trend_fig, trend_jc_fig, table_block


# ── Excel download callback ─────────────────────────────────────────────────

# Clientside callback: show loading state on button immediately when clicked
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return window.dash_clientside.no_update;
        var btn = document.getElementById('download-excel-btn');
        if (btn) {
            btn.classList.add('download-btn-loading');
            var txt = document.getElementById('download-btn-text');
            if (txt) txt.innerText = '⏳ Бэлдэж байна...';
        }
        return true;
    }
    """,
    Output("download-loading-state", "data"),
    Input("download-excel-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("download-excel", "data"),
    Output("download-btn-text", "children"),
    Output("download-excel-btn", "className"),
    Input("download-excel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def download_excel(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    try:
        # Write to a unique temp file to avoid "Permission denied" when
        # a previous download is still open in Excel.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        out_dir = os.path.join(base_dir, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx", prefix="salary_report_", dir=out_dir)
        os.close(tmp_fd)
        generated = generate_salary_report(tmp_path)
        return dcc.send_file(generated, filename="salary_report.xlsx"), "📥 Excel татах", ""
    except Exception as e:
        print(f"Excel download error: {e}")
        return dash.no_update, "❌ Алдаа гарлаа", ""


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port="8006")
