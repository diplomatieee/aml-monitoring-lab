-- =====================================================
-- Rule Name: profile_mismatch
-- Legal Basis: 특정금융거래정보의 보고 및 이용 등에 관한 법률 (CDD/KYC 행태 불일치)
--              세부 조문번호는 docs/legal_basis.md 참조
-- Purpose: Flag low-income customers whose monthly transaction
--          volume exceeds 50,000,000 KRW.
-- Caveat: Self-reported income band may be outdated. This rule
--         surfaces candidates for re-KYC rather than confirming suspicion.
-- =====================================================

WITH monthly_totals AS (
    SELECT
        t.customer_id,
        strftime('%Y-%m', t.txn_date) AS year_month,
        SUM(t.amount)                 AS monthly_total,
        COUNT(*)                      AS txn_count
    FROM transactions t
    GROUP BY t.customer_id, strftime('%Y-%m', t.txn_date)
)
SELECT
    m.customer_id,
    c.income_band,
    c.occupation,
    m.year_month,
    m.monthly_total,
    m.txn_count,
    'profile_mismatch' AS rule_name
FROM monthly_totals m
JOIN customers c ON c.customer_id = m.customer_id
WHERE c.income_band = 'LOW'
  AND m.monthly_total > 50000000
ORDER BY m.monthly_total DESC;
