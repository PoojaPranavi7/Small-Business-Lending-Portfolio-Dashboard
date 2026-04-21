"""
ClearFund Capital — Mock Data Generator: repayment_transactions
---------------------------------------------------------------
Builds a monthly repayment ledger off of the funded_accounts.csv produced
by `generate_funded_accounts.py`.

Rules:
  - One row per account per scheduled month, from the month AFTER
    disbursement up to the earlier of (a) end of repayment term, or
    (b) December 2024.
  - transaction_date is the month-end of that month.
  - payment behavior is driven by the parent account's repayment_status:
      * On Track / Paid Off  -> every installment paid in full.
      * Late                 -> ~60% partial (70-95% of scheduled), ~40% full.
      * Defaulted            -> full payments up to a random cutoff between
                                ~1/3 and ~2/3 of the scheduled term, then
                                every subsequent month is Missed (0 paid).
  - ~2% of rows get a null injected into actual_payment_made, and
    ~2% into payment_status, independently, to simulate real-world data
    quality issues (to be caught by the QA SQL layer later).

Output: data/raw/repayment_transactions.csv

Run:
    python scripts/generate_repayment_transactions.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
PORTFOLIO_AS_OF = pd.Timestamp("2024-12-31")
NULL_RATE_ACTUAL = 0.02
NULL_RATE_STATUS = 0.02

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "funded_accounts.csv"
OUTPUT_PATH = ROOT / "data" / "raw" / "repayment_transactions.csv"


def build_schedule(disbursement_date: pd.Timestamp, term_months: int) -> pd.DatetimeIndex:
    """
    Monthly payment dates = month-end of (disbursement month + k) for
    k = 1..term_months, truncated at PORTFOLIO_AS_OF.
    """
    first_period = disbursement_date.to_period("M") + 1
    periods = pd.period_range(start=first_period, periods=term_months, freq="M")
    month_ends = periods.to_timestamp(how="end").normalize()
    return month_ends[month_ends <= PORTFOLIO_AS_OF]


def simulate_account_payments(
    rng: np.random.Generator,
    scheduled_payment: float,
    n_installments: int,
    term_months: int,
    repayment_status: str,
) -> tuple[np.ndarray, list[str]]:
    """
    Returns (actual_payments, payment_statuses) arrays of length n_installments.
    """
    if n_installments == 0:
        return np.array([], dtype=float), []

    actuals = np.full(n_installments, scheduled_payment, dtype=float)
    statuses = ["Paid"] * n_installments

    if repayment_status in ("On Track", "Paid Off"):
        pass

    elif repayment_status == "Late":
        is_partial = rng.random(n_installments) < 0.60
        partial_ratio = rng.uniform(0.70, 0.95, size=n_installments)
        actuals = np.where(is_partial, scheduled_payment * partial_ratio, scheduled_payment)
        statuses = ["Partial" if p else "Paid" for p in is_partial]

    elif repayment_status == "Defaulted":
        low = max(1, term_months // 3)
        high = max(low + 1, (2 * term_months) // 3)
        cutoff_term_month = int(rng.integers(low=low, high=high + 1))
        cutoff = min(cutoff_term_month, n_installments)
        for i in range(cutoff, n_installments):
            actuals[i] = 0.0
            statuses[i] = "Missed"

    actuals = np.round(actuals, 2)
    return actuals, statuses


def build_transactions(accounts: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    records: list[dict] = []

    for _, acct in accounts.iterrows():
        disbursement = pd.Timestamp(acct["disbursement_date"])
        term = int(acct["repayment_term_months"])
        scheduled = float(acct["monthly_payment_amount"])
        status = str(acct["repayment_status"])

        schedule = build_schedule(disbursement, term)
        n = len(schedule)
        if n == 0:
            continue

        actuals, pay_statuses = simulate_account_payments(
            rng=rng,
            scheduled_payment=scheduled,
            n_installments=n,
            term_months=term,
            repayment_status=status,
        )

        for tx_date, actual, pay_status in zip(schedule, actuals, pay_statuses):
            records.append(
                {
                    "account_id": acct["account_id"],
                    "transaction_date": tx_date.strftime("%Y-%m-%d"),
                    "scheduled_payment": round(scheduled, 2),
                    "actual_payment_made": actual,
                    "payment_status": pay_status,
                }
            )

    df = pd.DataFrame.from_records(records)

    df.insert(
        0,
        "transaction_id",
        [f"TXN-{i:08d}" for i in range(1, len(df) + 1)],
    )

    inject_nulls(df, rng)

    df["payment_variance"] = np.where(
        df["actual_payment_made"].isna(),
        np.nan,
        (df["actual_payment_made"] - df["scheduled_payment"]).round(2),
    )

    df = df[
        [
            "transaction_id",
            "account_id",
            "transaction_date",
            "scheduled_payment",
            "actual_payment_made",
            "payment_variance",
            "payment_status",
        ]
    ]

    return df


def inject_nulls(df: pd.DataFrame, rng: np.random.Generator) -> None:
    n = len(df)

    actual_null_mask = rng.random(n) < NULL_RATE_ACTUAL
    df.loc[actual_null_mask, "actual_payment_made"] = np.nan

    status_null_mask = rng.random(n) < NULL_RATE_STATUS
    df.loc[status_null_mask, "payment_status"] = np.nan


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_PATH}. Run generate_funded_accounts.py first."
        )

    accounts = pd.read_csv(INPUT_PATH)
    transactions = build_transactions(accounts)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    transactions.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(transactions):,} rows to {OUTPUT_PATH}")
    print(f"  Accounts covered: {transactions['account_id'].nunique():,}")
    print(
        "  Avg installments per account: "
        f"{len(transactions) / transactions['account_id'].nunique():.2f}"
    )

    print("\nPreview:")
    print(transactions.head(10).to_string(index=False))

    print("\nPayment status distribution (non-null):")
    print(transactions["payment_status"].value_counts(dropna=False))

    print("\nNull rates (data quality injection):")
    print(
        pd.Series(
            {
                "actual_payment_made": transactions["actual_payment_made"].isna().mean(),
                "payment_status": transactions["payment_status"].isna().mean(),
                "payment_variance": transactions["payment_variance"].isna().mean(),
            }
        ).round(4)
    )


if __name__ == "__main__":
    main()
