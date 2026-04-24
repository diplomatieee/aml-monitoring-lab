# AML Monitoring Lab

> 법학 전공자 관점에서 자금세탁방지(AML) 업무의 "법규 → 데이터 → AI 보조" 흐름을 직접 손으로 구현해본 학습 목적 프로젝트입니다.

## 3분 독해 요약

이 레포는 두 개의 독립 모듈로 구성됩니다.

**Module 1: Alert Triage Demo**
가상 거래 데이터를 기반으로 AML 의심거래 탐지 룰 5개를 SQL로 구현하고, 각 탐지 결과에 위험 점수를 부여해 검토 우선순위(High/Medium/Low)로 분류합니다. 각 룰에는 특정금융거래정보의 보고 및 이용 등에 관한 법률(이하 "특금법") 및 금융정보분석원 업무규정상 근거를 [`docs/legal_basis.md`](./docs/legal_basis.md)에 매핑했습니다.

**Module 2: Regulatory Monitor**
FATF, OFAC, 금융위원회, 금융정보분석원의 규제·제재 공지를 주기적으로 수집하여 한국어 요약, 영향 영역 분류(KYC/STR/CTR/Sanctions), 긴급도를 생성하는 소형 에이전트입니다. Claude API 기반이며, human-in-the-loop 원칙에 따라 최종 판단은 담당자에게 귀속됩니다. API 키 없이도 `--mock` 플래그로 동작합니다.

## 설계 원칙

- **Rule-based + Explainable**: 블랙박스 모델 대신 명시적 규칙. 법학도가 각 룰을 법적 근거로 설명 가능.
- **Human-in-the-loop**: AI는 담당자 판단을 대체하지 않고 인지 부하를 줄이는 도구로 한정.
- **Synthetic data only**: 실거래 데이터 미사용. 학습 목적 명시.
- **Source-traceable**: 모든 AI 요약에 원문 URL 병기. 환각 방지.

## 모듈별 실행 방법

각 모듈의 README를 참조하세요.

- [Module 1: Alert Triage Demo](./module_1_alert_triage/README.md)
- [Module 2: Regulatory Monitor](./module_2_regulatory_monitor/README.md)

## 주요 문서

- [법적 근거 매핑 (legal_basis.md)](./docs/legal_basis.md)
- [설계 판단 기록 (design_notes.md)](./docs/design_notes.md)

## 한계 및 주의사항

1. 본 프로젝트는 학습 목적 프로토타입이며 실무 시스템이 아닙니다.
2. Module 1의 탐지 룰은 가상 데이터 기반이며, false positive 검증을 수행하지 않았습니다. 실무에서는 실제 거래 데이터와의 calibration이 필수입니다.
3. Module 2의 AI 요약은 환각 가능성이 있으며, 원문 대조 없이 정책 결정에 사용할 수 없습니다.
4. 본 데모는 rule-based 접근만을 다루며, 실무에서는 머신러닝 모델과의 병행이 일반적입니다.
5. AML 관련 최종 법적 판단은 변호사·전문가·규제당국의 자문을 따라야 합니다.

## 작성자

이정은 / 충남대학교 법학전문대학원
