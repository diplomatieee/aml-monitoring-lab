"""
Fetch regulatory notices from the RSS sources listed in config/sources.yaml.

각 소스를 순회하며 최근 항목을 수집합니다. 네트워크 실패는 해당 소스만
skip하고 나머지는 계속 진행합니다.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import feedparser
import yaml

logger = logging.getLogger(__name__)


@dataclass
class RawNotice:
    source_name: str
    title: str
    link: str
    published: str
    summary_raw: str
    language: str
    category: str
    # 수집 단계에서는 사전 분류가 없음 (summarizer가 채움)
    pre_classified: dict = field(default_factory=dict)


def load_sources(config_path: Path) -> list[dict]:
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("sources", [])


def fetch_one(source: dict, max_items: int = 10) -> list[RawNotice]:
    notices: list[RawNotice] = []
    try:
        parsed = feedparser.parse(source["url"])
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", source["name"], exc)
        return notices

    if parsed.bozo and not parsed.entries:
        logger.warning("Empty/malformed feed: %s", source["name"])
        return notices

    for entry in parsed.entries[:max_items]:
        notices.append(
            RawNotice(
                source_name=source["name"],
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published=entry.get("published", ""),
                summary_raw=entry.get("summary", ""),
                language=source.get("language", "en"),
                category=source.get("category", "other"),
            )
        )
    return notices


def fetch_all(config_path: Path, max_per_source: int = 10) -> list[RawNotice]:
    sources = load_sources(config_path)
    all_notices: list[RawNotice] = []
    for src in sources:
        logger.info("Fetching %s", src["name"])
        all_notices.extend(fetch_one(src, max_items=max_per_source))
    return all_notices


def save_raw_items(notices: list[RawNotice], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(n) for n in notices]
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    module_root = Path(__file__).parent.parent
    notices = fetch_all(module_root / "config" / "sources.yaml")
    save_raw_items(notices, module_root / "raw_items.json")
    print(f"Fetched {len(notices)} notices -> raw_items.json")
