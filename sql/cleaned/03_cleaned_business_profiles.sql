-- =============================================================
-- CLEANED LAYER  |  cleaned_business_profiles
-- =============================================================
-- Source      : raw_business_profiles
-- Grain       : one row per account_id
-- Transforms  :
--   * Cast account_id to TEXT so the join key type matches
--     cleaned_funded_accounts and cleaned_repayment_transactions.
--   * Derive size_segment from employee_count:
--         <= 5         -> 'Micro'
--          6 -  20     -> 'Small'
--         21 -  50     -> 'Medium'
--   * Normalize repeat_borrower to 1/0 INTEGER for Tableau friendliness
--     (SQLite stores Python True/False as strings via to_sql).
-- =============================================================

DROP TABLE IF EXISTS cleaned_business_profiles;

CREATE TABLE cleaned_business_profiles AS
SELECT
    CAST(account_id AS TEXT)        AS account_id,
    employee_count,
    annual_revenue_band,
    years_in_business,

    CASE
        WHEN LOWER(CAST(repeat_borrower AS TEXT)) IN ('1', 'true', 't')  THEN 1
        WHEN LOWER(CAST(repeat_borrower AS TEXT)) IN ('0', 'false', 'f') THEN 0
        ELSE NULL
    END                             AS repeat_borrower,

    CASE
        WHEN employee_count <=  5 THEN 'Micro'
        WHEN employee_count <= 20 THEN 'Small'
        WHEN employee_count <= 50 THEN 'Medium'
        ELSE 'Unknown'
    END                             AS size_segment
FROM raw_business_profiles;
