"""Deterministic research-monitor layer for the AI portfolio framework."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from ai_portfolio_framework.config import (
    CONFIG_DIR,
    GENERATED_DATA_DIR,
    SITE_DIR,
    ensure_directories,
)

HOLDINGS_CONFIG_PATH = CONFIG_DIR / "holdings.yml"
METRICS_CATALOG_PATH = CONFIG_DIR / "metrics_catalog.yml"
ALERT_RULES_PATH = CONFIG_DIR / "alert_rules.yml"
SOURCES_CONFIG_PATH = CONFIG_DIR / "sources.yml"
DECISION_LOG_PATH = GENERATED_DATA_DIR.parent / "decision_log.yml"
SITE_PORTFOLIO_DATA_PATH = SITE_DIR / "portfolio-data.json"
SITE_MONITOR_DATA_PATH = SITE_DIR / "research-monitor-data.json"
GENERATED_MONITOR_DATA_PATH = GENERATED_DATA_DIR / "dashboard_data.json"

LEVEL_RANK = {"green": 0, "blue": 1, "gray": 1, "yellow": 2, "red": 3}
SOURCE_STATUS_ORDER = ("healthy", "manual_expected", "planned", "stale", "broken")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic research monitor data.")
    parser.add_argument("--portfolio-data", type=Path, default=SITE_PORTFOLIO_DATA_PATH)
    parser.add_argument("--output", type=Path, default=SITE_MONITOR_DATA_PATH)
    parser.add_argument("--generated-output", type=Path, default=GENERATED_MONITOR_DATA_PATH)
    args = parser.parse_args()

    payload = build_research_monitor_data(
        portfolio_data_path=args.portfolio_data,
        output_path=args.output,
        generated_output_path=args.generated_output,
    )
    print(
        "Built research monitor: "
        f"{args.output.resolve()} alerts={len(payload['alerts'])} "
        f"highest={payload['summary']['highest_alert']}"
    )


def build_research_monitor_data(
    *,
    holdings_config_path: Path = HOLDINGS_CONFIG_PATH,
    metrics_catalog_path: Path = METRICS_CATALOG_PATH,
    alert_rules_path: Path = ALERT_RULES_PATH,
    sources_config_path: Path = SOURCES_CONFIG_PATH,
    decision_log_path: Path = DECISION_LOG_PATH,
    portfolio_data_path: Path = SITE_PORTFOLIO_DATA_PATH,
    output_path: Path = SITE_MONITOR_DATA_PATH,
    generated_output_path: Path | None = GENERATED_MONITOR_DATA_PATH,
    portfolio_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and persist the static JSON used by the research-monitor UI."""

    ensure_directories()
    holdings_config = load_yaml(holdings_config_path)
    metrics_catalog = load_yaml(metrics_catalog_path)
    alert_rules = load_yaml(alert_rules_path)
    sources_config = load_yaml(sources_config_path)
    decision_log = load_yaml_list(decision_log_path)
    portfolio_data = portfolio_data or load_json(portfolio_data_path)

    as_of_date = date.fromisoformat(portfolio_data.get("asOfDate", today_utc()))
    summary = portfolio_data.get("summary", {})
    portfolio_total = float(summary.get("total_value_usd") or 0)
    portfolio_rows = {row["ticker"]: row for row in portfolio_data.get("holdings", [])}
    rules_by_id = {rule["id"]: rule for rule in alert_rules.get("rules", [])}

    alerts: list[dict[str, Any]] = []
    monitored_holdings = []
    for holding in holdings_config.get("holdings", []):
        ticker = str(holding["ticker"])
        row = portfolio_rows.get(ticker)
        catalog_entry = metrics_catalog.get(ticker, {})
        holding_alerts = evaluate_holding_alerts(
            holding=holding,
            portfolio_row=row,
            portfolio_total=portfolio_total,
            as_of_date=as_of_date,
            rules_by_id=rules_by_id,
        )
        alerts.extend(holding_alerts)
        metrics = [normalize_metric(metric) for metric in catalog_entry.get("metrics", [])]
        monitored_holdings.append(
            {
                "ticker": ticker,
                "name": holding["name"],
                "bucket": holding["bucket"],
                "layers": holding["layers"],
                "target_weight": normalize_weight(holding["target_weight"]),
                "current_weight": current_weight(row, portfolio_total),
                "weight_drift_pct_points": weight_drift(holding, row, portfolio_total),
                "status": highest_level(holding_alerts),
                "core_question": catalog_entry.get("core_question", ""),
                "top_metrics": metrics[:4],
                "watch_rule": catalog_entry.get("watch_rule", ""),
                "falsifier": catalog_entry.get("falsifier", []),
                "next_action": normalize_next_action(ticker, catalog_entry.get("next_action")),
                "alert_count": len(holding_alerts),
            }
        )

    portfolio_alert = evaluate_portfolio_drawdown(
        portfolio_data.get("history", []),
        as_of_date=as_of_date,
        rule=rules_by_id.get("portfolio_drawdown_watch", {}),
    )
    if portfolio_alert:
        alerts.append(portfolio_alert)

    source_health = build_source_health(
        sources_config=sources_config,
        portfolio_data=portfolio_data,
        as_of_date=as_of_date,
        stale_days=int(rules_by_id.get("stale_price", {}).get("threshold_days", 3)),
    )
    review_queue = build_review_queue(monitored_holdings, alerts)
    source_status_counts = count_source_statuses(source_health)
    source_issues = source_status_counts["stale"] + source_status_counts["broken"]
    highest_rule_alert = highest_level(alerts)
    payload = {
        "schemaVersion": 1,
        "generatedAtUtc": utc_iso(),
        "asOfDate": as_of_date.isoformat(),
        "principles": {
            "llm_phase": "disabled",
            "llm_role": "future draft_insight only; never portfolio_action",
            "red_alert_policy": alert_rules.get("falsifier_policy", {}).get("message", ""),
        },
        "summary": {
            "highest_alert": highest_rule_alert,
            "rule_alert": highest_rule_alert,
            "framework_bottleneck": "Trust / write-permission evidence",
            "alert_counts": count_levels(alerts),
            "review_queue_count": len(review_queue),
            "source_count": len(source_health),
            "source_issues": source_issues,
            "source_status_counts": source_status_counts,
        },
        "alerts": alerts,
        "reviewQueue": review_queue,
        "sourceHealth": source_health,
        "holdings": monitored_holdings,
        "metricCatalog": compact_metric_catalog(metrics_catalog),
        "decisionLog": decision_log[-10:],
    }
    write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    return payload


