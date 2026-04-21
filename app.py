"""
CFG Mock Analytics — Portfolio Analytics Dashboard (Plotly Dash)

Multi-page dashboard backed by four pre-aggregated CSVs in /data.
All column references below come from the actual files; no columns
are assumed.
"""
from __future__ import annotations

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dash_table, dcc, html
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

COLOR_PRIMARY    = "#1F4E79"
COLOR_SECONDARY  = "#2E75B6"
COLOR_ACCENT     = "#4BACC6"
COLOR_BG         = "#F4F8FB"
COLOR_CARD       = "#FFFFFF"
COLOR_DANGER     = "#C00000"
COLOR_SUCCESS    = "#1E7D45"
COLOR_TEXT       = "#1F2937"
COLOR_MUTED      = "#6B7280"
COLOR_GRID       = "#E5EAF0"

CHART_FONT_FAMILY = (
    '"Inter", "Helvetica Neue", "Segoe UI", Arial, sans-serif'
)

PLOTLY_TEMPLATE = go.layout.Template()
PLOTLY_TEMPLATE.layout = go.Layout(
    font=dict(family=CHART_FONT_FAMILY, size=12, color=COLOR_TEXT),
    paper_bgcolor=COLOR_CARD,
    plot_bgcolor=COLOR_CARD,
    title=dict(
        font=dict(family=CHART_FONT_FAMILY, size=16, color=COLOR_PRIMARY),
        x=0.01, xanchor="left",
    ),
    colorway=[COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT,
              COLOR_SUCCESS, "#C98A2B", COLOR_DANGER],
    xaxis=dict(gridcolor=COLOR_GRID, zerolinecolor=COLOR_GRID,
               linecolor=COLOR_GRID, ticks="outside",
               title=dict(font=dict(size=12, color=COLOR_MUTED))),
    yaxis=dict(gridcolor=COLOR_GRID, zerolinecolor=COLOR_GRID,
               linecolor=COLOR_GRID, ticks="outside",
               title=dict(font=dict(size=12, color=COLOR_MUTED))),
    legend=dict(bgcolor="rgba(0,0,0,0)",
                font=dict(size=11, color=COLOR_TEXT)),
    margin=dict(l=60, r=30, t=60, b=60),
    hoverlabel=dict(bgcolor="white",
                    font=dict(family=CHART_FONT_FAMILY,
                              size=12, color=COLOR_TEXT),
                    bordercolor=COLOR_GRID),
)

STATUS_COLORS = {
    "On Track":  COLOR_PRIMARY,
    "Paid Off":  COLOR_SUCCESS,
    "Late":      "#C98A2B",
    "Defaulted": COLOR_DANGER,
    "Unknown":   COLOR_MUTED,
}

# Light-blue -> red gradient used on industry + cohort risk visuals.
RISK_COLORSCALE = [
    [0.00, "#DDE9F5"],
    [0.25, COLOR_ACCENT],
    [0.50, "#F4C27E"],
    [0.75, "#E4856B"],
    [1.00, COLOR_DANGER],
]

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def fmt_currency(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return f"${value:,.0f}"


def fmt_currency_m(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def fmt_pct(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return f"{value:.1f}%"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Expected CSV not found: {path}. "
            "Ensure the four reporting CSVs are placed under /data."
        )
    return pd.read_csv(path)


portfolio_df = load_csv("rpt_portfolio_summary.csv")
industry_df  = load_csv("rpt_industry_performance.csv")
cashflow_df  = load_csv("rpt_monthly_cashflow.csv").copy()
cohort_df    = load_csv("rpt_cohort_performance.csv").copy()

cashflow_df["month_dt"] = pd.to_datetime(cashflow_df["month"] + "-01")
cashflow_df = cashflow_df.sort_values("month_dt").reset_index(drop=True)

cohort_df["cohort_dt"] = pd.to_datetime(
    cohort_df["disbursement_cohort"] + "-01"
)
cohort_df = cohort_df.sort_values("cohort_dt").reset_index(drop=True)

# ---------------------------------------------------------------------------
# View 1 — Portfolio Overview
# ---------------------------------------------------------------------------


def build_overview_kpis() -> list[dict]:
    total_funded = portfolio_df["funding_amount"].sum()
    total_collected = portfolio_df["total_paid"].sum()
    total_outstanding = portfolio_df["outstanding_balance"].sum()
    total_repayable = portfolio_df["total_repayable"].sum()
    overall_collection_rate = (
        total_collected / total_repayable * 100 if total_repayable else 0
    )

    return [
        {"label": "Total Funded",
         "value": fmt_currency_m(total_funded),
         "sub":   f"{len(portfolio_df):,} accounts"},
        {"label": "Total Collected",
         "value": fmt_currency_m(total_collected),
         "sub":   "Payments received to date"},
        {"label": "Outstanding Balance",
         "value": fmt_currency_m(total_outstanding),
         "sub":   "Remaining contracted repayable"},
        {"label": "Overall Collection Rate",
         "value": fmt_pct(overall_collection_rate),
         "sub":   "Collected / total repayable"},
    ]


def kpi_card(kpi: dict) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div(kpi["label"], className="kpi-label"),
            html.Div(kpi["value"], className="kpi-value"),
            html.Div(kpi["sub"],   className="kpi-sub"),
        ]),
        className="kpi-card",
    )


