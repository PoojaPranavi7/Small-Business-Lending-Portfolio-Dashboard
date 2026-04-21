"""
ClearFund Capital — Portfolio Analytics Dashboard (Streamlit)

A 4-view interactive dashboard backed by four pre-aggregated CSVs in
/tableau_exports. All data manipulation is via pandas; all charts are
plotly. No backend, no database, no external APIs.

Run:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ClearFund Capital | Portfolio Analytics",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    "On Track":  "#2ECC71",
    "Paid Off":  "#2E75B6",
    "Late":      "#F39C12",
    "Defaulted": "#E74C3C",
}
STATUS_ORDER = ["On Track", "Paid Off", "Late", "Defaulted"]

PRIMARY    = "#1F4E79"
SECONDARY  = "#2E75B6"
SUCCESS    = "#2ECC71"
WARNING    = "#F39C12"
DANGER     = "#E74C3C"
MUTED      = "#6B7280"

CHART_FONT = "Arial"
CHART_TEMPLATE = "plotly_white"

DATA_DIR = Path(__file__).resolve().parent / "tableau_exports"

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def fmt_money_compact(value: float) -> str:
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:,.0f}"


def fmt_money_full(value: float) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"${value:,.0f}"


def fmt_pct(value: float) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%"

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------


@st.cache_data
def load_portfolio() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "rpt_portfolio_summary.csv")


@st.cache_data
def load_industry() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "rpt_industry_performance.csv")


@st.cache_data
def load_cohort() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "rpt_cohort_performance.csv")
    return df.sort_values("disbursement_cohort").reset_index(drop=True)


@st.cache_data
def load_cashflow() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "rpt_monthly_cashflow.csv")
    return df.sort_values("month").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------


def style_figure(fig: go.Figure, *, title: str | None = None,
                 height: int | None = None) -> go.Figure:
    fig.update_layout(
        template=CHART_TEMPLATE,
        font_family=CHART_FONT,
        title_font_size=16,
        title_font_color=PRIMARY,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=30, t=60, b=60),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    if title is not None:
        fig.update_layout(title=title)
    if height is not None:
        fig.update_layout(height=height)
    return fig

# ---------------------------------------------------------------------------
# Sidebar + page chrome
# ---------------------------------------------------------------------------


def render_sidebar() -> str:
    st.sidebar.markdown(
        f"""
        <div style="padding: 4px 0 18px 0;">
            <div style="font-size: 1.35rem; font-weight: 700;
                        color: {PRIMARY}; line-height: 1.15;">
                💼 ClearFund Capital
            </div>
            <div style="font-size: 0.78rem; color: {MUTED};
                        letter-spacing: 0.4px; margin-top: 2px;">
                PORTFOLIO ANALYTICS
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    view = st.sidebar.radio(
        "Navigate",
        options=[
            "Portfolio Overview",
            "Industry Performance",
            "Cohort Performance",
            "Monthly Cashflow",
        ],
        label_visibility="collapsed",
    )

    # Push the credit toward the bottom of the sidebar.
    st.sidebar.markdown(
        "<div style='height: 60vh;'></div>", unsafe_allow_html=True
    )
    st.sidebar.markdown(
        f"<div style='color:{MUTED}; font-size:0.78rem; "
        f"text-align:center; padding-top:12px;'>"
        f"Built by Pooja Pranavi Nalamothu</div>",
        unsafe_allow_html=True,
    )

    return view


