# Module 1: Alert Triage Demo

특정금융거래정보의 보고 및 이용 등에 관한 법률(이하 "특금법")상 의심거래보고(STR)·고액현금거래보고(CTR) 및 금융정보분석원(FIU) 업무규정상 의심거래 유형을 rule-based 탐지 쿼리로 옮기고, 각 alert에 위험 점수를 부여해 검토 우선순위를 분류하는 학습 데모입니다.

가상 데이터(Faker 기반)로만 동작하며, 실거래 데이터는 일절 포함하지 않습니다.

## 탐지 룰 5개

| 룰명 | 법적 근거 (요지) | 탐지 로직 |
|---|---|---|
| `daily_cash_aggregation` (CTR) | 특금법 고액현금거래보고 | 동일 고객 동일 영업일 현금 거래 합계 1천만원 이상 |
| `structured_transactions` | 특금법 의심거래보고 (CTR 회피 의심 패턴) | 7일 rolling window 내 9백만~9백99만원 거래 3회 이상 |
| `new_account_large_txn` | CDD/EDD 강화 대상 식별 | 계좌 개설 30일 이내 5백만원 초과 거래 |
| `shared_device_multi_account` | 차명계좌·대포통장 리스크 | 동일 `device_id`를 공유하는 고유 계정 3개 이상 |
| `profile_mismatch` | KYC 행태 불일치 | 저소득 신고 고객의 월 거래액 5천만원 초과 |

각 룰의 법적 근거·FP 가능성·담당자 추가 확인 항목은 [`../docs/legal_basis.md`](../docs/legal_basis.md) 참조.

## 실행 방법

```bash
cd module_1_alert_triage
pip install -r ../requirements.txt

# 1) 가상 데이터 생성 (customers.csv, transactions.csv)
python data/generate_synthetic_data.py

# 2) 탐지 + 위험 점수 산출 노트북 실행
jupyter notebook notebooks/alert_prioritization.ipynb
```

노트북은 저장 시점에 이미 모든 셀이 실행된 상태이므로, Jupyter 없이 GitHub에서 그대로 결과를 확인할 수도 있습니다.

## 구조

```
module_1_alert_triage/
├── data/
│   └── generate_synthetic_data.py   # Faker 기반 가상 데이터 생성 (의도된 의심 시나리오 7건 포함)
├── sql/
│   ├── 01_daily_cash_aggregation.sql
│   ├── 02_structured_transactions.sql
│   ├── 03_new_account_large_txn.sql
│   ├── 04_shared_device_multi_account.sql
│   └── 05_profile_mismatch.sql
├── notebooks/
│   └── alert_prioritization.ipynb   # SQL 실행 → 점수 → 우선순위 분류
└── outputs/
    └── sample_alerts.csv            # 노트북의 최종 산출물 (커밋됨)
```

## 한계

1. 본 데모는 rule-based 접근만 다룹니다. 실무에서는 머신러닝 모델을 병행하여 false positive를 줄이는 것이 일반적입니다.
2. 가상 데이터는 7개의 의심 시나리오를 의도적으로 심어 두었기 때문에, hit 건수와 분포는 실제 거래 환경을 반영하지 않습니다.
3. 임계값(threshold)은 예시이며, 실무에서는 거래량 분포와 과거 STR 정확도를 기반으로 calibration이 필수입니다.
4. 위험 점수의 가중치는 heuristic이며 통계적으로 검증된 값이 아닙니다.
5. 최종 STR/CTR 보고 판단은 고객 컨텍스트 전반을 고려한 담당자 검토를 통해 이루어져야 합니다.
