# ClearFund Capital — Small Business Lending Portfolio Analytics Dashboard

An end-to-end financial data analytics demo simulating portfolio reporting,
SQL transformation layering, QA validation, and interactive web dashboard
delivery for a revenue-based alternative lending company.

---

## Why I built this

I built this as a recruiter-facing demo for Financial Data Analyst role at an
alternative lending company. The job description talks about automating
financial reporting, validating portfolio data, and shipping analytics to the
business — so instead of listing those skills on a resume, I built a working
version of the job.

Every piece of this repo mirrors something an analyst on a lending team
would actually do on a Tuesday afternoon: generate a realistic book of
loans, move it through a three-tier SQL pipeline, flag data-quality issues
before anything reaches a stakeholder, and deliver the final numbers as an
interactive dashboard a non-technical person can read in thirty seconds.
The data is mock.

---

## Tech stack

- **Python** — data generation (`numpy`, `pandas`) and SQLite loaders
- **SQL (SQLite)** — raw → cleaned → reporting → QA layer transformations
- **HTML / CSS / vanilla JavaScript** — single-file dashboard
- **Chart.js** — all charts in the web dashboard
- **PapaParse** — client-side CSV parsing
- **GitHub Pages** — static hosting for the live dashboard

---

## Project architecture

```
   Raw CSVs (Python Generated)
        │
        ▼
   SQLite — Raw Layer
        │
        ▼
   SQLite — Cleaned Layer
     (nulls handled, types cast, business rules applied)
        │
        ▼
   SQLite — Reporting Layer  (rpt_ tables)
        │
        ▼
   QA Validation Script
     (6 automated checks, PASS / FAIL output)
        │
        ▼
   CSV Exports  →  index.html  (Chart.js Dashboard)
    
```


## Phase breakdown

### 1. Data generation

A trio of Python scripts produces a realistic mock portfolio: 800 funded
loans across six industries, 6,226 monthly repayment transactions, and one
business-profile record per account. Funding amounts follow a log-normal
distribution centered around typical small-business ticket sizes rather
than a flat uniform, so the book looks like something an actual lender
would hold. Status, late behavior, and default cutoffs are all driven by
weighted probabilities seeded for reproducibility. About 2% of payment
records have injected nulls — deliberately — so the QA layer has something
real to catch.

### 2. SQL transformation

The reporting stack is three-tier: **raw → cleaned → reporting.** The
cleaned layer casts types, standardizes industry and state codes, handles
nulls, and derives fields the business cares about — `total_repayable`,
`net_funding`, `disbursement_cohort`, `is_payment_gap`, `size_segment`.
The reporting layer builds four analyst-ready tables on top of that:
account-level portfolio summary, industry performance, cohort vintages,
and monthly cashflow. Everything is materialized as a table (not a view)
so downstream consumers — the dashboard, Excel, Tableau — get consistent,
fast reads.

### 3. QA validation

Before any number goes on a dashboard, it has to pass a six-check gate:
null primary keys, negative balances, orphan accounts, overpayment beyond
tolerance, status-vs-ledger mismatch, and unknown payment status. Every
check writes a row to `qa_validation_results` with a severity, a flagged
count, a PASS / FAIL verdict, and a note explaining what the check is
guarding against. In this portfolio three warnings fire — each one has a
defensible business explanation (just-disbursed loans with no installments
yet, a known status-vs-ledger reconciliation gap, and the injected null
rate in the payments feed). That separation of "alarm" vs "expected
finding" is what makes the QA layer usable in practice.

### 4. Web dashboard

The final deliverable is a single `index.html` page that parses the
exported CSVs in the browser and renders four interactive views with
Chart.js. It loads locally from a plain HTTP server and from GitHub Pages
with no configuration — the whole app is roughly 38 KB of HTML, CSS, and
JavaScript with two pinned CDN dependencies.

---

## How to run locally

```bash
# 1. Clone
git clone https://github.com/<your-username>/Small-Business-Lending-Portfolio-Dashboard.git
cd Small-Business-Lending-Portfolio-Dashboard

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Generate the mock portfolio (raw CSVs)
python scripts/generate_funded_accounts.py
python scripts/generate_repayment_transactions.py
python scripts/generate_business_profiles.py

# 4. Load into SQLite and build the SQL layers
python scripts/load_raw_to_sqlite.py
python scripts/run_sql.py sql/cleaned
python scripts/run_sql.py sql/reporting
python scripts/run_sql.py sql/qa

# 5. Export the reporting tables as CSVs for the dashboard
python scripts/export_for_tableau.py

# 6. Serve the dashboard over HTTP (browsers block file:// fetches by default)
python3 -m http.server 8000
```

Then open **http://localhost:8000/index.html** in any modern browser.

---

## Dashboard views

1. **Portfolio Overview** — How big is the book, and where are the dollars?
   Answers total funded, collected, outstanding, and overall collection
   rate in four tiles, with an industry breakdown and status mix.
2. **Industry Performance** — Which industries are dragging on the
   portfolio? Compares default and late rates side-by-side and shows the
   status mix per industry.
3. **Cohort Performance** — Are newer loans performing better or worse
   than older ones? Tracks average percent repaid and default rate by
   disbursement month, with a color-coded detail table.
4. **Monthly Cashflow** — Are we collecting what we're owed this month?
   Plots scheduled vs. actual collections over time and flags months with
   above-average shortfall.

---

## Closing note

Built to demonstrate end-to-end financial data analytics capability
including SQL query optimization, data transformation layering, QA
validation logic, and dashboard delivery — mirroring the core
responsibilities of a Financial Data Analyst role in the alternative
lending space.

Built by **Pooja Pranavi Nalamothu**.
