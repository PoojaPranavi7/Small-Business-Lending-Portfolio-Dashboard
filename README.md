# CFG Mock Analytics — Portfolio Analytics Dashboard

A multi-page Plotly Dash web application that visualizes a small-business
lending portfolio — funded volume, industry risk, cohort vintages, and
monthly collections — for a fictional revenue-based lender.

## Views

1. **Portfolio Overview** — KPI tiles, status mix, top industries by funded volume.
2. **Industry Performance** — industry funded colored by default rate, default vs. late rate comparison, industry positioning scatter.
3. **Monthly Cash Flow Trend** — dual-axis collections vs. collection rate with a dashed average reference line, cumulative collections area chart, date-range filter.
4. **Cohort Performance** — green-to-red performance heatmap, metric comparison bars, full styled data table with risk-based conditional formatting.

## Quick start (local)

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:8050** in a browser.

## Project layout

```
.
├── app.py                        # Dash app (all views, callbacks)
├── assets/
│   └── custom.css                # theme + component styling
├── data/                         # CSV inputs consumed by the app
│   ├── rpt_portfolio_summary.csv
│   ├── rpt_industry_performance.csv
│   ├── rpt_monthly_cashflow.csv
│   └── rpt_cohort_performance.csv
├── requirements.txt
├── Procfile                      # gunicorn command for Render / Heroku
├── render.yaml                   # Render free-tier blueprint
└── README.md
```

## Deploy on Render (free tier)

1. Push this repo to GitHub.
2. In Render, **New → Blueprint**, point at the repo.
3. Render picks up `render.yaml` and spins up a web service on the free plan.
4. First boot takes ~2 minutes; subsequent deploys are incremental.

The `Procfile` is provided for any other gunicorn-based host (Heroku, Fly.io)
that prefers it over `render.yaml`.

## Design

- **Color theme** — primary `#1F4E79`, secondary `#2E75B6`, accent `#4BACC6`,
  page background `#F4F8FB`, success `#1E7D45`, danger `#C00000`. All charts
  share one Plotly template so no sheet looks foreign.
- **Typography** — Inter / Helvetica Neue / Segoe UI fallback stack.
- **Responsive** — Bootstrap grid on all rows; navbar, KPI cards, and charts
  reflow on mobile.
- **Accessibility** — every chart has a title, axis labels, and a rich
  hover tooltip; the data table has a sticky header and alternating
  row colors with risk-tier color highlights.

## Built by

Pooja Pranavi Nalamothu.
