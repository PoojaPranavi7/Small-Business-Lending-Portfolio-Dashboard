-- =============================================================
-- REPORTING LAYER  |  rpt_monthly_cashflow
-- =============================================================
-- Grain  : one row per calendar month of transaction_date ('YYYY-MM')
-- Purpose: drives the cashflow / collections trend view --
--          "How is the portfolio performing this month vs. last month?"
--
-- Source : cleaned_repayment_transactions (the ledger). We deliberately
--          aggregate straight from the ledger, not from the account
--          summary, because the KPI is calendar-month collections
--          across all accounts active in that month.
-- =============================================================

DROP TABLE IF EXISTS rpt_monthly_cashflow;

CREATE TABLE rpt_monthly_cashflow AS
SELECT
    STRFTIME('%Y-%m', transaction_date)                  AS month,

    -- what we were supposed to collect this month, across all accounts
    ROUND(SUM(scheduled_payment),    2)                  AS total_scheduled,

    -- what we actually collected (NULLs are already coalesced to 0 in
    -- the cleaned layer, so this is a safe SUM)
    ROUND(SUM(actual_payment_made),  2)                  AS total_collected,

    -- collection shortfall: positive = underpayment, negative = overpayment.
    -- Not floored at 0 on purpose -- a negative gap (overcollection) is
    -- a signal worth showing rather than hiding.
    ROUND(
        SUM(scheduled_payment) - SUM(actual_payment_made),
        2
    )                                                    AS total_gap,

    -- the flagship month-over-month KPI.
    -- * 100.0 forces float division; NULLIF prevents divide-by-zero
    -- on any month with (hypothetically) $0 scheduled.
    ROUND(
        SUM(actual_payment_made) * 100.0
        / NULLIF(SUM(scheduled_payment), 0),
        2
    )                                                    AS collection_rate

FROM cleaned_repayment_transactions
GROUP BY STRFTIME('%Y-%m', transaction_date)
ORDER BY month;
