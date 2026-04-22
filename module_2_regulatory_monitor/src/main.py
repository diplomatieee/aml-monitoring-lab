"""
Entry point for the regulatory monitor.

Live mode:
    python src/main.py
        -> fetch RSS -> Claude summarizer -> formatter -> daily_report.md

Mock mode (no API key / no network required):
    python src/main.py --mock
        -> read sample_inputs/sample_notices.json (with pre_classified) -> formatter
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from dataclasses import asdict

from fetcher import fetch_all, save_raw_items
from summarizer import save_classified, summarize_all
from formatter import render_report, save_report


MODULE_ROOT = Path(__file__).parent.parent


def run_mock() -> list[dict]:
    sample_path = MODULE_ROOT / "sample_inputs" / "sample_notices.json"
    with sample_path.open(encoding="utf-8") as f:
        items = json.load(f)
    # Mock mode에서는 summarizer를 건너뛰고 pre_classified 필드를 그대로 사용
    return items


def run_live() -> list[dict]:
    load_dotenv(dotenv_path=MODULE_ROOT.parent / ".env")
    notices = fetch_all(MODULE_ROOT / "config" / "sources.yaml")
    save_raw_items(notices, MODULE_ROOT / "raw_items.json")
    notice_dicts = [asdict(n) for n in notices]
    classified = summarize_all(
        notice_dicts,
        MODULE_ROOT / "prompts" / "summarizer_prompt.md",
    )
    save_classified(classified, MODULE_ROOT / "classified_items.json")
    return classified


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Regulatory monitor daily run")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use sample_inputs/sample_notices.json and skip live RSS + Claude API",
    )
    parser.add_argument(
        "--report-date",
        default=date.today().isoformat(),
        help="Date string used in the report title and output filename (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    if args.mock:
        logging.info("Running in MOCK mode")
        items = run_mock()
    else:
        logging.info("Running in LIVE mode")
        items = run_live()

    report_md = render_report(items, report_date=args.report_date)
    out_path = (
        MODULE_ROOT
        / "sample_outputs"
        / f"{args.report_date}_daily_report.md"
    )
    save_report(report_md, out_path)
    print(f"Wrote report -> {out_path}")


if __name__ == "__main__":
    main()
