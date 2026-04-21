-- =============================================================
-- REPORTING LAYER  |  rpt_cohort_performance
-- =============================================================
-- Grain  : one row per disbursement_cohort ('YYYY-MM')
-- Purpose: vintage / cohort analysis -- "Which disbursement months
--          are performing best or worst?" A recruiter-ready dashboard
--          must show vintage curves, which is the whole point of
--          the disbursement_cohort field we derived upstream.
--
-- Source : rpt_portfolio_summary -- same grain translation pattern
--          as the industry table.
-- =============================================================

DROP TABLE IF EXISTS rpt_cohort_performance;

CREATE TABLE rpt_cohort_performance AS
SELECT
    disbursement_cohort,

    COUNT(*)                                       AS total_accounts,

    -- dollars originated in the cohort (headline vintage number)
    ROUND(SUM(funding_amount),     2)              AS total_funded,

    -- average ticket size for the cohort; useful for spotting months
    -- where underwriting shifted toward larger/smaller loans
    ROUND(AVG(funding_amount),     2)              AS avg_funding_amount,

    -- cohort-level average repayment progress
    ROUND(AVG(pct_repaid),         2)              AS avg_pct_repaid,

    -- cohort-level default and late rates (% of accounts)
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
GROUP BY disbursement_cohort
ORDER BY disbursement_cohort;
