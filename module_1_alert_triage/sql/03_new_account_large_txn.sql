-- =====================================================
-- Rule Name: new_account_large_txn
-- Legal Basis: 특정금융거래정보의 보고 및 이용 등에 관한 법률 (CDD/EDD 강화 대상)
--              세부 조문번호는 docs/legal_basis.md 참조
-- Purpose: Flag transactions over 5,000,000 KRW from accounts
--          opened within the last 30 days.
-- Caveat: Short-tenure large transactions are a known mule-account
--         signal but also match legitimate onboarding flows
--         (e.g., salary transfers). Requires human review.
-- =====================================================

SELECT
    t.customer_id,
    c.onboarding_date,
    t.txn_date,
    CAST(JULIANDAY(t.txn_date) - JULIANDAY(c.onboarding_date) AS INTEGER)
        AS days_since_onboarding,
    t.amount,
    t.cash_yn,
    t.channel,
    'new_account_large_txn' AS rule_name
FROM transactions t
JOIN customers c ON c.customer_id = t.customer_id
WHERE JULIANDAY(t.txn_date) - JULIANDAY(c.onboarding_date) BETWEEN 0 AND 30
  AND t.amount > 5000000
ORDER BY t.amount DESC;
