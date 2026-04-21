-- =============================================================
-- REPORTING LAYER  |  rpt_portfolio_summary
-- =============================================================
-- Grain  : one row per account_id
-- Purpose: the primary account-level fact table for the dashboard.
--          Every KPI card (total funded, outstanding, % repaid) and
--          the account-drilldown grid resolve against this table.
--
-- Joins  : cleaned_funded_accounts  LEFT JOIN  payment rollup per account
--          (LEFT JOIN is required so accounts disbursed too recently to
--          have any installments still appear with zeros.)
-- =============================================================

DROP TABLE IF EXISTS rpt_portfolio_summary;

CREATE TABLE rpt_portfolio_summary AS
WITH payments_per_account AS (
    SELECT
        account_id,
        -- total dollars actually collected for this account to date
        ROUND(SUM(actual_payment_made), 2) AS total_paid,
        -- number of scheduled installments observed so far (proxy for loan age)
        COUNT(*)                           AS months_active
    FROM cleaned_repayment_transactions
    GROUP BY account_id
)
SELECT
    f.account_id,
    f.business_name,
    f.industry,
    f.state,
    f.disbursement_cohort,
    f.funding_amount,
    f.total_repayable,
    f.net_funding,
    f.repayment_status,
    f.repayment_term_months,
    f.monthly_payment_amount,

    -- accounts with zero transactions (just-disbursed) still show up
    -- thanks to the LEFT JOIN; we coalesce to $0 / 0 months
    COALESCE(p.total_paid, 0)      AS total_paid,

    -- outstanding_balance is floored at 0 so overpayment (if it ever
    -- occurs in future data) doesn't produce negative balances on the
    -- dashboard. Uses SQLite's scalar MAX(a, b).
    MAX(
        ROUND(f.total_repayable - COALESCE(p.total_paid, 0), 2),
        0
    )                              AS outstanding_balance,

    -- % of contracted repayable that's been collected.
    -- Multiplied by 100.0 (not 100) to force float division in SQLite.
    -- Not capped at 100 intentionally: if an account shows > 100%, that's
    -- a data issue the QA layer should surface, not something to hide.
    ROUND(
        COALESCE(p.total_paid, 0) * 100.0 / NULLIF(f.total_repayable, 0),
        2
    )                              AS pct_repaid,

    COALESCE(p.months_active, 0)   AS months_active

FROM cleaned_funded_accounts    AS f
LEFT JOIN payments_per_account   AS p
  ON p.account_id = f.account_id;
