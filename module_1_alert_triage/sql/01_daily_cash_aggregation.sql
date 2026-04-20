-- =====================================================
-- Rule Name: daily_cash_aggregation
-- Legal Basis: 특정금융거래정보의 보고 및 이용 등에 관한 법률 (고액현금거래보고/CTR)
--              세부 조문번호는 docs/legal_basis.md 참조
-- Purpose: Flag customers whose same-day cash transactions aggregate
--          to 10,000,000 KRW or more.
-- Caveat: Threshold is illustrative. Production systems must
--         calibrate against actual transaction volume distribution.
-- =====================================================

WITH daily_cash AS (
    SELECT
        customer_id,
        txn_date,
        SUM(amount) AS daily_cash_total,
        COUNT(*)   AS txn_count
    FROM transactions
    WHERE cash_yn = 'Y'
    GROUP BY customer_id, txn_date
)
SELECT
    customer_id,
    txn_date,
    daily_cash_total,
    txn_count,
    'daily_cash_aggregation' AS rule_name
FROM daily_cash
WHERE daily_cash_total >= 10000000
ORDER BY daily_cash_total DESC;
