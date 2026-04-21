# ClearFund Capital - Small Business Lending Portfolio Analytics Dashboard

Live Dashboard https://clearfund-capital-dashboard.streamlit.app/

> An end-to-end financial data analytics demo simulating portfolio reporting, SQL transformation layering, QA validation, and interactive Streamlit dashboard delivery for a revenue-based alternative lending company.

---

## Why I Built This

I built this project as a recruiter-facing demo for a **Financial Data Analyst** role at **CFG Merchant Solutions**, a revenue-based alternative lending company that finances small and mid-sized businesses.

The goal was to show — not claim — that I can do the actual work the role requires: automate financial reporting, write optimized SQL transformation layers, build QA validation logic that catches bad data before it reaches a stakeholder, and ship an interactive analytics dashboard a portfolio manager could open and use today.

Everything in this repo runs end-to-end from raw Python-generated data to a live Streamlit URL. No screenshots, no slideware.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Python** | Data generation, pipeline scripting, CSV exports |
| **SQL / SQLite** | Raw, cleaned, and reporting layer transformations |
| **pandas** | Data manipulation and transformation |
| **Streamlit** | Interactive multi-view web dashboard |
| **Plotly** | Chart rendering (bar, line, dual-axis, stacked) |
| **GitHub Pages / Streamlit Cloud** | Live hosting and sharing |

---

## Project Architecture

```
Phase 1 — Python Scripts (Data Generation)
     ↓
funded_accounts.csv  +  repayment_transactions.csv  +  business_profiles.csv
     ↓
Phase 2 — SQLite Database (clearfund_portfolio.db)
[ Raw Layer  →  Cleaned Layer  →  Reporting Layer ]
     ↓
Phase 2.4 — QA Validation Script
(6 automated checks, PASS / FAIL output)
     ↓
Phase 3.1 — CSV Exports (/tableau_exports folder)
rpt_portfolio_summary | rpt_industry_performance | rpt_cohort_performance | rpt_monthly_cashflow
     ↓
Phase 3.2 — Streamlit App (app.py)
     ↓
Streamlit Community Cloud  →  Live Public URL
```

---

## Phase Breakdown

### Phase 1 — Data Generation

Three mock datasets were generated using Python to simulate the book of business of a fictional alternative lender called **ClearFund Capital**: 800 funded accounts, the corresponding monthly repayment transactions, and one business profile per account. Funding amounts use a log-normal distribution clipped to the realistic $10K–$250K small business range, repayment statuses follow a weighted distribution (55% On Track, 20% Paid Off, 15% Late, 10% Defaulted), and roughly 2% nulls are intentionally injected into the transactions table so the QA layer downstream has something real to detect.

### Phase 2 — SQL Transformation Layer

Raw CSVs are loaded into a local SQLite database and transformed through three structured layers. The **raw layer** is a direct, typed-as-text load. The **cleaned layer** handles nulls, casts dates, standardizes industry and state values, applies business rules (e.g. `total_repayable = funding_amount × factor_rate`), and derives features like `disbursement_cohort` and `is_payment_gap`. The **reporting layer** produces four aggregated `rpt_` tables ready for direct dashboard consumption. A separate **QA validation script** then runs 6 automated checks — null primary keys, negative balances, orphan accounts, overpayments, status mismatches, and unknown payment statuses — and emits a PASS/FAIL result per check with severity and notes, so a reviewer can immediately see whether the data is dashboard-ready.

### Phase 3 — Streamlit Dashboard

`app.py` reads the four reporting CSVs and renders a 4-view interactive dashboard built with Plotly. Each view uses `st.metric` KPI tiles, dynamic filters, color-coded tables, and a consistent finance-appropriate design system (navy primary, status-colored accents, white cards, transparent chart backgrounds). Each view answers one specific business question — overall portfolio health, industry concentration risk, cohort vintage performance, and monthly cashflow vs. plan — rather than dumping every metric on every page.

### Phase 4 — GitHub & Deployment

The full project is version-controlled on GitHub with a clean folder structure separating data generation, SQL layers, exports, and the dashboard app. The Streamlit app is deployed to **Streamlit Community Cloud** as a single public URL that can be shared directly with recruiters and hiring managers — no install, no setup, just a link.

