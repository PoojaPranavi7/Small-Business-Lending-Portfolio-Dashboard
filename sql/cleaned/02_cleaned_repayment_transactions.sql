-- =============================================================
-- CLEANED LAYER  |  cleaned_repayment_transactions
-- =============================================================
-- Source      : raw_repayment_transactions
-- Grain       : one row per (account_id, transaction_date)
-- Transforms  :
--   * Cast transaction_date to DATE.
--   * Coalesce null actual_payment_made -> 0 (missed pay = $0 received).
--   * Coalesce null payment_status      -> 'Unknown' for QA surfacing.
--   * Derive is_payment_gap flag (actual < scheduled).
--   * Recompute payment_variance against the coalesced actual so the
--     cleaned layer is internally consistent after null handling.
-- Notes       :
--   A coalesced NULL -> 0 actual_payment is, by design, flagged as a
--   payment gap. This is the correct business treatment: a missing
--   payment record is a payment that did not arrive.
-- =============================================================

DROP TABLE IF EXISTS cleaned_repayment_transactions;

CREATE TABLE cleaned_repayment_transactions AS
SELECT
    transaction_id,
    account_id,
    DATE(transaction_date)                                      AS transaction_date,

    scheduled_payment,

    COALESCE(actual_payment_made, 0)                            AS actual_payment_made,

    ROUND(
        COALESCE(actual_payment_made, 0) - scheduled_payment,
        2
    )                                                            AS payment_variance,

    COALESCE(payment_status, 'Unknown')                         AS payment_status,

    CASE
        WHEN COALESCE(actual_payment_made, 0) < scheduled_payment THEN 1
        ELSE 0
    END                                                          AS is_payment_gap
FROM raw_repayment_transactions;
