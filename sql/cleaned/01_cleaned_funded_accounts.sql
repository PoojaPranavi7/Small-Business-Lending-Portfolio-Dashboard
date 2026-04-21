-- =============================================================
-- CLEANED LAYER  |  cleaned_funded_accounts
-- =============================================================
-- Source      : raw_funded_accounts
-- Grain       : one row per account_id
-- Transforms  :
--   * Cast disbursement_date to DATE.
--   * Standardize industry (canonical title-case mapping).
--   * Standardize state code (uppercase, trimmed -- USPS format).
--   * Drop rows with null or zero funding_amount (invalid loans).
--   * Compute total_repayable  = funding_amount * factor_rate.
--   * Compute net_funding       = funding_amount - origination_fee.
--   * Derive disbursement_cohort as 'YYYY-MM' for cohort analysis.
-- =============================================================

DROP TABLE IF EXISTS cleaned_funded_accounts;

CREATE TABLE cleaned_funded_accounts AS
SELECT
    account_id,
    TRIM(business_name)                                  AS business_name,

    CASE LOWER(TRIM(industry))
        WHEN 'retail'           THEN 'Retail'
        WHEN 'food & beverage'  THEN 'Food & Beverage'
        WHEN 'healthcare'       THEN 'Healthcare'
        WHEN 'e-commerce'       THEN 'E-Commerce'
        WHEN 'construction'     THEN 'Construction'
        WHEN 'logistics'        THEN 'Logistics'
        ELSE TRIM(industry)
    END                                                  AS industry,

    UPPER(TRIM(state))                                   AS state,

    DATE(disbursement_date)                              AS disbursement_date,

    funding_amount,
    repayment_term_months,
    factor_rate,
    origination_fee,
    repayment_status,
    monthly_payment_amount,

    ROUND(funding_amount * factor_rate,      2)          AS total_repayable,
    ROUND(funding_amount - origination_fee,  2)          AS net_funding,
    STRFTIME('%Y-%m', DATE(disbursement_date))           AS disbursement_cohort
FROM raw_funded_accounts
WHERE funding_amount IS NOT NULL
  AND funding_amount > 0;