def chart_status_donut() -> go.Figure:
    counts = (
        portfolio_df["repayment_status"]
        .value_counts()
        .reindex(list(STATUS_COLORS.keys()))
        .dropna()
    )
    fig = go.Figure(
        go.Pie(
            labels=counts.index.tolist(),
            values=counts.values.tolist(),
            hole=0.55,
            marker=dict(colors=[STATUS_COLORS[s] for s in counts.index]),
            textinfo="label+percent",
            textfont=dict(size=12, color=COLOR_TEXT),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Accounts: %{value:,}<br>"
                "Share: %{percent}<extra></extra>"
            ),
            sort=False,
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Accounts by Repayment Status",
        showlegend=True,
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        annotations=[dict(
            text=f"{len(portfolio_df):,}<br><span style='font-size:12px;"
                 f"color:{COLOR_MUTED}'>accounts</span>",
            showarrow=False, font=dict(size=18, color=COLOR_PRIMARY),
            x=0.5, y=0.5,
        )],
    )
    return fig


def chart_funded_by_industry() -> go.Figure:
    agg = (
        portfolio_df.groupby("industry", as_index=False)["funding_amount"]
        .sum()
        .sort_values("funding_amount", ascending=True)
        .tail(10)
    )
    fig = go.Figure(go.Bar(
        x=agg["funding_amount"],
        y=agg["industry"],
        orientation="h",
        marker=dict(color=COLOR_PRIMARY),
        text=[fmt_currency_m(v) for v in agg["funding_amount"]],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>Total Funded: %{x:$,.0f}<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Total Funded by Industry (Top 10)",
        xaxis=dict(title="Total Funded (USD)", tickprefix="$",
                   tickformat=",.0f"),
        yaxis=dict(title=""),
        margin=dict(l=140, r=40, t=60, b=60),
    )
    return fig


def view_overview() -> html.Div:
    kpis = build_overview_kpis()
    return html.Div([
        html.H2("Portfolio Overview", className="view-title"),
        html.P(
            "Portfolio-wide funding, collections, and account status "
            "across all ClearFund-backed loans.",
            className="view-subtitle",
        ),
        dbc.Row(
            [dbc.Col(kpi_card(k), md=3, sm=6, xs=12) for k in kpis],
            className="g-3 mb-4",
        ),
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody(dcc.Graph(
                    figure=chart_status_donut(),
                    config={"displayModeBar": False},
                )), className="chart-card"),
                md=6, xs=12,
            ),
            dbc.Col(
                dbc.Card(dbc.CardBody(dcc.Graph(
                    figure=chart_funded_by_industry(),
                    config={"displayModeBar": False},
                )), className="chart-card"),
                md=6, xs=12,
            ),
        ], className="g-3"),
    ])

# ---------------------------------------------------------------------------
# View 2 — Industry Performance
# ---------------------------------------------------------------------------


