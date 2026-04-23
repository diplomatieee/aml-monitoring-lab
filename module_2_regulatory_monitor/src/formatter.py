"""
분류된 notice들을 Markdown 일일 리포트로 포맷팅.

정렬 규칙:
  1) MUST_REVIEW 먼저
  2) urgency HIGH > MEDIUM > LOW
  3) published 내림차순
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

URGENCY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "": 3}
PRIORITY_ORDER = {"MUST_REVIEW": 0, "STANDARD": 1, "": 2}

HEADER = """\
> ⚠ 이 문서는 프로토타입 샘플 출력입니다.
> 기관명은 실제일 수 있으나, 기사 제목·조치 내용·링크는 모두 가상 예시입니다.
> 실제 규제 공지와 혼동하지 마십시오.

"""


def sort_key(item: dict) -> tuple:
    pc = item.get("pre_classified") or {}
    return (
        PRIORITY_ORDER.get(pc.get("human_review_priority", ""), 2),
        URGENCY_ORDER.get(pc.get("urgency", ""), 3),
        # 최신 날짜를 위로: published 역순
        -1 * _parse_date_key(item.get("published", "")),
    )


def _parse_date_key(s: str) -> int:
    # YYYY-MM-DD 앞 10글자만 정수로 변환 (숫자가 아니면 0)
    digits = "".join(ch for ch in s[:10] if ch.isdigit())
    return int(digits) if digits else 0


def format_item(item: dict) -> str:
    pc = item.get("pre_classified") or {}
    urgency = pc.get("urgency", "UNSPECIFIED")
    impact = ", ".join(pc.get("impact_area", [])) or "-"
    priority = pc.get("human_review_priority", "STANDARD")
    priority_tag = "⚠ MUST_REVIEW" if priority == "MUST_REVIEW" else "STANDARD"

    lines = [
        f"## [{urgency} / {impact}] {item.get('title', '')}",
        "",
        f"- **출처**: {item.get('source_name', '')}",
        f"- **공지일**: {item.get('published', '')}",
        f"- **요약**: {pc.get('korean_summary', '(요약 없음)')}",
        f"- **영향 영역**: {impact}",
        f"- **제안 조치**: {pc.get('suggested_action', '-')}",
        f"- **원문**: [{item.get('link', '')}]({item.get('link', '')})",
        f"- **검토 우선순위**: {priority_tag}",
        "",
    ]
    return "\n".join(lines)


def render_report(items: list[dict], report_date: str) -> str:
    sorted_items = sorted(items, key=sort_key)
    parts = [HEADER, f"# 규제 모니터링 일일 리포트 ({report_date})\n"]
    parts.append(f"수집된 공지: {len(sorted_items)}건\n")
    for item in sorted_items:
        parts.append(format_item(item))
    return "\n".join(parts)


def save_report(markdown: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
