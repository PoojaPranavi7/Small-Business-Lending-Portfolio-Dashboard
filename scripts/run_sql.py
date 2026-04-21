"""
ClearFund Capital — SQL Layer Runner
------------------------------------
Executes every *.sql file in a directory (alphabetically, which is why
the files are prefixed 01_, 02_, 03_ ...) against the local SQLite
database.

Run the cleaned layer:
    python scripts/run_sql.py sql/cleaned

Run any other layer later:
    python scripts/run_sql.py sql/reporting
    python scripts/run_sql.py sql/qa
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "clearfund_portfolio.db"


def run_sql_directory(sql_dir: Path, db_path: Path = DB_PATH) -> int:
    if not sql_dir.exists():
        print(f"ERROR: SQL directory not found: {sql_dir}", file=sys.stderr)
        return 1

    sql_files = sorted(sql_dir.glob("*.sql"))
    if not sql_files:
        print(f"ERROR: no .sql files found in {sql_dir}", file=sys.stderr)
        return 1

    if not db_path.exists():
        print(
            f"ERROR: database not found at {db_path}. "
            "Run scripts/load_raw_to_sqlite.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"Database : {db_path}")
    print(f"SQL dir  : {sql_dir}\n")

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as exc:
        print(f"ERROR: could not open database: {exc}", file=sys.stderr)
        return 1

    try:
        for sql_file in sql_files:
            script = sql_file.read_text()
            try:
                with conn:
                    conn.executescript(script)
                print(f"  [OK]   {sql_file.name}")
            except sqlite3.Error as exc:
                print(f"  [FAIL] {sql_file.name}: {exc}", file=sys.stderr)
                return 2

        print("\nTables now in database:")
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' ORDER BY name"
        )
        for (name,) in cursor.fetchall():
            (count,) = conn.execute(
                f'SELECT COUNT(*) FROM "{name}"'
            ).fetchone()
            print(f"  {name:40s} {count:>6,} rows")
    finally:
        conn.close()

    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/run_sql.py <sql_directory>",
              file=sys.stderr)
        return 1
    return run_sql_directory(Path(argv[1]).resolve())


if __name__ == "__main__":
    sys.exit(main(sys.argv))