def chart_industry_funded() -> go.Figure:
    df = industry_df.sort_values("total_funded", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["total_funded"],
        y=df["industry"],
        orientation="h",
        marker=dict(
            color=df["default_rate"],
            colorscale=RISK_COLORSCALE,
            cmin=df["default_rate"].min(),
            cmax=df["default_rate"].max(),
            colorbar=dict(
                title=dict(text="Default<br>Rate (%)",
                           font=dict(size=11, color=COLOR_MUTED)),
                thickness=14, len=0.8,
                tickfont=dict(size=10, color=COLOR_MUTED),
            ),
        ),
        customdata=np.stack([df["default_rate"], df["total_accounts"]], axis=-1),
        text=[fmt_currency_m(v) for v in df["total_funded"]],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Total Funded: %{x:$,.0f}<br>"
            "Default Rate: %{customdata[0]:.2f}%<br>"
            "Accounts: %{customdata[1]:,}"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Total Funded by Industry (colored by Default Rate)",
        xaxis=dict(title="Total Funded (USD)", tickprefix="$",
                   tickformat=",.0f"),
        yaxis=dict(title=""),
        margin=dict(l=140, r=40, t=60, b=60),
    )
    return fig


def chart_industry_default_vs_late() -> go.Figure:
    df = industry_df.sort_values("default_rate", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Default Rate",
        x=df["industry"], y=df["default_rate"],
        marker_color=COLOR_DANGER,
        hovertemplate="<b>%{x}</b><br>Default Rate: %{y:.2f}%<extra></extra>",
        text=[fmt_pct(v) for v in df["default_rate"]],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Late Rate",
        x=df["industry"], y=df["late_rate"],
        marker_color="#C98A2B",
        hovertemplate="<b>%{x}</b><br>Late Rate: %{y:.2f}%<extra></extra>",
        text=[fmt_pct(v) for v in df["late_rate"]],
        textposition="outside",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Default Rate vs. Late Rate by Industry",
        barmode="group",
        xaxis=dict(title=""),
        yaxis=dict(title="Rate (% of accounts)", ticksuffix="%"),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
    )
    return fig


def chart_industry_scatter() -> go.Figure:
    df = industry_df.copy()
    fig = go.Figure(go.Scatter(
        x=df["default_rate"],
        y=df["avg_pct_repaid"],
        mode="markers+text",
        text=df["industry"],
        textposition="top center",
        textfont=dict(size=11, color=COLOR_TEXT),
        marker=dict(
            size=df["total_funded"] / df["total_funded"].max() * 60 + 14,
            color=df["default_rate"],
            colorscale=RISK_COLORSCALE,
            line=dict(color="white", width=1.5),
            sizemode="diameter",
        ),
        customdata=np.stack(
            [df["total_funded"], df["total_accounts"], df["late_rate"]],
            axis=-1,
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Default Rate: %{x:.2f}%<br>"
            "Avg % Repaid: %{y:.2f}%<br>"
            "Late Rate: %{customdata[2]:.2f}%<br>"
            "Total Funded: %{customdata[0]:$,.0f}<br>"
            "Accounts: %{customdata[1]:,}"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Industry Positioning — Default Rate vs. Avg % Repaid",
        xaxis=dict(title="Default Rate (%)", ticksuffix="%"),
        yaxis=dict(title="Avg % Repaid", ticksuffix="%"),
        showlegend=False,
    )
    return fig


def view_industry() -> html.Div:
    return html.Div([
        html.H2("Industry Performance", className="view-title"),
        html.P(
            "Where in the portfolio risk concentrates, and how each "
            "industry trades volume against default performance.",
            className="view-subtitle",
        ),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody(dcc.Graph(
                figure=chart_industry_funded(),
                config={"displayModeBar": False},
            )), className="chart-card"),
            xs=12,
        ), className="mb-3"),
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody(dcc.Graph(
                    figure=chart_industry_default_vs_late(),
                    config={"displayModeBar": False},
                )), className="chart-card"),
                md=6, xs=12,
            ),
            dbc.Col(
                dbc.Card(dbc.CardBody(dcc.Graph(
                    figure=chart_industry_scatter(),
                    config={"displayModeBar": False},
                )), className="chart-card"),
                md=6, xs=12,
            ),
        ], className="g-3"),
    ])

# ---------------------------------------------------------------------------
# View 3 — Monthly Cash Flow Trend
# ---------------------------------------------------------------------------


