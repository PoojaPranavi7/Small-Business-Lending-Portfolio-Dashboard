-- =============================================================
-- QA LAYER  |  qa_validation_results
-- =============================================================
-- Purpose  : Pre-dashboard data-quality gate. Every check below
--            produces exactly one row describing what was audited,
--            how many records tripped the rule, and a PASS / FAIL
--            verdict.
--
-- Contract : A check is PASS only when records_flagged = 0.
--            Results persist in the `qa_validation_results` table
--            so the dashboard (or a CI job) can surface them.
--
-- Convention:
--   * Critical checks  -> any failure should block publish.
--   * Warning checks   -> failure is expected in certain conditions
--                         (e.g., just-disbursed accounts with no
--                         installments yet). See `notes` column.
-- =============================================================

DROP TABLE IF EXISTS qa_validation_results;

CREATE TABLE qa_validation_results (
    check_id         INTEGER,
    check_name       TEXT,
    severity         TEXT,
    records_flagged  INTEGER,
    pass_or_fail     TEXT,
    notes            TEXT
);

INSERT INTO qa_validation_results (check_id, check_name, severity, records_flagged, pass_or_fail, notes)

-- -------------------------------------------------------------
-- 1. Null primary key on the account fact table.
--    Critical: every account must have an ID. A null here means
--    the upstream load corrupted the key and all account-level
--    joins will silently drop records.
-- -------------------------------------------------------------
SELECT
    1                                                       AS check_id,
    'null_account_id_in_portfolio_summary'                  AS check_name,
    'CRITICAL'                                              AS severity,
    COUNT(*)                                                AS records_flagged,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END      AS pass_or_fail,
    'Primary key must never be NULL. Blocks publish.'       AS notes
FROM rpt_portfolio_summary
WHERE account_id IS NULL

UNION ALL

-- -------------------------------------------------------------
-- 2. Negative outstanding balance.
--    Critical: a negative balance means we collected more than
--    we were owed -- a refund liability or a double-posting bug.
-- -------------------------------------------------------------
SELECT
    2,
    'negative_outstanding_balance',
    'CRITICAL',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Outstanding balance should never be < 0. Indicates refund or double-posting.'
FROM rpt_portfolio_summary
WHERE outstanding_balance < 0

UNION ALL

-- -------------------------------------------------------------
-- 3. Orphan accounts -- present in the account table but with
--    zero rows in the transaction ledger.
--    Warning: expected for accounts disbursed too recently to have
--    a first installment. Investigate anything beyond the most
--    recent month.
-- -------------------------------------------------------------
SELECT
    3,
    'orphan_accounts_no_transactions',
    'WARNING',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Accounts with zero ledger rows. Expected for just-disbursed loans; review older orphans.'
FROM rpt_portfolio_summary p
WHERE NOT EXISTS (
    SELECT 1
    FROM cleaned_repayment_transactions t
    WHERE t.account_id = p.account_id
)

UNION ALL

-- -------------------------------------------------------------
-- 4. Overpayment above a 5% tolerance.
--    Critical: total_paid > total_repayable * 1.05 means the
--    ledger is reporting collections materially above contract.
--    Likely causes: duplicate transaction rows, double-counted
--    fees, or seed/test contamination.
-- -------------------------------------------------------------
SELECT
    4,
    'overpayment_above_5pct_of_contract',
    'CRITICAL',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'total_paid exceeds total_repayable by more than 5%. Likely duplicate postings.'
FROM rpt_portfolio_summary
WHERE total_paid > total_repayable * 1.05

UNION ALL

-- -------------------------------------------------------------
-- 5. Status / balance mismatch.
--    Critical: accounts flagged "Paid Off" should have a trivial
--    outstanding balance. Anything > $100 means either the status
--    field is stale or the ledger is incomplete -- a classic
--    reconciliation issue in real lending books.
-- -------------------------------------------------------------
SELECT
    5,
    'paid_off_status_with_balance_over_100',
    'CRITICAL',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Status = Paid Off but outstanding_balance > $100. Reconcile status vs. ledger.'
FROM rpt_portfolio_summary
WHERE repayment_status = 'Paid Off'
  AND outstanding_balance > 100

UNION ALL

-- -------------------------------------------------------------
-- 6. Unknown payment status.
--    Warning: every NULL payment_status in raw was coalesced to
--    'Unknown' in the cleaned layer. A large count points to an
--    upstream ingestion issue with the payments feed.
-- -------------------------------------------------------------
SELECT
    6,
    'unknown_payment_status_in_ledger',
    'WARNING',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Null payment_status coalesced to Unknown in cleaned layer. Investigate ingestion feed.'
FROM cleaned_repayment_transactions
WHERE payment_status = 'Unknown'

;

-- -------------------------------------------------------------
-- Final ordering: stable by check_id so downstream consumers
-- (Tableau, CI reports) see the checks in a predictable sequence.
-- -------------------------------------------------------------
-- (The ORDER BY belongs on the SELECT, not on INSERT. A view on
-- top gives us a stable, queryable summary.)
DROP VIEW IF EXISTS qa_validation_summary;

CREATE VIEW qa_validation_summary AS
SELECT
    check_id,
    check_name,
    severity,
    records_flagged,
    pass_or_fail,
    notes
FROM qa_validation_results
ORDER BY check_id;
