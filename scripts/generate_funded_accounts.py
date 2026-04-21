"""
ClearFund Capital — Mock Data Generator: funded_accounts
--------------------------------------------------------
Generates a realistic mock portfolio of 800 revenue-based small-business
loans for the fictional lender "ClearFund Capital".

Output: data/raw/funded_accounts.csv

Run:
    python scripts/generate_funded_accounts.py
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_ACCOUNTS = 800
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "funded_accounts.csv"

INDUSTRIES = [
    "Retail",
    "Food & Beverage",
    "Healthcare",
    "E-Commerce",
    "Construction",
    "Logistics",
]

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

REPAYMENT_STATUSES = ["On Track", "Paid Off", "Late", "Defaulted"]
REPAYMENT_WEIGHTS = [0.55, 0.20, 0.15, 0.10]

REPAYMENT_TERMS = [6, 9, 12, 18]
REPAYMENT_TERM_WEIGHTS = [0.20, 0.30, 0.35, 0.15]

BUSINESS_PREFIXES = [
    "Summit", "Blue River", "Ironclad", "Evergreen", "Harbor", "Copper",
    "Maple Lane", "Stonebridge", "Oakline", "Silver Creek", "Redwood",
    "Northwind", "Golden State", "Cascade", "Lakeside", "Downtown",
    "Midtown", "Urban", "Coastal", "Highland", "Prairie", "Sunrise",
    "Rocky Peak", "Lone Star", "Bayview", "Pine Hollow", "Cedar Grove",
    "Willow", "Granite", "Sapphire", "Emerald", "Brookstone", "Heritage",
    "Liberty", "Patriot", "Vanguard", "Beacon", "Compass", "Meridian",
    "Horizon", "Pioneer", "Hometown", "Mainline", "Market Street",
    "First Avenue", "Trailhead", "Keystone", "Old Town", "New Day",
    "Crossroads",
]

BUSINESS_SUFFIX_BY_INDUSTRY = {
    "Retail": [
        "Boutique", "Outfitters", "Mercantile", "Trading Co.", "Emporium",
        "Supply Co.", "Goods", "Market", "Dry Goods", "Apparel",
    ],
    "Food & Beverage": [
        "Kitchen", "Cafe", "Bistro", "Bakery", "Grill", "Taproom",
        "Coffee Co.", "Pizzeria", "Eatery", "Smokehouse",
    ],
    "Healthcare": [
        "Family Dental", "Wellness Clinic", "Physical Therapy",
        "Urgent Care", "Chiropractic", "Vision Center", "Pediatrics",
        "Medical Group", "Home Health", "Dermatology",
    ],
    "E-Commerce": [
        "Online", "Digital", "Direct", "Shop", "Marketplace", "Fulfillment",
        "DTC", "Storefront", "Commerce Co.", "Outlet",
    ],
    "Construction": [
        "Builders", "Contracting", "Roofing", "Plumbing", "HVAC Services",
        "Electric", "Masonry", "Remodeling", "Excavation", "Carpentry",
    ],
    "Logistics": [
        "Freight", "Trucking", "Transport", "Delivery Co.", "Cartage",
        "Dispatch", "Hauling", "Logistics Group", "Express", "Fleet Services",
    ],
}


def generate_business_name(rng: np.random.Generator, industry: str) -> str:
    prefix = rng.choice(BUSINESS_PREFIXES)
    suffix = rng.choice(BUSINESS_SUFFIX_BY_INDUSTRY[industry])
    return f"{prefix} {suffix}"


def generate_funding_amounts(rng: np.random.Generator, n: int) -> np.ndarray:
    """
    Realistic right-skewed distribution: most loans cluster in the
    $25k-$80k range with a long tail up to $250k. Uses a log-normal
    draw, then clips to [10_000, 250_000] and rounds to the nearest $500.
    """
    mu = np.log(55_000)
    sigma = 0.55
    raw = rng.lognormal(mean=mu, sigma=sigma, size=n)
    clipped = np.clip(raw, 10_000, 250_000)
    rounded = np.round(clipped / 500.0) * 500
    return rounded.astype(int)


def generate_disbursement_dates(rng: np.random.Generator, n: int) -> pd.Series:
    start = pd.Timestamp("2023-01-01")
    end = pd.Timestamp("2024-12-31")
    total_days = (end - start).days
    offsets = rng.integers(low=0, high=total_days + 1, size=n)
    return pd.to_datetime(start + pd.to_timedelta(offsets, unit="D"))


def build_dataset(n: int = N_ACCOUNTS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    account_ids = [f"ACC-{i:04d}" for i in range(1, n + 1)]

    industries = rng.choice(INDUSTRIES, size=n)
    business_names = [generate_business_name(rng, ind) for ind in industries]
    states = rng.choice(US_STATES, size=n)

    disbursement_dates = generate_disbursement_dates(rng, n)
    funding_amounts = generate_funding_amounts(rng, n)

    repayment_terms = rng.choice(
        REPAYMENT_TERMS, size=n, p=REPAYMENT_TERM_WEIGHTS
    ).astype(int)

    factor_rates = np.round(rng.uniform(1.15, 1.45, size=n), 3)

    origination_fee_pct = rng.uniform(0.015, 0.030, size=n)
    origination_fees = np.round(funding_amounts * origination_fee_pct, 2)

    repayment_statuses = rng.choice(
        REPAYMENT_STATUSES, size=n, p=REPAYMENT_WEIGHTS
    )

    total_repayable = funding_amounts * factor_rates
    monthly_payments = np.round(total_repayable / repayment_terms, 2)

    df = pd.DataFrame(
        {
            "account_id": account_ids,
            "business_name": business_names,
            "industry": industries,
            "state": states,
            "disbursement_date": disbursement_dates.strftime("%Y-%m-%d"),
            "funding_amount": funding_amounts,
            "repayment_term_months": repayment_terms,
            "factor_rate": factor_rates,
            "origination_fee": origination_fees,
            "repayment_status": repayment_statuses,
            "monthly_payment_amount": monthly_payments,
        }
    )

    return df


def main() -> None:
    df = build_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(df):,} rows to {OUTPUT_PATH}")
    print("\nPreview:")
    print(df.head(10).to_string(index=False))
    print("\nRepayment status distribution:")
    print(df["repayment_status"].value_counts(normalize=True).round(3))
    print("\nIndustry distribution:")
    print(df["industry"].value_counts())


if __name__ == "__main__":
    main()
