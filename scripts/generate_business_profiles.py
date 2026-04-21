"""
ClearFund Capital — Mock Data Generator: business_profiles
----------------------------------------------------------
Produces one firmographic profile row per account in funded_accounts.csv.

Design notes:
  - employee_count is drawn from a right-skewed triangular distribution
    peaked near 5, because the SMB universe is dominated by very small
    shops; a flat uniform 1-50 would over-represent 40+ headcount firms.
  - annual_revenue_band is sampled with realistic lender-book weights
    (Under $500K and $500K-$1M are the most common tickets).
  - years_in_business uses a triangular distribution peaked near year 4,
    reflecting that alternative-finance customers skew younger but are
    rarely brand-new.
  - repeat_borrower is exactly 20% True (Bernoulli p=0.2).

Output: data/raw/business_profiles.csv

Run:
    python scripts/generate_business_profiles.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "funded_accounts.csv"
OUTPUT_PATH = ROOT / "data" / "raw" / "business_profiles.csv"

REVENUE_BANDS = ["Under $500K", "$500K-$1M", "$1M-$5M", "Over $5M"]
REVENUE_WEIGHTS = [0.30, 0.35, 0.25, 0.10]

REPEAT_BORROWER_RATE = 0.20


def draw_employee_counts(rng: np.random.Generator, n: int) -> np.ndarray:
    """Right-skewed: most firms 1-15 employees, long tail up to 50."""
    raw = rng.triangular(left=1, mode=5, right=50, size=n)
    return np.clip(np.round(raw), 1, 50).astype(int)


def draw_years_in_business(rng: np.random.Generator, n: int) -> np.ndarray:
    """Skewed toward 3-6 years in business, range 1-20."""
    raw = rng.triangular(left=1, mode=4, right=20, size=n)
    return np.clip(np.round(raw), 1, 20).astype(int)


def build_profiles(account_ids: pd.Series, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(account_ids)

    df = pd.DataFrame(
        {
            "account_id": account_ids.values,
            "employee_count": draw_employee_counts(rng, n),
            "annual_revenue_band": rng.choice(
                REVENUE_BANDS, size=n, p=REVENUE_WEIGHTS
            ),
            "years_in_business": draw_years_in_business(rng, n),
            "repeat_borrower": rng.random(n) < REPEAT_BORROWER_RATE,
        }
    )

    return df


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_PATH}. Run generate_funded_accounts.py first."
        )

    accounts = pd.read_csv(INPUT_PATH, usecols=["account_id"])
    profiles = build_profiles(accounts["account_id"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(profiles):,} rows to {OUTPUT_PATH}")

    print("\nPreview:")
    print(profiles.head(10).to_string(index=False))

    print("\nEmployee count summary:")
    print(profiles["employee_count"].describe().round(2))

    print("\nRevenue band distribution:")
    print(profiles["annual_revenue_band"].value_counts(normalize=True).round(3))

    print("\nYears in business summary:")
    print(profiles["years_in_business"].describe().round(2))

    print(
        f"\nRepeat borrower share: "
        f"{profiles['repeat_borrower'].mean():.1%}"
    )


if __name__ == "__main__":
    main()