def chart_cashflow_dual_axis(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            name="Total Collected",
            x=df["month_dt"], y=df["total_collected"],
            marker_color=COLOR_PRIMARY,
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Collected: %{y:$,.0f}<extra></extra>"
            ),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="Collection Rate",
            x=df["month_dt"], y=df["collection_rate"],
            mode="lines+markers",
            line=dict(color=COLOR_ACCENT, width=3),
            marker=dict(size=7, color=COLOR_ACCENT,
                        line=dict(color="white", width=1.5)),
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Collection Rate: %{y:.2f}%<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    if not df.empty:
        avg_rate = df["collection_rate"].mean()
        fig.add_hline(
            y=avg_rate, line=dict(color=COLOR_MUTED, dash="dash"),
            annotation_text=f"Avg {avg_rate:.1f}%",
            annotation_position="top left",
            annotation_font=dict(color=COLOR_MUTED, size=11),
            secondary_y=True,
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Monthly Collections vs. Collection Rate",
        barmode="overlay",
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
        hovermode="x unified",
    )
    fig.update_xaxes(title="Month", tickformat="%b %Y")
    fig.update_yaxes(title="Total Collected (USD)", tickprefix="$",
                     tickformat=",.0f", secondary_y=False)
    fig.update_yaxes(title="Collection Rate (%)", ticksuffix="%",
                     secondary_y=True, rangemode="tozero")
    return fig


def chart_cashflow_cumulative(df: pd.DataFrame) -> go.Figure:
    d = df.copy().sort_values("month_dt")
    d["cumulative_collected"] = d["total_collected"].cumsum()
    fig = go.Figure(go.Scatter(
        x=d["month_dt"],
        y=d["cumulative_collected"],
        mode="lines",
        line=dict(color=COLOR_SECONDARY, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(46,117,182,0.18)",
        hovertemplate=(
            "<b>%{x|%b %Y}</b><br>"
            "Cumulative Collected: %{y:$,.0f}<extra></extra>"
        ),
        name="Cumulative Collected",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cumulative Collections Over Time",
        xaxis=dict(title="Month", tickformat="%b %Y"),
        yaxis=dict(title="Cumulative Collected (USD)",
                   tickprefix="$", tickformat=",.0f"),
        showlegend=False,
    )
    return fig


def view_cashflow() -> html.Div:
    months = cashflow_df["month"].tolist()

    return html.Div([
        html.H2("Monthly Cash Flow Trend", className="view-title"),
        html.P(
            "Scheduled vs. actual collections by month, with collection "
            "rate trend and cumulative inflow.",
            className="view-subtitle",
        ),
        dbc.Card(dbc.CardBody([
            html.Label("Date range",
                       className="filter-label"),
            dcc.Dropdown(
                id="cashflow-start-month",
                options=[{"label": m, "value": m} for m in months],
                value=months[0],
                clearable=False,
                className="mb-2",
            ),
            html.Label("To",
                       className="filter-label"),
            dcc.Dropdown(
                id="cashflow-end-month",
                options=[{"label": m, "value": m} for m in months],
                value=months[-1],
                clearable=False,
            ),
        ]), className="filter-card mb-3"),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody(dcc.Graph(
                id="cashflow-dual-axis",
                config={"displayModeBar": False},
            )), className="chart-card"),
            xs=12,
        ), className="mb-3"),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody(dcc.Graph(
                id="cashflow-cumulative",
                config={"displayModeBar": False},
            )), className="chart-card"),
            xs=12,
        )),
    ])

# ---------------------------------------------------------------------------
# View 4 — Cohort Performance
# ---------------------------------------------------------------------------


def chart_cohort_heatmap() -> go.Figure:
    df = cohort_df.sort_values("cohort_dt")
    metric_cols = ["avg_pct_repaid", "default_rate", "late_rate"]
    metric_labels = ["Avg % Repaid", "Default Rate", "Late Rate"]

    # Build a "goodness" z-matrix (0=bad,1=good) so one green->red palette
    # reads correctly across metrics with opposite polarity.
    def norm_good(series: pd.Series, inverse: bool) -> pd.Series:
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([0.5] * len(series), index=series.index)
        scaled = (series - mn) / (mx - mn)
        return 1.0 - scaled if inverse else scaled

    z = np.column_stack([
        norm_good(df["avg_pct_repaid"], inverse=False),
        norm_good(df["default_rate"],   inverse=True),
        norm_good(df["late_rate"],      inverse=True),
    ])

    text_matrix = np.column_stack([
        df["avg_pct_repaid"].map(lambda v: f"{v:.1f}%"),
        df["default_rate"].map(lambda v: f"{v:.1f}%"),
        df["late_rate"].map(lambda v: f"{v:.1f}%"),
    ])

    fig = go.Figure(go.Heatmap(
        z=z,
        x=metric_labels,
        y=df["disbursement_cohort"],
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(color=COLOR_TEXT, size=11),
        colorscale=[
            [0.0, COLOR_DANGER],
            [0.5, "#F4C27E"],
            [1.0, COLOR_SUCCESS],
        ],
        zmin=0, zmax=1,
        hovertemplate=(
            "<b>Cohort %{y}</b><br>"
            "%{x}: %{text}<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="Relative<br>Performance",
                       font=dict(size=11, color=COLOR_MUTED)),
            tickvals=[0, 0.5, 1],
            ticktext=["Worse", "Mid", "Better"],
            thickness=14, len=0.7,
        ),
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cohort Performance Heatmap",
        xaxis=dict(title="", side="top"),
        yaxis=dict(title="Disbursement Cohort", autorange="reversed"),
        height=max(420, 22 * len(df)),
        margin=dict(l=100, r=40, t=70, b=40),
    )
    return fig


