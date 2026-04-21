"""
ClearFund Capital — Raw Layer Loader
------------------------------------
Loads the three generated CSVs into a local SQLite database as the
raw/bronze layer. Tables are replaced on every run so this script is
idempotent and safe to re-run after regenerating the CSVs.

Mapping:
    data/raw/funded_accounts.csv         -> raw_funded_accounts
    data/raw/repayment_transactions.csv  -> raw_repayment_transactions
    data/raw/business_profiles.csv       -> raw_business_profiles

Target DB:
    data/clearfund_portfolio.db

Run:
    python scripts/load_raw_to_sqlite.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "clearfund_portfolio.db"

RAW_SOURCES: list[tuple[str, str]] = [
    ("funded_accounts.csv", "raw_funded_accounts"),
    ("repayment_transactions.csv", "raw_repayment_transactions"),
    ("business_profiles.csv", "raw_business_profiles"),
]


def load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Source CSV not found: {csv_path}. "
            "Run the generator scripts in scripts/ first."
        )
    try:
        return pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{csv_path} is empty.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"Could not parse {csv_path}: {exc}") from exc


def load_table(conn: sqlite3.Connection, df: pd.DataFrame, table: str) -> int:
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
    except (sqlite3.DatabaseError, ValueError) as exc:
        raise RuntimeError(f"Failed to write table '{table}': {exc}") from exc
    return verify_row_count(conn, table)


def verify_row_count(conn: sqlite3.Connection, table: str) -> int:
    cursor = conn.execute(f'SELECT COUNT(*) FROM "{table}"')
    (count,) = cursor.fetchone()
    return int(count)


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Target database: {DB_PATH}")
    print(f"Source directory: {RAW_DIR}\n")

    results: list[tuple[str, int]] = []

    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as exc:
        print(f"ERROR: could not open SQLite database at {DB_PATH}: {exc}",
              file=sys.stderr)
        return 1

    try:
        with conn:
            for csv_name, table in RAW_SOURCES:
                csv_path = RAW_DIR / csv_name
                try:
                    df = load_csv(csv_path)
                    row_count = load_table(conn, df, table)
                    results.append((table, row_count))
                    print(f"  [OK]   {csv_name:35s} -> {table:30s} "
                          f"({row_count:>6,} rows)")
                except (FileNotFoundError, ValueError, RuntimeError) as exc:
                    print(f"  [FAIL] {csv_name:35s} -> {table:30s}  {exc}",
                          file=sys.stderr)
                    return 2
    finally:
        conn.close()

    print("\nLoad complete. Row counts:")
    for table, count in results:
        print(f"  {table:30s} {count:>6,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
