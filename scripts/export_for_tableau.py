"""
ClearFund Capital — Tableau Export
----------------------------------
Reads the four reporting-layer tables out of the local SQLite database
and writes them as CSV files for ingestion into Tableau Public.

Tableau Public cannot connect live to SQLite, so the workflow is:
    1. Build the reporting layer:  python scripts/run_sql.py sql/reporting
    2. Export to CSV:              python scripts/export_for_tableau.py
    3. Upload the CSVs as data sources in Tableau Public.

Output:
    tableau_exports/rpt_portfolio_summary.csv
    tableau_exports/rpt_industry_performance.csv
    tableau_exports/rpt_cohort_performance.csv
    tableau_exports/rpt_monthly_cashflow.csv
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "clearfund_portfolio.db"
EXPORT_DIR = ROOT / "tableau_exports"

REPORTING_TABLES: list[str] = [
    "rpt_portfolio_summary",
    "rpt_industry_performance",
    "rpt_cohort_performance",
    "rpt_monthly_cashflow",
]


def export_table(conn: sqlite3.Connection, table: str, out_dir: Path) -> pd.DataFrame:
    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    out_path = out_dir / f"{table}.csv"
    df.to_csv(out_path, index=False)
    return df


def preview_dataframe(df: pd.DataFrame, n: int = 3) -> str:
    return df.head(n).to_string(index=False)


def main() -> int:
    if not DB_PATH.exists():
        print(
            f"ERROR: database not found at {DB_PATH}. "
            "Run the loader and SQL layers first.",
            file=sys.stderr,
        )
        return 1

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Database    : {DB_PATH}")
    print(f"Export dir  : {EXPORT_DIR}\n")

    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as exc:
        print(f"ERROR: could not open database: {exc}", file=sys.stderr)
        return 1

    exit_code = 0
    try:
        for table in REPORTING_TABLES:
            try:
                df = export_table(conn, table, EXPORT_DIR)
            except (pd.errors.DatabaseError, sqlite3.Error) as exc:
                print(f"  [FAIL] {table}: {exc}", file=sys.stderr)
                exit_code = 2
                continue

            header = f"  [OK] {table}.csv  ({len(df):,} rows, {len(df.columns)} cols)"
            print(header)
            print("  " + "-" * (len(header) - 2))
            for line in preview_dataframe(df).splitlines():
                print("    " + line)
            print()
    finally:
        conn.close()

    if exit_code == 0:
        print("Export complete. Upload these CSVs to Tableau Public as data sources.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