def render_view_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div style="margin-bottom: 4px;">
            <div style="font-size:1.6rem; font-weight:700; color:{PRIMARY};">
                {title}
            </div>
            <div style="color:{MUTED}; font-size:0.95rem; margin-top:2px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def render_footer() -> None:
    st.markdown(
        f"""
        <div style="text-align:center; color:{MUTED}; font-size:0.82rem;
                    padding:18px 12px 4px; margin-top:24px;
                    border-top:1px solid #E5EAF0;">
            ClearFund Capital Portfolio Analytics |
            Demo Project by Pooja Pranavi Nalamothu |
            Built to demonstrate financial data analytics and
            reporting automation
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# View 1 — Portfolio Overview
# ---------------------------------------------------------------------------


def view_portfolio_overview() -> None:
    render_view_header(
        "Portfolio Overview",
        "Headline funding, collections, and account status across the "
        "ClearFund book.",
    )

    portfolio = load_portfolio()
    statuses_present = [
        s for s in STATUS_ORDER if s in portfolio["repayment_status"].unique()
    ]

    filter_col, _spacer = st.columns([2, 3])
    with filter_col:
        selected = st.multiselect(
            "Filter by repayment status",
            options=statuses_present,
            default=statuses_present,
            help="KPIs and charts below recalculate based on this selection.",
        )

    if not selected:
        st.warning("Select at least one repayment status to see results.")
        render_footer()
        return

    df = portfolio[portfolio["repayment_status"].isin(selected)].copy()

    total_funded      = df["funding_amount"].sum()
    total_outstanding = df["outstanding_balance"].sum()
    total_collected   = df["total_paid"].sum()
    total_repayable   = df["total_repayable"].sum()
    collection_rate   = (
        total_collected / total_repayable * 100 if total_repayable else 0.0
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Funded",      fmt_money_compact(total_funded),
              help=f"{len(df):,} accounts in selection")
    k2.metric("Total Outstanding", fmt_money_compact(total_outstanding),
              help="Remaining contracted repayable")
    k3.metric("Total Collected",   fmt_money_compact(total_collected),
              help="Payments received to date")
    k4.metric("Collection Rate",   fmt_pct(collection_rate),
              help="Total Collected / Total Repayable")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    chart_col_l, chart_col_r = st.columns([1, 1])

    with chart_col_l:
        status_counts = (
            df.groupby("repayment_status")
              .size()
              .reset_index(name="accounts")
              .sort_values("accounts", ascending=True)
        )
        fig1 = px.bar(
            status_counts,
            x="accounts",
            y="repayment_status",
            orientation="h",
            color="repayment_status",
            color_discrete_map=STATUS_COLORS,
            text="accounts",
            category_orders={
                "repayment_status": status_counts["repayment_status"].tolist()
            },
        )
        fig1.update_traces(
            texttemplate="%{x:,}",
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Accounts: %{x:,}<extra></extra>",
        )
        fig1.update_xaxes(title="Account Count", tickformat=",")
        fig1.update_yaxes(title="")
        style_figure(
            fig1,
            title="Account Distribution by Repayment Status",
            height=400,
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col_r:
        industry_funded = (
            df.groupby("industry", as_index=False)["funding_amount"]
              .sum()
              .sort_values("funding_amount", ascending=False)
        )
        fig2 = px.bar(
            industry_funded,
            x="industry",
            y="funding_amount",
            color="funding_amount",
            color_continuous_scale="Blues",
            text="funding_amount",
        )
        fig2.update_traces(
            texttemplate="%{text:$,.2s}",
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>Total Funded: %{y:$,.0f}<extra></extra>"
            ),
        )
        fig2.update_xaxes(
            title="",
            categoryorder="array",
            categoryarray=industry_funded["industry"].tolist(),
        )
        fig2.update_yaxes(title="Total Funded (USD)", tickprefix="$",
                          tickformat=",.0f")
        style_figure(
            fig2,
            title="Total Funded Amount by Industry",
            height=400,
        )
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    render_footer()

# ---------------------------------------------------------------------------
# View 2 — Industry Performance
# ---------------------------------------------------------------------------


def view_industry_performance() -> None:
    render_view_header(
        "Industry Performance",
        "Where risk concentrates in the portfolio: default rates and "
        "status mix by industry.",
    )

    industry = load_industry().copy()
    industry_by_default = industry.sort_values("default_rate", ascending=True)

    chart_col_l, chart_col_r = st.columns([1, 1])

    with chart_col_l:
        fig1 = px.bar(
            industry_by_default,
            x="default_rate",
            y="industry",
            orientation="h",
            color="default_rate",
            color_continuous_scale="Reds",
            text="default_rate",
        )
        fig1.update_traces(
            texttemplate="%{x:.2f}%",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>Default Rate: %{x:.2f}%<extra></extra>"
            ),
        )
        fig1.update_xaxes(title="Default Rate (%)", ticksuffix="%")
        fig1.update_yaxes(title="")
        style_figure(
            fig1,
            title="Default Rate by Industry (%)",
            height=420,
        )
        fig1.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col_r:
        ind_for_stack = industry.sort_values("default_rate", ascending=True)
        fig2 = go.Figure()
        for status, col in [
            ("On Track",  "on_track_count"),
            ("Paid Off",  "paid_off_count"),
            ("Late",      "late_count"),
            ("Defaulted", "default_count"),
        ]:
            fig2.add_trace(go.Bar(
                y=ind_for_stack["industry"],
                x=ind_for_stack[col],
                name=status,
                orientation="h",
                marker_color=STATUS_COLORS[status],
                hovertemplate=(
                    f"<b>%{{y}}</b><br>{status}: "
                    "%{x:,} accounts<extra></extra>"
                ),
            ))
        fig2.update_layout(barmode="stack")
        fig2.update_xaxes(title="Account Count", tickformat=",")
        fig2.update_yaxes(title="")
        style_figure(
            fig2,
            title="Portfolio Status Breakdown by Industry",
            height=420,
        )
        fig2.update_layout(legend=dict(orientation="h", y=-0.18, x=0.5,
                                        xanchor="center"))
        st.plotly_chart(fig2, use_container_width=True)

    summary = pd.DataFrame({
        "Industry":          industry["industry"],
        "Total Accounts":    industry["total_accounts"],
        "Total Funded ($)":  industry["total_funded"],
        "Avg % Repaid":      industry["avg_pct_repaid"],
        "Default Rate (%)":  industry["default_rate"],
        "Late Rate (%)":     industry["late_rate"],
    }).sort_values("Default Rate (%)", ascending=False).reset_index(drop=True)

    st.dataframe(
        summary,
        use_container_width=True,
        height=250,
        hide_index=True,
        column_config={
            "Industry":         st.column_config.TextColumn(width="medium"),
            "Total Accounts":   st.column_config.NumberColumn(format="%d"),
            "Total Funded ($)": st.column_config.NumberColumn(format="$%,.0f"),
            "Avg % Repaid":     st.column_config.NumberColumn(format="%.2f%%"),
            "Default Rate (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Late Rate (%)":    st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    render_footer()

# ---------------------------------------------------------------------------
# View 3 — Cohort Performance
# ---------------------------------------------------------------------------


def view_cohort_performance() -> None:
    render_view_header(
        "Cohort Performance",
        "Vintage analysis — how each disbursement-month cohort is "
        "aging against repayment and default benchmarks.",
    )

    cohort = load_cohort()  # already sorted ascending by cohort

    chart_col_l, chart_col_r = st.columns([1, 1])

    with chart_col_l:
        fig1 = px.line(
            cohort,
            x="disbursement_cohort",
            y="avg_pct_repaid",
            markers=True,
        )
        fig1.update_traces(
            line=dict(color=SECONDARY, width=3),
            marker=dict(size=8, color=SECONDARY,
                        line=dict(color="white", width=1.5)),
            hovertemplate=(
                "<b>%{x}</b><br>Avg % Repaid: %{y:.2f}%<extra></extra>"
            ),
        )
        avg_line = cohort["avg_pct_repaid"].mean()
        fig1.add_hline(
            y=avg_line,
            line_dash="dash",
            line_color=MUTED,
            annotation_text=f"Overall avg {avg_line:.1f}%",
            annotation_position="top left",
            annotation_font=dict(color=MUTED, size=11),
        )
        fig1.update_xaxes(title="Cohort (YYYY-MM)")
        fig1.update_yaxes(title="Avg % Repaid", ticksuffix="%",
                          rangemode="tozero")
        style_figure(
            fig1,
            title="Average % Repaid by Disbursement Cohort",
            height=420,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col_r:
        fig2 = px.bar(
            cohort,
            x="disbursement_cohort",
            y="total_funded",
        )
        fig2.update_traces(
            marker_color=PRIMARY,
            hovertemplate=(
                "<b>%{x}</b><br>Total Funded: %{y:$,.0f}<extra></extra>"
            ),
        )
        fig2.update_xaxes(title="Cohort (YYYY-MM)")
        fig2.update_yaxes(title="Total Funded (USD)", tickprefix="$",
                          tickformat=",.0f")
        style_figure(
            fig2,
            title="Total Funded by Cohort",
            height=420,
        )
        st.plotly_chart(fig2, use_container_width=True)

    table = pd.DataFrame({
        "Cohort":           cohort["disbursement_cohort"],
        "Total Accounts":   cohort["total_accounts"],
        "Avg % Repaid":     cohort["avg_pct_repaid"].round(2),
        "Default Rate (%)": cohort["default_rate"].round(2),
        "Total Funded ($)": cohort["total_funded"],
    })

    def color_default_rate(val: float) -> str:
        if pd.isna(val):
            return ""
        if val < 5:
            return "background-color: #D4EDDA; color: #125A2E; font-weight: 600;"
        if val < 15:
            return "background-color: #FFF3CD; color: #8C5A00; font-weight: 600;"
        return "background-color: #F8D7DA; color: #C00000; font-weight: 700;"

    styled = (
        table.style
             .applymap(color_default_rate, subset=["Default Rate (%)"])
             .format({
                 "Total Accounts":   "{:,}",
                 "Avg % Repaid":     "{:.1f}%",
                 "Default Rate (%)": "{:.1f}%",
                 "Total Funded ($)": "${:,.0f}",
             })
    )
    st.dataframe(styled, use_container_width=True, height=320, hide_index=True)

    render_footer()

# ---------------------------------------------------------------------------
# View 4 — Monthly Cashflow
# ---------------------------------------------------------------------------


def view_monthly_cashflow() -> None:
    render_view_header(
        "Monthly Cashflow",
        "Scheduled vs. actual collections by month, with a flagging "
        "view of monthly shortfall.",
    )

    cashflow = load_cashflow()

    avg_rate = cashflow["collection_rate"].mean()
    k1, _, _, _ = st.columns(4)
    k1.metric(
        "Average Monthly Collection Rate",
        fmt_pct(avg_rate),
        help=f"Mean across {len(cashflow)} months of activity",
    )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=cashflow["month"],
        y=cashflow["total_scheduled"],
        mode="lines+markers",
        name="Scheduled Payments",
        line=dict(color=SECONDARY, width=3, dash="dash"),
        marker=dict(size=7, color=SECONDARY,
                    line=dict(color="white", width=1.5)),
        hovertemplate=(
            "<b>%{x}</b><br>Scheduled: %{y:$,.0f}<extra></extra>"
        ),
    ))
    fig1.add_trace(go.Scatter(
        x=cashflow["month"],
        y=cashflow["total_collected"],
        mode="lines+markers",
        name="Actual Collections",
        line=dict(color=SUCCESS, width=3),
        marker=dict(size=7, color=SUCCESS,
                    line=dict(color="white", width=1.5)),
        hovertemplate=(
            "<b>%{x}</b><br>Collected: %{y:$,.0f}<extra></extra>"
        ),
    ))
    fig1.update_xaxes(title="Month")
    fig1.update_yaxes(title="Dollar Amount (USD)", tickprefix="$",
                      tickformat=",.0f")
    style_figure(
        fig1,
        title="Monthly Scheduled vs Actual Collections",
        height=440,
    )
    fig1.update_layout(
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)

    mean_gap = cashflow["total_gap"].mean()
    bar_colors = [
        DANGER if v > mean_gap else WARNING
        for v in cashflow["total_gap"]
    ]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=cashflow["month"],
        y=cashflow["total_gap"],
        marker_color=bar_colors,
        hovertemplate=(
            "<b>%{x}</b><br>Gap: %{y:$,.0f}<extra></extra>"
        ),
        name="Payment Gap",
    ))
    fig2.add_hline(
        y=mean_gap,
        line_dash="dash",
        line_color=MUTED,
        annotation_text=f"Mean gap {fmt_money_compact(mean_gap)}",
        annotation_position="top left",
        annotation_font=dict(color=MUTED, size=11),
    )
    fig2.update_xaxes(title="Month")
    fig2.update_yaxes(title="Payment Gap (USD)", tickprefix="$",
                      tickformat=",.0f")
    style_figure(
        fig2,
        title="Monthly Payment Gap (Scheduled minus Collected)",
        height=420,
    )
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    render_footer()

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def main() -> None:
    view = render_sidebar()

    if not DATA_DIR.exists():
        st.error(
            f"Data folder not found: {DATA_DIR}\n\n"
            "Expected the four `rpt_*.csv` files inside a "
            "`/tableau_exports` folder next to `app.py`."
        )
        return

    if view == "Portfolio Overview":
        view_portfolio_overview()
    elif view == "Industry Performance":
        view_industry_performance()
    elif view == "Cohort Performance":
        view_cohort_performance()
    elif view == "Monthly Cashflow":
        view_monthly_cashflow()


if __name__ == "__main__":
    main()
