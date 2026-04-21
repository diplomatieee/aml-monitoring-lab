-- =====================================================
-- Rule Name: shared_device_multi_account
-- Legal Basis: 특정금융거래정보의 보고 및 이용 등에 관한 법률 (차명계좌·대포통장 리스크)
--              금융정보분석원 업무규정상 의심거래 유형 참조
--              세부 조문번호는 docs/legal_basis.md 참조
-- Purpose: Flag device_ids shared by 3 or more distinct customers
--          (potential mule-account network signal).
-- Caveat: Family-shared devices and public kiosks produce false positives.
-- =====================================================

SELECT
    device_id,
    COUNT(DISTINCT customer_id)          AS shared_customer_count,
    GROUP_CONCAT(DISTINCT customer_id)   AS customer_list,
    'shared_device_multi_account'        AS rule_name
FROM transactions
WHERE device_id IS NOT NULL
  AND device_id <> ''
GROUP BY device_id
HAVING COUNT(DISTINCT customer_id) >= 3
ORDER BY shared_customer_count DESC;
