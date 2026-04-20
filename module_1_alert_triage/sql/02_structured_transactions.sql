-- =====================================================
-- Rule Name: structured_transactions
-- Legal Basis: 특정금융거래정보의 보고 및 이용 등에 관한 법률 (의심거래보고/STR)
--              세부 조문번호는 docs/legal_basis.md 참조
-- Purpose: Flag customers making 3+ transactions of 9.0M-9.99M KRW
--          within any 7-day rolling window (potential CTR-avoidance).
-- Caveat: The 9M-9.99M band is heuristic; real calibration should be
--         based on observed distribution around the 10M CTR threshold.
-- =====================================================

WITH sub_ctr_txns AS (
    SELECT
        txn_id,
        customer_id,
        txn_date,
        amount,
        JULIANDAY(txn_date) AS txn_julian
    FROM transactions
    WHERE amount BETWEEN 9000000 AND 9999999
),
rolling_counts AS (
    -- 각 거래를 기준점으로 7일 이내(해당 거래 포함) 동일 고객 sub-CTR 거래 수 집계
    SELECT
        a.customer_id,
        a.txn_date      AS window_start_date,
        COUNT(b.txn_id) AS txn_count,
        SUM(b.amount)   AS total_amount
    FROM sub_ctr_txns a
    JOIN sub_ctr_txns b
      ON a.customer_id = b.customer_id
     AND b.txn_julian BETWEEN a.txn_julian AND a.txn_julian + 6
    GROUP BY a.customer_id, a.txn_date
)
SELECT
    customer_id,
    window_start_date,
    txn_count,
    total_amount,
    'structured_transactions' AS rule_name
FROM rolling_counts
WHERE txn_count >= 3
ORDER BY total_amount DESC;