def evaluate_holding_alerts(
    *,
    holding: dict[str, Any],
    portfolio_row: dict[str, Any] | None,
    portfolio_total: float,
    as_of_date: date,
    rules_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    ticker = str(holding["ticker"])
    if ticker == "CASH":
        return []
    if not portfolio_row:
        return [
            make_alert(
                as_of_date=as_of_date,
                ticker=ticker,
                rule=rules_by_id["missing_price"],
                message=f"{ticker}: {rules_by_id['missing_price']['message']}",
            )
        ]

    alerts = []
    stale_rule = rules_by_id.get("stale_price", {})
    price_date = date.fromisoformat(str(portfolio_row["price_date"]))
    price_age_days = (as_of_date - price_date).days
    if price_age_days > int(stale_rule.get("threshold_days", 3)):
        alerts.append(
            make_alert(
                as_of_date=as_of_date,
                ticker=ticker,
                rule=stale_rule,
                message=f"{ticker}: price is {price_age_days} days old.",
                metadata={"price_date": price_date.isoformat(), "price_age_days": price_age_days},
            )
        )

    drift_rule = rules_by_id.get("weight_drift", {})
    drift = weight_drift(holding, portfolio_row, portfolio_total)
    target_weight = normalize_weight(holding["target_weight"])
    relative_drift = pct(abs(drift), target_weight)
    if relative_drift > float(drift_rule.get("threshold_relative_pct", 15.0)):
        alerts.append(
            make_alert(
                as_of_date=as_of_date,
                ticker=ticker,
                rule=drift_rule,
                message=(
                    f"{ticker}: weight drift is {drift:.2f} percentage points "
                    f"({relative_drift:.1f}% relative to target)."
                ),
                metadata={
                    "weight_drift_pct_points": round(drift, 4),
                    "weight_drift_relative_pct": round(relative_drift, 4),
                },
            )
        )
    return alerts


def evaluate_portfolio_drawdown(
    history: list[dict[str, Any]],
    *,
    as_of_date: date,
    rule: dict[str, Any],
) -> dict[str, Any] | None:
    if not history or not rule:
        return None
    lookback_days = int(rule.get("lookback_days", 20))
    rows = sorted(history, key=lambda item: str(item["snapshot_date"]))[-lookback_days:]
    values = [float(row.get("total_value_usd") or 0) for row in rows]
    peak = max(values) if values else 0
    latest = values[-1] if values else 0
    drawdown_pct = pct(latest - peak, peak)
    if drawdown_pct >= float(rule.get("threshold_pct", -12.0)):
        return None
    return make_alert(
        as_of_date=as_of_date,
        ticker="PORTFOLIO",
        rule=rule,
        message=f"Portfolio drawdown is {drawdown_pct:.2f}% over the last {len(rows)} rows.",
        metadata={"drawdown_pct": round(drawdown_pct, 4), "lookback_rows": len(rows)},
    )


def build_source_health(
    *,
    sources_config: dict[str, Any],
    portfolio_data: dict[str, Any],
    as_of_date: date,
    stale_days: int,
) -> list[dict[str, Any]]:
    rows = []
    price_dates = [
        date.fromisoformat(str(row["price_date"]))
        for row in portfolio_data.get("holdings", [])
        if row.get("source") == "yfinance" and row.get("price_date")
    ]
    latest_price_date = max(price_dates) if price_dates else None
    portfolio_updated = parse_utc_date(portfolio_data.get("updatedAtUtc"))
    for source in sources_config.get("sources", []):
        source_id = source["id"]
        last_update = None
        status = "planned"
        if source_id == "yfinance":
            last_update = latest_price_date.isoformat() if latest_price_date else None
            age = (as_of_date - latest_price_date).days if latest_price_date else None
            status = "healthy" if age is not None and age <= stale_days else "stale"
        elif source_id == "local_calculation":
            last_update = portfolio_updated.isoformat() if portfolio_updated else None
            age = (as_of_date - portfolio_updated).days if portfolio_updated else None
            status = "healthy" if age is not None and age <= 1 else "stale"
        elif source.get("update_mode") == "manual":
            status = "manual_expected"
        elif source.get("update_mode") == "planned":
            status = "planned"
        rows.append(
            {
                "id": source_id,
                "label": source["label"],
                "tier": source["tier"],
                "cadence": source["cadence"],
                "update_mode": source["update_mode"],
                "status_policy": source.get("status_policy", ""),
                "status": status,
                "last_update": last_update,
                "notes": source.get("notes", ""),
            }
        )
    return rows


def make_alert(
    *,
    as_of_date: date,
    ticker: str,
    rule: dict[str, Any],
    message: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "date": as_of_date.isoformat(),
        "ticker": ticker,
        "level": rule.get("level", "gray"),
        "category": rule.get("category", "system"),
        "rule_id": rule.get("id", "unknown"),
        "message": message,
        "requires_human_review": bool(rule.get("requires_human_review", False)),
        "source_ids": rule.get("source_ids", []),
        "metadata": metadata or {},
    }


def compact_metric_catalog(metrics_catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": ticker,
            "core_question": entry.get("core_question", ""),
            "metric_count": len(entry.get("metrics", [])),
            "metrics": [normalize_metric(metric) for metric in entry.get("metrics", [])],
            "watch_rule": entry.get("watch_rule", ""),
            "falsifier": entry.get("falsifier", []),
            "next_action": normalize_next_action(ticker, entry.get("next_action")),
        }
        for ticker, entry in metrics_catalog.items()
    ]


