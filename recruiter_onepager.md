# AML Monitoring Lab — 프로젝트 요약

> 법학 전공자가 자금세탁방지(AML) 업무의 "법규 → 데이터 → AI 보조" 흐름을 직접 구현한 학습 목적 프로젝트
>
> GitHub: https://github.com/diplomatieee/aml-monitoring-lab

---

## 프로젝트 목적

특정금융거래정보의 보고 및 이용 등에 관한 법률(이하 "특금법")과 금융정보분석원(FIU) 업무규정상 의심거래 유형을 SQL 탐지 룰로 옮기고, 규제 공지를 한국어로 요약·분류하는 소형 에이전트를 직접 구현했습니다. AML 실무에서 통용되는 사고방식 — 규정을 데이터화하고, AI를 담당자 보조 도구로 한정하는 구조 — 를 코드 단위에서 익히는 것이 목적입니다.

## 인터넷전문은행 AML 리스크 가정

- 비대면 계좌개설로 인한 KYC 정보의 한계
- 동일 device/IP를 통한 다계정 운용 (차명·대포통장 네트워크)
- 신규 계좌 개설 직후의 rapid in/out 거래
- 가입 시 신고 프로필(소득·직업) 대비 과다 거래
- 고액현금거래보고(CTR) 임계값 직하의 분할거래 (structuring)

## 구현한 Red Flag 탐지 룰 5개

| 룰명 | 법적 근거 (요지) | 탐지 로직 |
|---|---|---|
| `daily_cash_aggregation` (CTR) | 특금법 고액현금거래보고 의무 | 동일 고객 동일 영업일 현금 거래 합계 1천만원 이상 |
| `structured_transactions` | 특금법 의심거래보고 (CTR 회피 의심 패턴) | 7일 rolling window 내 9백만~9백99만원 거래 3회 이상 |
| `new_account_large_txn` | 특금법 CDD/EDD 강화 대상 식별 | 계좌 개설 30일 이내 5백만원 초과 거래 |
| `shared_device_multi_account` | FIU 업무규정상 차명거래 의심 패턴 | 동일 `device_id`를 공유하는 고유 계정 3개 이상 |
| `profile_mismatch` | 특금법 CDD의 지속적 모니터링 요건 | 저소득 신고 고객의 월 거래액 5천만원 초과 |

각 룰의 법적 근거·FP 가능성·담당자 추가 확인 항목은 [`docs/legal_basis.md`](./docs/legal_basis.md)에 상세 매핑.

## 사용한 도구와 역할 분담

- **SQL**: 법적 기준의 쿼리 번역 (룰 5종)
- **Python (pandas, sqlite3, matplotlib)**: 룰 통합 실행, 위험 점수 산출, 우선순위 분류
- **Claude API**: Module 2의 규제 공지 요약·분류 에이전트 (`--mock` 플래그로 API 키 없이 실행 가능)
- **human 담당자**: 모든 최종 STR/CTR 보고 판단

> AI는 담당자의 최종 판단을 대체하는 도구가 아니라, alert 검토 초안 작성·규제 모니터링 요약 등 담당자의 인지 부하를 줄이는 보조 도구로 한정했습니다.

## 샘플 출력 예시 (`module_1_alert_triage/outputs/sample_alerts.csv` 상위 3건)

| customer_id | 트리거된 룰 | 위험 점수 | 우선순위 |
|---|---|---|---|
| C0045 | new_account_large_txn, shared_device_multi_account, structured_transactions | 60 | High |
| C0030 | new_account_large_txn, profile_mismatch, shared_device_multi_account | 55 | Medium |
| C0002 | shared_device_multi_account, structured_transactions | 40 | Medium |

## 본 역량과 AML 직무의 연결

1. **규정 해석력**: 로스쿨에서 훈련한 법규 포섭·해석 능력을 [`docs/legal_basis.md`](./docs/legal_basis.md)에서 특금법 및 FIU 업무규정 매핑으로 구체화.
2. **무결성 운영 경험**: 수험생 300명 대상 8개월간 운영 오류 0건. AML의 STR·CTR 보고에서 요구되는 무결성 감각과 같은 근육.
3. **데이터/AI 실행력**: SQL로 탐지 룰, Python으로 위험 점수, Claude API로 모니터링 에이전트를 직접 구현.
4. **설계 원칙의 일관성**: 모든 모듈에서 human-in-the-loop 고수. AI 시대에도 책임이 사람에게 귀속된다는 법학적 관점을 코드로 구현.

---
학습 목적 프로젝트 / 가상 데이터 사용 / 실무 시스템 아님
이정은 | 충남대학교 법학전문대학원
