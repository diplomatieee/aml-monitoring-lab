# Module 2: Regulatory Monitor

FATF, OFAC, 금융위원회, 금융정보분석원(FIU)의 규제·제재 공지를 일 배치로 수집해 한국어 요약, 영향 영역(KYC/STR/CTR/Sanctions 등), 긴급도, 제안 조치를 생성하는 소형 에이전트입니다. 담당자가 "30초 스캔"으로 당일 처리 대상을 식별할 수 있도록 산출물을 Markdown 일일 리포트로 고정합니다.

설계 원칙은 [`../docs/design_notes.md`](../docs/design_notes.md)를 참조하세요.

## 아키텍처

```
[RSS/공지 소스] ──────┐
                      ├──> fetcher.py ──> raw_items.json
[sample_inputs] ──────┘                        ↓
                                        summarizer.py (Claude API)
                                                ↓
                                        classified_items.json
                                                ↓
                                        formatter.py
                                                ↓
                                        daily_report.md (human reviews)
```

## 설계 원칙

- **Human-in-the-loop**: AI는 정렬·요약·태깅만 수행하고 최종 보고 판단은 담당자 귀속.
- **Source-traceable**: 모든 항목에 원문 링크를 병기하여 환각 여부 즉시 확인 가능.
- **Domain-bounded**: prompts/summarizer_prompt.md에 번역 용어·에스컬레이션 규칙을 고정해 일관성 확보.
- **Low-dependency**: feedparser + anthropic SDK 외 추가 프레임워크 미사용. 디버깅 단순성 우선.

## 실행 방법

```bash
cd module_2_regulatory_monitor
pip install -r ../requirements.txt
```

### Live mode (네트워크 + Claude API 키 필요)

```bash
cp ../.env.example ../.env
# .env 파일에 ANTHROPIC_API_KEY 값을 입력
python src/main.py
```

### Mock mode (네트워크·API 키 불필요, 데모용)

```bash
python src/main.py --mock --report-date 2026-04-24
```

`sample_inputs/sample_notices.json`의 `pre_classified` 필드를 그대로 formatter에 넘겨 리포트를 재생성합니다. `sample_outputs/2026-04-24_daily_report.md`가 이 명령으로 만들어진 산출물입니다.

## 구조

```
module_2_regulatory_monitor/
├── src/
│   ├── fetcher.py        # RSS/공지 수집 (feedparser)
│   ├── summarizer.py     # Claude API 호출 및 JSON 파싱
│   ├── formatter.py      # Markdown 리포트 렌더링
│   └── main.py           # 엔트리 포인트 (--mock 지원)
├── config/
│   └── sources.yaml      # 수집 대상 RSS URL
├── prompts/
│   └── summarizer_prompt.md  # 시스템 프롬프트 (번역 용어·에스컬레이션 규칙)
├── sample_inputs/
│   └── sample_notices.json   # mock mode 입력 (가상 공지 6건)
└── sample_outputs/
    └── 2026-04-24_daily_report.md  # mock mode 산출물 예시
```

## 한계

1. RSS URL은 예시입니다. 실제 기관의 RSS 경로는 변경될 수 있으며, 운영 전 확인이 필요합니다.
2. AI 요약은 환각 가능성이 있어, 원문 대조 없이 정책 결정에 사용할 수 없습니다. 본 모듈은 담당자 검토 전 사전 정리 도구입니다.
3. mock mode는 데모 목적입니다. `pre_classified` 필드는 사전에 사람이 검수한 가상 데이터이며, 실제 AI 호출을 대체하지 않습니다.
4. `sample_outputs/` 리포트의 기사 제목·조치 내용·링크는 모두 가상 예시입니다.
