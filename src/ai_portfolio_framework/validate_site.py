"""Validation checks for the AI framework static site artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ai_portfolio_framework.config import MANUAL_DIR, SITE_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the static AI framework site.")
    parser.add_argument("--site-dir", type=Path, default=SITE_DIR)
    parser.add_argument("--require-portfolio", action="store_true")
    args = parser.parse_args()

    errors = validate_site(args.site_dir, require_portfolio=args.require_portfolio)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"Site validation passed: {args.site_dir.resolve()}")


def validate_site(site_dir: Path, *, require_portfolio: bool = False) -> list[str]:
    errors: list[str] = []
    site_dir = site_dir.resolve()
    for filename in ("index.html", "styles.css", "app.js", "research-data.js"):
        if not (site_dir / filename).exists():
            errors.append(f"missing required site file: {filename}")

    research_data_path = site_dir / "research-data.js"
    if research_data_path.exists():
        research_text = research_data_path.read_text(encoding="utf-8")
        if "window.AI_FRAMEWORK_DATA" not in research_text:
            errors.append("research-data.js does not define window.AI_FRAMEWORK_DATA")
        if "trusted execution" not in research_text.lower():
            errors.append("research-data.js does not include the trusted-execution thesis")

    errors.extend(validate_manual_holdings())

    portfolio_path = site_dir / "portfolio-data.json"
    if require_portfolio or portfolio_path.exists():
        errors.extend(validate_portfolio_json(site_dir, portfolio_path))

    monitor_path = site_dir / "research-monitor-data.json"
    if require_portfolio or monitor_path.exists():
        errors.extend(validate_research_monitor_json(site_dir, monitor_path))
    return errors


def validate_manual_holdings() -> list[str]:
    path = MANUAL_DIR / "ai_framework_holdings.csv"
    if not path.exists():
        return [f"missing manual holdings file: {path}"]

    errors: list[str] = []
    holdings = pd.read_csv(path)
    required = {"ticker", "holding_name", "target_weight"}
    missing = required - set(holdings.columns)
    if missing:
        errors.append(f"manual holdings missing columns: {sorted(missing)}")
        return errors

    if len(holdings) != 14:
        errors.append(f"manual holdings should have 14 rows, got {len(holdings)}")
    if holdings["ticker"].duplicated().any():
        errors.append("manual holdings contain duplicate tickers")
    if "CASH" not in set(holdings["ticker"]):
        errors.append("manual holdings must include CASH")
    weight_total = float(pd.to_numeric(holdings["target_weight"]).sum())
    if abs(weight_total - 100.0) > 0.0001:
        errors.append(f"manual holding weights must sum to 100, got {weight_total}")
    return errors


def validate_portfolio_json(site_dir: Path, portfolio_path: Path) -> list[str]:
    if not portfolio_path.exists():
        return [f"portfolio-data.json is required but missing in {site_dir}"]

    errors: list[str] = []
    try:
        portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"portfolio-data.json is invalid JSON: {exc}"]

    required_fields = (
        "asOfDate",
        "baseCurrency",
        "initialCapitalUsd",
        "summary",
        "holdings",
        "history",
    )
    for field in required_fields:
        if field not in portfolio:
            errors.append(f"portfolio-data.json missing required field: {field}")

    if portfolio.get("baseCurrency") != "USD":
        errors.append(f"portfolio baseCurrency must be USD, got {portfolio.get('baseCurrency')}")
    if float(portfolio.get("initialCapitalUsd", 0)) != 1000.0:
        errors.append(
            "portfolio initialCapitalUsd must be 1000, "
            f"got {portfolio.get('initialCapitalUsd')}"
        )

    summary = portfolio.get("summary", {})
    for field in ("total_value_usd", "pnl_usd", "return_pct", "daily_pnl_usd", "daily_return_pct"):
        if not isinstance(summary.get(field), int | float):
            errors.append(f"portfolio summary {field} must be numeric")

    holdings = portfolio.get("holdings", [])
    if len(holdings) != 14:
        errors.append(f"portfolio holdings must have 14 rows, got {len(holdings)}")
    else:
        tickers = {holding.get("ticker") for holding in holdings}
        if "CASH" not in tickers:
            errors.append("portfolio holdings must include CASH")
        total_weight = sum(float(holding.get("target_weight", 0)) for holding in holdings)
        if abs(total_weight - 100.0) > 0.0001:
            errors.append(f"portfolio target weights must sum to 100, got {total_weight}")

    if not portfolio.get("history"):
        errors.append("portfolio history must have at least one row")

    for label, plot_path in portfolio.get("plots", {}).items():
        clean_path = str(plot_path).removeprefix("./")
        if not (site_dir / clean_path).exists():
            errors.append(f"portfolio plot {label} is missing: {plot_path}")
    return errors


def validate_research_monitor_json(site_dir: Path, monitor_path: Path) -> list[str]:
    if not monitor_path.exists():
        return [f"research-monitor-data.json is required but missing in {site_dir}"]

    errors: list[str] = []
    try:
        monitor = json.loads(monitor_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"research-monitor-data.json is invalid JSON: {exc}"]

    for field in (
        "schemaVersion",
        "summary",
        "alerts",
        "reviewQueue",
        "sourceHealth",
        "holdings",
    ):
        if field not in monitor:
            errors.append(f"research-monitor-data.json missing required field: {field}")
    if monitor.get("schemaVersion") != 1:
        errors.append(
            f"research monitor schemaVersion must be 1, got {monitor.get('schemaVersion')}"
        )
    holding_count = len(monitor.get("holdings", []))
    if holding_count != 14:
        errors.append(f"research monitor holdings must have 14 rows, got {holding_count}")
    if not monitor.get("sourceHealth"):
        errors.append("research monitor sourceHealth must not be empty")

    valid_levels = {"green", "blue", "gray", "yellow", "red"}
    valid_source_statuses = {"healthy", "manual_expected", "planned", "stale", "broken"}
    highest = monitor.get("summary", {}).get("highest_alert")
    if highest not in valid_levels:
        errors.append(f"research monitor highest_alert has invalid level: {highest}")
    for alert in monitor.get("alerts", []):
        if alert.get("level") not in valid_levels:
            errors.append(f"research monitor alert has invalid level: {alert}")
    for source in monitor.get("sourceHealth", []):
        if source.get("status") not in valid_source_statuses:
            errors.append(f"research monitor source has invalid status: {source}")
    return errors


if __name__ == "__main__":
    main()