def chart_cohort_grouped_bar() -> go.Figure:
    df = cohort_df.sort_values("cohort_dt")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg % Repaid", x=df["disbursement_cohort"],
        y=df["avg_pct_repaid"], marker_color=COLOR_SUCCESS,
        hovertemplate=(
            "<b>%{x}</b><br>Avg % Repaid: %{y:.2f}%<extra></extra>"
        ),
    ))
    fig.add_trace(go.Bar(
        name="Default Rate", x=df["disbursement_cohort"],
        y=df["default_rate"], marker_color=COLOR_DANGER,
        hovertemplate=(
            "<b>%{x}</b><br>Default Rate: %{y:.2f}%<extra></extra>"
        ),
    ))
    fig.add_trace(go.Bar(
        name="Late Rate", x=df["disbursement_cohort"],
        y=df["late_rate"], marker_color="#C98A2B",
        hovertemplate=(
            "<b>%{x}</b><br>Late Rate: %{y:.2f}%<extra></extra>"
        ),
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cohort Metrics Comparison",
        barmode="group",
        xaxis=dict(title="Disbursement Cohort"),
        yaxis=dict(title="Rate (%)", ticksuffix="%"),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
    )
    return fig


def cohort_table() -> dash_table.DataTable:
    df = cohort_df.drop(columns=["cohort_dt"]).copy()

    column_defs = [
        {"name": "Cohort",             "id": "disbursement_cohort",
         "type": "text"},
        {"name": "Accounts",           "id": "total_accounts",
         "type": "numeric",
         "format": dash_table.Format.Format(group=",")},
        {"name": "Total Funded",       "id": "total_funded",
         "type": "numeric",
         "format": dash_table.Format.Format(symbol=dash_table.Format.Symbol.yes,
                                             symbol_prefix="$",
                                             precision=0,
                                             group=",")},
        {"name": "Avg Funding",        "id": "avg_funding_amount",
         "type": "numeric",
         "format": dash_table.Format.Format(symbol=dash_table.Format.Symbol.yes,
                                             symbol_prefix="$",
                                             precision=0,
                                             group=",")},
        {"name": "Avg % Repaid",       "id": "avg_pct_repaid",
         "type": "numeric",
         "format": dash_table.Format.Format(precision=2,
                                             scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Default Rate (%)",   "id": "default_rate",
         "type": "numeric",
         "format": dash_table.Format.Format(precision=2,
                                             scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Late Rate (%)",      "id": "late_rate",
         "type": "numeric",
         "format": dash_table.Format.Format(precision=2,
                                             scheme=dash_table.Format.Scheme.fixed)},
    ]

    return dash_table.DataTable(
        id="cohort-table",
        columns=column_defs,
        data=df.to_dict("records"),
        sort_action="native",
        page_size=24,
        fixed_rows={"headers": True},
        style_table={
            "maxHeight": "520px",
            "overflowY": "auto",
            "border": f"1px solid {COLOR_GRID}",
            "borderRadius": "6px",
        },
        style_header={
            "backgroundColor": COLOR_PRIMARY,
            "color": "white",
            "fontWeight": "600",
            "fontFamily": CHART_FONT_FAMILY,
            "border": "none",
            "textAlign": "left",
            "position": "sticky", "top": 0, "zIndex": 1,
        },
        style_cell={
            "fontFamily": CHART_FONT_FAMILY,
            "fontSize": "13px",
            "padding": "10px 14px",
            "border": "none",
            "borderBottom": f"1px solid {COLOR_GRID}",
            "color": COLOR_TEXT,
            "backgroundColor": "white",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"},
             "backgroundColor": "#F9FBFD"},
            {"if": {"filter_query": "{default_rate} >= 10",
                    "column_id": "default_rate"},
             "backgroundColor": "#FDE2E2",
             "color": COLOR_DANGER,
             "fontWeight": "600"},
            {"if": {"filter_query": "{default_rate} >= 5 && {default_rate} < 10",
                    "column_id": "default_rate"},
             "backgroundColor": "#FFF1D9",
             "color": "#8C5A00",
             "fontWeight": "600"},
            {"if": {"filter_query": "{late_rate} >= 20",
                    "column_id": "late_rate"},
             "backgroundColor": "#FDE2E2",
             "color": COLOR_DANGER,
             "fontWeight": "600"},
        ],
        style_cell_conditional=[
            {"if": {"column_id": "disbursement_cohort"},
             "fontWeight": "600", "color": COLOR_PRIMARY},
        ],
    )


def view_cohort() -> html.Div:
    return html.Div([
        html.H2("Cohort Performance", className="view-title"),
        html.P(
            "Vintage analysis: how each disbursement cohort is aging "
            "against repayment, default, and late benchmarks.",
            className="view-subtitle",
        ),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody(dcc.Graph(
                figure=chart_cohort_heatmap(),
                config={"displayModeBar": False},
            )), className="chart-card"),
            xs=12,
        ), className="mb-3"),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody(dcc.Graph(
                figure=chart_cohort_grouped_bar(),
                config={"displayModeBar": False},
            )), className="chart-card"),
            xs=12,
        ), className="mb-3"),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H5("Cohort Detail", className="table-title"),
                cohort_table(),
            ]), className="chart-card"),
            xs=12,
        )),
    ])

# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
    title="CFG Mock Analytics — Portfolio Dashboard",
    suppress_callback_exceptions=True,
)
server = app.server  # gunicorn entrypoint


def navbar() -> dbc.Navbar:
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("CFG Mock Analytics",
                            className="brand-text", href="#"),
            dcc.Tabs(
                id="top-tabs",
                value="tab-overview",
                children=[
                    dcc.Tab(label="Portfolio Overview",
                            value="tab-overview",
                            className="custom-tab",
                            selected_className="custom-tab--selected"),
                    dcc.Tab(label="Industry Performance",
                            value="tab-industry",
                            className="custom-tab",
                            selected_className="custom-tab--selected"),
                    dcc.Tab(label="Monthly Cash Flow",
                            value="tab-cashflow",
                            className="custom-tab",
                            selected_className="custom-tab--selected"),
                    dcc.Tab(label="Cohort Performance",
                            value="tab-cohort",
                            className="custom-tab",
                            selected_className="custom-tab--selected"),
                ],
                parent_className="top-tabs-parent",
                className="top-tabs",
            ),
        ], fluid=True),
        color=COLOR_PRIMARY, dark=True, sticky="top",
        className="app-navbar",
    )


def footer() -> html.Footer:
    return html.Footer(
        "CFG Mock Analytics — Portfolio Dashboard Demo  |  "
        "Built by Pooja Pranavi Nalamothu",
        className="app-footer",
    )


app.layout = html.Div([
    navbar(),
    dbc.Container(html.Div(id="view-content"),
                  fluid=True, className="app-body"),
    footer(),
], className="app-root")

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@app.callback(Output("view-content", "children"),
              Input("top-tabs", "value"))
def render_view(tab: str):
    if tab == "tab-industry":
        return view_industry()
    if tab == "tab-cashflow":
        return view_cashflow()
    if tab == "tab-cohort":
        return view_cohort()
    return view_overview()


@app.callback(
    Output("cashflow-dual-axis", "figure"),
    Output("cashflow-cumulative", "figure"),
    Input("cashflow-start-month", "value"),
    Input("cashflow-end-month", "value"),
)
def update_cashflow(start_month: str, end_month: str):
    if start_month and end_month and start_month > end_month:
        start_month, end_month = end_month, start_month

    df = cashflow_df.copy()
    if start_month:
        df = df[df["month"] >= start_month]
    if end_month:
        df = df[df["month"] <= end_month]

    if df.empty:
        df = cashflow_df.copy()

    return (
        chart_cashflow_dual_axis(df),
        chart_cashflow_cumulative(df),
    )

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