---

## How To Run Locally

1. **Clone the repo**

   ```bash
   git clone https://github.com/YOUR-USERNAME/clearfund-portfolio-dashboard.git
   cd clearfund-portfolio-dashboard
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Generate the raw datasets (Phase 1)**

   ```bash
   python scripts/generate_funded_accounts.py
   python scripts/generate_repayment_transactions.py
   python scripts/generate_business_profiles.py
   ```

4. **Load and transform — raw → cleaned → reporting (Phase 2)**

   ```bash
   python scripts/load_raw_to_sqlite.py
   python scripts/run_sql.py sql/cleaned
   python scripts/run_sql.py sql/reporting
   python scripts/run_sql.py sql/qa
   ```

5. **Export the four dashboard CSVs (Phase 3.1)**

   ```bash
   python scripts/export_for_tableau.py
   ```

6. **Launch the Streamlit dashboard (Phase 3.2)**

   ```bash
   streamlit run app.py
   ```

7. **Open the dashboard**

   Navigate to <http://localhost:8501> in your browser.

---

## Dashboard Views

| View | Charts Included | Business Question Answered |
|---|---|---|
| **Portfolio Overview** | KPI tiles, status bar chart, funded-by-industry bar chart | How is the overall portfolio performing and where is funding concentrated? |
| **Industry Performance** | Default rate bar, stacked status bar, summary table | Which industries carry the highest default and late payment risk? |
| **Cohort Performance** | Repaid % line chart, funded bar chart, color-coded cohort table | Which disbursement cohorts are performing best and worst over time? |
| **Monthly Cashflow** | Dual-line scheduled vs collected, gap bar chart, collection rate KPI | Are monthly collections meeting targets and where are the problem months? |

---

## Project Folder Structure

```
clearfund-portfolio-dashboard/
│
├── app.py                                    # Streamlit dashboard entrypoint (4 views)
├── requirements.txt                          # streamlit, pandas, plotly
├── README.md                                 # This file
│
├── scripts/                                  # Python pipeline scripts
│   ├── generate_funded_accounts.py           # Phase 1 — 800 mock funded accounts
│   ├── generate_repayment_transactions.py    # Phase 1 — monthly repayment ledger
│   ├── generate_business_profiles.py         # Phase 1 — borrower profiles
│   ├── load_raw_to_sqlite.py                 # Phase 2 — CSV → SQLite raw layer
│   ├── run_sql.py                            # Phase 2 — runs all .sql files in a folder
│   └── export_for_tableau.py                 # Phase 3.1 — rpt_ tables → CSV exports
│
├── sql/                                      # SQL transformation layers
│   ├── cleaned/                              # Cleaned layer (null handling, casting, derived cols)
│   │   ├── 01_cleaned_funded_accounts.sql
│   │   ├── 02_cleaned_repayment_transactions.sql
│   │   └── 03_cleaned_business_profiles.sql
│   ├── reporting/                            # Reporting layer (aggregated rpt_ tables)
│   │   ├── 01_rpt_portfolio_summary.sql
│   │   ├── 02_rpt_industry_performance.sql
│   │   ├── 03_rpt_cohort_performance.sql
│   │   └── 04_rpt_monthly_cashflow.sql
│   └── qa/                                   # QA validation layer
│       └── 01_qa_validation.sql              # 6 automated checks, PASS/FAIL output
│
├── data/                                     # Local working data (gitignored in practice)
│   ├── raw/                                  # Raw CSVs from Phase 1
│   │   ├── funded_accounts.csv
│   │   ├── repayment_transactions.csv
│   │   └── business_profiles.csv
│   └── clearfund_portfolio.db                # SQLite database
│
└── tableau_exports/                          # Reporting CSVs the Streamlit app reads
    ├── rpt_portfolio_summary.csv
    ├── rpt_industry_performance.csv
    ├── rpt_cohort_performance.csv
    └── rpt_monthly_cashflow.csv
```

---

## About This Project

Built to demonstrate end-to-end financial data analytics capability including SQL query optimization, multi-layer data transformation, automated QA validation, and interactive dashboard delivery - mirroring the core responsibilities of a Financial Data Analyst role in the alternative lending and revenue-based financing space.
