"""Build the static AI framework site artifact for GitHub Pages."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ai_portfolio_framework.config import MANUAL_DIR, PUBLIC_DIR, SITE_DIR, display_path
from ai_portfolio_framework.research_monitor import build_research_monitor_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the AI framework GitHub Pages artifact.")
    parser.add_argument("--output-dir", type=Path, default=PUBLIC_DIR)
    parser.add_argument("--site-source-dir", type=Path, default=SITE_DIR)
    parser.add_argument("--data-date", default=None)
    parser.add_argument("--review-date", default=None)
    args = parser.parse_args()

    build_site(
        output_dir=args.output_dir,
        site_source_dir=args.site_source_dir,
        data_date=args.data_date,
        review_date=args.review_date,
    )


def build_site(
    *,
    output_dir: Path = PUBLIC_DIR,
    site_source_dir: Path = SITE_DIR,
    data_date: str | None = None,
    review_date: str | None = None,
) -> Path:
    output_dir = output_dir.resolve()
    site_source_dir = site_source_dir.resolve()
    data_date = data_date or latest_manual_data_date()
    review_date = review_date or today_los_angeles()

    if not site_source_dir.exists():
        raise SystemExit(f"Site source directory not found: {site_source_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(site_source_dir, output_dir)

    stamp_research_data(output_dir / "research-data.js", data_date, review_date)
    build_research_monitor_data(
        portfolio_data_path=output_dir / "portfolio-data.json",
        output_path=output_dir / "research-monitor-data.json",
        research_data_path=output_dir / "research-data.js",
        provenance_output_path=output_dir / "provenance-coverage.json",
        generated_output_path=None,
        generated_provenance_output_path=None,
    )
    write_refresh_manifest(output_dir, site_source_dir, data_date, review_date)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Built AI framework Pages artifact: {output_dir}")
    print(f"Data date: {data_date}")
    print(f"Review date: {review_date}")
    return output_dir


def today_los_angeles() -> str:
    return datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()


def latest_manual_data_date() -> str:
    candidates = []
    for filename in (
        "ai_framework_holdings.csv",
        "ai_framework_indicators.csv",
        "ai_framework_predictions.csv",
        "ai_framework_scenarios.csv",
    ):
        path = MANUAL_DIR / filename
        if not path.exists():
            continue
        frame = pd.read_csv(path, usecols=["as_of_date"])
        if not frame.empty:
            candidates.append(pd.to_datetime(frame["as_of_date"]).dt.date.max())
    if not candidates:
        return today_los_angeles()
    return max(candidates).isoformat()


def stamp_research_data(path: Path, data_date: str, review_date: str) -> None:
    text = path.read_text(encoding="utf-8")
    replacements = {
        "asOf": review_date,
        "dataDate": data_date,
        "reviewDate": review_date,
    }
    for field, value in replacements.items():
        text = re.sub(
            rf'{field}: "\d{{4}}-\d{{2}}-\d{{2}}"',
            f'{field}: "{value}"',
            text,
            count=1,
        )
    path.write_text(text, encoding="utf-8")


def write_refresh_manifest(
    output_dir: Path,
    site_source_dir: Path,
    data_date: str,
    review_date: str,
) -> None:
    portfolio_data_path = output_dir / "portfolio-data.json"
    portfolio_as_of = None
    if portfolio_data_path.exists():
        portfolio_as_of = json.loads(portfolio_data_path.read_text(encoding="utf-8")).get(
            "asOfDate"
        )
    manifest = {
        "built_at_utc": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "data_date": data_date,
        "review_date": review_date,
        "portfolio_as_of": portfolio_as_of,
        "site_source": display_path(site_source_dir),
    }
    (output_dir / "refresh.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
