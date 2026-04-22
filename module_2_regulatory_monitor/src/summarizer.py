"""
Claude API 기반 요약기. raw notice 리스트를 받아 한국어 요약·영향 영역·
긴급도·제안 조치·사람 검토 우선순위를 JSON으로 산출합니다.

API 키는 ANTHROPIC_API_KEY 환경변수에서 로드합니다.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5"
TEMPERATURE = 0.2
MAX_TOKENS = 1024


def load_system_prompt(prompt_path: Path) -> str:
    return prompt_path.read_text(encoding="utf-8")


def build_user_message(notice: dict) -> str:
    # 원문을 가공 없이 그대로 전달 (환각 방지)
    return (
        f"Source: {notice.get('source_name', '')}\n"
        f"Language: {notice.get('language', '')}\n"
        f"Title: {notice.get('title', '')}\n"
        f"Published: {notice.get('published', '')}\n"
        f"Link: {notice.get('link', '')}\n"
        f"---\n"
        f"{notice.get('summary_raw', '')}"
    )


def _parse_json_safely(text: str) -> dict | None:
    # 모델이 간혹 코드블록을 감싸므로 제거
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s", exc)
        return None


def summarize_one(
    client: Anthropic,
    system_prompt: str,
    notice: dict,
) -> dict:
    """
    Returns the notice dict with either `pre_classified` populated,
    or with is_ai_processed=False on parse failure.
    """
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": build_user_message(notice)}],
    )
    raw_text = message.content[0].text if message.content else ""
    parsed = _parse_json_safely(raw_text)

    enriched = dict(notice)
    if parsed is None:
        enriched["pre_classified"] = {}
        enriched["is_ai_processed"] = False
        enriched["raw_llm_output"] = raw_text
    else:
        enriched["pre_classified"] = parsed
        enriched["is_ai_processed"] = True
    return enriched


def summarize_all(notices: list[dict], prompt_path: Path) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Use --mock mode to run without a key."
        )

    client = Anthropic(api_key=api_key)
    system_prompt = load_system_prompt(prompt_path)

    results: list[dict] = []
    for i, notice in enumerate(notices, start=1):
        logger.info("Summarizing %d/%d: %s", i, len(notices), notice.get("title", "")[:60])
        try:
            results.append(summarize_one(client, system_prompt, notice))
        except Exception as exc:
            logger.warning("Summarizer error on item %d: %s", i, exc)
            fallback = dict(notice)
            fallback["pre_classified"] = {}
            fallback["is_ai_processed"] = False
            fallback["error"] = str(exc)
            results.append(fallback)
    return results


def save_classified(items: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
