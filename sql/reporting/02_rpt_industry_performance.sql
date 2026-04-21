-- =============================================================
-- REPORTING LAYER  |  rpt_industry_performance
-- =============================================================
-- Grain  : one row per industry
-- Purpose: feeds the "Industry Risk" view of the dashboard. Answers
--          "Which industries have the highest default and late rates?"
--
-- Source : rpt_portfolio_summary  (so industry totals reconcile
--          exactly against the account-level KPI cards).
-- =============================================================

DROP TABLE IF EXISTS rpt_industry_performance;

CREATE TABLE rpt_industry_performance AS
SELECT
    industry,

    COUNT(*)                                       AS total_accounts,

    -- dollars disbursed and dollars contracted to be repaid
    ROUND(SUM(funding_amount),  2)                 AS total_funded,
    ROUND(SUM(total_repayable), 2)                 AS total_repayable,
    ROUND(SUM(total_paid),      2)                 AS total_paid,

    -- average % repaid across accounts in the industry (unweighted;
    -- a weighted version could use SUM(total_paid)/SUM(total_repayable)).
    ROUND(AVG(pct_repaid), 2)                      AS avg_pct_repaid,

    -- raw status counts that Tableau can also stack into a bar chart
    SUM(CASE WHEN repayment_status = 'Defaulted' THEN 1 ELSE 0 END) AS default_count,
    SUM(CASE WHEN repayment_status = 'Late'      THEN 1 ELSE 0 END) AS late_count,
    SUM(CASE WHEN repayment_status = 'On Track'  THEN 1 ELSE 0 END) AS on_track_count,
    SUM(CASE WHEN repayment_status = 'Paid Off'  THEN 1 ELSE 0 END) AS paid_off_count,

    -- rates as % of accounts; * 100.0 forces float division in SQLite
    ROUND(
        SUM(CASE WHEN repayment_status = 'Defaulted' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                              AS default_rate,

    ROUND(
        SUM(CASE WHEN repayment_status = 'Late' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                              AS late_rate

FROM rpt_portfolio_summary
GROUP BY industry
ORDER BY default_rate DESC, industry;