def normalize_metric(metric: dict[str, Any]) -> dict[str, Any]:
    evidence_state = metric.get("evidence_state", {})
    return {
        **metric,
        "evidence_state": {
            "state": evidence_state.get("state", metric.get("state", "unknown")),
            "confidence": evidence_state.get("confidence", metric.get("confidence", "unknown")),
            "last_evidence_date": evidence_state.get(
                "last_evidence_date", metric.get("last_evidence_date")
            ),
        },
    }


def normalize_next_action(ticker: str, next_action: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_action:
        return None
    return {
        "ticker": ticker,
        "type": next_action.get("type", "evidence_check"),
        "priority": next_action.get("priority", "medium"),
        "due": str(next_action.get("due", "")),
        "question": next_action.get("question", ""),
        "success_condition": next_action.get("success_condition", ""),
    }


def build_review_queue(
    holdings: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue = []
    for alert in alerts:
        if not alert.get("requires_human_review"):
            continue
        queue.append(
            {
                "ticker": alert["ticker"],
                "type": "alert_review",
                "priority": "high" if alert["level"] == "red" else "medium",
                "due": alert["date"],
                "question": alert["message"],
                "success_condition": "Human reviewer accepts, rejects, or rewrites the alert.",
                "source": "alert",
            }
        )
    for holding in holdings:
        action = holding.get("next_action")
        if action:
            queue.append({**action, "source": "next_action"})
    return sorted(
        queue,
        key=lambda item: (
            PRIORITY_RANK.get(item.get("priority", "medium"), 1),
            item.get("due") or "9999-12-31",
            item.get("ticker", ""),
        ),
    )


def count_source_statuses(source_health: list[dict[str, Any]]) -> dict[str, int]:
    return {
        status: sum(1 for source in source_health if source.get("status") == status)
        for status in SOURCE_STATUS_ORDER
    }


def current_weight(portfolio_row: dict[str, Any] | None, portfolio_total: float) -> float | None:
    if not portfolio_row or portfolio_total <= 0:
        return None
    return round(pct(float(portfolio_row.get("market_value_usd") or 0), portfolio_total), 4)


def weight_drift(
    holding: dict[str, Any],
    portfolio_row: dict[str, Any] | None,
    portfolio_total: float,
) -> float:
    value = current_weight(portfolio_row, portfolio_total)
    if value is None:
        return 0.0
    return value - normalize_weight(holding["target_weight"])


def normalize_weight(value: float | int | str) -> float:
    parsed = float(value)
    return parsed * 100.0 if parsed <= 1 else parsed


def highest_level(alerts: list[dict[str, Any]]) -> str:
    if not alerts:
        return "green"
    return max((alert["level"] for alert in alerts), key=lambda level: LEVEL_RANK.get(level, 0))


def count_levels(alerts: list[dict[str, Any]]) -> dict[str, int]:
    return {level: sum(1 for alert in alerts if alert["level"] == level) for level in LEVEL_RANK}


def pct(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator * 100.0


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing monitor config: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_yaml_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(value, list):
        raise ValueError(f"Expected YAML list: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def parse_utc_date(value: Any) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def today_utc() -> str:
    return datetime.now(UTC).date().isoformat()


def utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
