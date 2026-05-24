"""Deterministic research-monitor layer for the AI portfolio framework."""

from __future__ import annotations

import argparse
import json
import re
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
RISK_FACTORS_CONFIG_PATH = CONFIG_DIR / "risk_factors.yml"
FALSIFIER_THRESHOLDS_CONFIG_PATH = CONFIG_DIR / "falsifier_thresholds.yml"
BEAR_CASES_CONFIG_PATH = CONFIG_DIR / "bear_cases.yml"
VALUATION_BANDS_CONFIG_PATH = CONFIG_DIR / "valuation_bands.yml"
DECISION_LOG_PATH = GENERATED_DATA_DIR.parent / "decision_log.yml"
EVIDENCE_LOG_PATH = GENERATED_DATA_DIR.parent / "evidence_log.yml"
THESIS_CHANGELOG_PATH = GENERATED_DATA_DIR.parent / "thesis_changelog.yml"
RESEARCH_DATA_PATH = SITE_DIR / "research-data.js"
SITE_PORTFOLIO_DATA_PATH = SITE_DIR / "portfolio-data.json"
SITE_MONITOR_DATA_PATH = SITE_DIR / "research-monitor-data.json"
SITE_PROVENANCE_COVERAGE_PATH = SITE_DIR / "provenance-coverage.json"
GENERATED_MONITOR_DATA_PATH = GENERATED_DATA_DIR / "dashboard_data.json"
GENERATED_PROVENANCE_COVERAGE_PATH = GENERATED_DATA_DIR / "provenance_coverage.json"

LEVEL_RANK = {"green": 0, "blue": 1, "gray": 1, "yellow": 2, "red": 3}
SOURCE_STATUS_ORDER = ("healthy", "manual_expected", "planned", "stale", "broken")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
PRIORITY_SCORE = {"high": 70, "medium": 40, "low": 10}
EVIDENCE_STATE_SCORE = {
    "deteriorating": 40,
    "unknown": 25,
    "watching": 15,
    "improving": 5,
    "confirmed": 0,
}


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
    risk_factors_config_path: Path = RISK_FACTORS_CONFIG_PATH,
    falsifier_thresholds_config_path: Path = FALSIFIER_THRESHOLDS_CONFIG_PATH,
    bear_cases_config_path: Path = BEAR_CASES_CONFIG_PATH,
    valuation_bands_config_path: Path = VALUATION_BANDS_CONFIG_PATH,
    decision_log_path: Path = DECISION_LOG_PATH,
    evidence_log_path: Path = EVIDENCE_LOG_PATH,
    thesis_changelog_path: Path = THESIS_CHANGELOG_PATH,
    research_data_path: Path = RESEARCH_DATA_PATH,
    portfolio_data_path: Path = SITE_PORTFOLIO_DATA_PATH,
    output_path: Path = SITE_MONITOR_DATA_PATH,
    generated_output_path: Path | None = GENERATED_MONITOR_DATA_PATH,
    provenance_output_path: Path | None = SITE_PROVENANCE_COVERAGE_PATH,
    generated_provenance_output_path: Path | None = GENERATED_PROVENANCE_COVERAGE_PATH,
    portfolio_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and persist the static JSON used by the research-monitor UI."""

    ensure_directories()
    holdings_config = load_yaml(holdings_config_path)
    metrics_catalog = load_yaml(metrics_catalog_path)
    alert_rules = load_yaml(alert_rules_path)
    sources_config = load_yaml(sources_config_path)
    risk_factors_config = load_yaml_optional(risk_factors_config_path)
    falsifier_thresholds_config = load_yaml_optional(falsifier_thresholds_config_path)
    bear_cases_config = load_yaml_optional(bear_cases_config_path)
    valuation_bands_config = load_yaml_optional(valuation_bands_config_path)
    decision_log = load_yaml_list(decision_log_path)
    evidence_log = load_yaml_list(evidence_log_path)
    thesis_changelog = load_yaml_list(thesis_changelog_path)
    evidence_index = latest_evidence_by_metric(evidence_log)
    portfolio_data = portfolio_data or load_json(portfolio_data_path)

    as_of_date = date.fromisoformat(portfolio_data.get("asOfDate", today_utc()))
    summary = portfolio_data.get("summary", {})
    portfolio_total = float(summary.get("total_value_usd") or 0)
    portfolio_rows = {row["ticker"]: row for row in portfolio_data.get("holdings", [])}
    rules_by_id = {rule["id"]: rule for rule in alert_rules.get("rules", [])}
    holding_tickers = [str(holding["ticker"]) for holding in holdings_config.get("holdings", [])]
    risk_overlay = build_risk_overlay(holdings_config, risk_factors_config)
    falsifier_threshold_index = index_by_ticker(
        falsifier_thresholds_config.get("thresholds", [])
    )
    bear_case_index = index_by_ticker(bear_cases_config.get("bear_cases", []))
    valuation_band_index = index_by_ticker(valuation_bands_config.get("bands", []))
    decision_discipline = build_decision_discipline(
        holding_tickers=holding_tickers,
        falsifier_thresholds_config=falsifier_thresholds_config,
        bear_cases_config=bear_cases_config,
        valuation_bands_config=valuation_bands_config,
    )

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
        metrics = [
            normalize_metric(metric, ticker=ticker, evidence_index=evidence_index)
            for metric in catalog_entry.get("metrics", [])
        ]
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
                "risk_profile": risk_overlay.get("holdingRisk", {}).get(ticker, {}),
                "falsifier_threshold": falsifier_threshold_index.get(ticker),
                "bear_case": bear_case_index.get(ticker),
                "valuation_band": valuation_band_index.get(ticker),
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
    review_queue = build_review_queue(monitored_holdings, alerts, as_of_date=as_of_date)
    evidence_coverage = build_evidence_coverage(monitored_holdings)
    provenance_coverage = build_provenance_coverage(
        research_data_path=research_data_path,
        evidence_log=evidence_log,
    )
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
            "evidence_coverage": evidence_coverage,
            "provenance_coverage": provenance_coverage["summary"],
            "risk_overlay": risk_overlay["summary"],
            "decision_discipline": decision_discipline["summary"],
        },
        "alerts": alerts,
        "reviewQueue": review_queue,
        "sourceHealth": source_health,
        "holdings": monitored_holdings,
        "metricCatalog": compact_metric_catalog(metrics_catalog, evidence_index=evidence_index),
        "riskOverlay": risk_overlay,
        "decisionDiscipline": decision_discipline,
        "decisionLog": decision_log[-10:],
        "evidenceLog": evidence_log[-20:],
        "thesisChangelog": thesis_changelog[-20:],
    }
    write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    if provenance_output_path:
        write_json(provenance_output_path, provenance_coverage)
    if generated_provenance_output_path:
        write_json(generated_provenance_output_path, provenance_coverage)
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


def compact_metric_catalog(
    metrics_catalog: dict[str, Any],
    *,
    evidence_index: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "ticker": ticker,
            "core_question": entry.get("core_question", ""),
            "metric_count": len(entry.get("metrics", [])),
            "metrics": [
                normalize_metric(metric, ticker=ticker, evidence_index=evidence_index)
                for metric in entry.get("metrics", [])
            ],
            "watch_rule": entry.get("watch_rule", ""),
            "falsifier": entry.get("falsifier", []),
            "next_action": normalize_next_action(ticker, entry.get("next_action")),
        }
        for ticker, entry in metrics_catalog.items()
    ]


def normalize_metric(
    metric: dict[str, Any],
    *,
    ticker: str,
    evidence_index: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    evidence_state = metric.get("evidence_state", {})
    latest_evidence = evidence_index.get((ticker, metric["id"]))
    if latest_evidence:
        evidence_state = {
            "state": latest_evidence.get("state_after", "unknown"),
            "confidence": latest_evidence.get("confidence", "unknown"),
            "last_evidence_date": str(latest_evidence.get("date", "")) or None,
            "direction": latest_evidence.get("direction", "unknown"),
            "latest_summary": latest_evidence.get("summary", ""),
            "evidence_type": latest_evidence.get("evidence_type", ""),
            "source_ids": latest_evidence.get("source_ids", []),
            "claim_ids": latest_evidence.get("claim_ids", []),
            "requires_review": bool(latest_evidence.get("requires_review", False)),
        }
    return {
        **metric,
        "evidence_state": {
            "state": evidence_state.get("state", metric.get("state", "unknown")),
            "confidence": evidence_state.get("confidence", metric.get("confidence", "unknown")),
            "last_evidence_date": evidence_state.get(
                "last_evidence_date", metric.get("last_evidence_date")
            ),
            "direction": evidence_state.get("direction", metric.get("direction", "unknown")),
            "latest_summary": evidence_state.get("latest_summary", ""),
            "evidence_type": evidence_state.get("evidence_type", ""),
            "source_ids": evidence_state.get("source_ids", []),
            "claim_ids": evidence_state.get("claim_ids", []),
            "requires_review": bool(evidence_state.get("requires_review", False)),
        },
    }


def normalize_next_action(ticker: str, next_action: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_action:
        return None
    return {
        "ticker": ticker,
        "type": next_action.get("type", "evidence_check"),
        "metric_id": next_action.get("metric_id"),
        "priority": next_action.get("priority", "medium"),
        "due": str(next_action.get("due", "")),
        "question": next_action.get("question", ""),
        "success_condition": next_action.get("success_condition", ""),
    }


def build_review_queue(
    holdings: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    *,
    as_of_date: date,
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
                "alert_level": alert["level"],
            }
            | score_review_item(
                priority="high" if alert["level"] == "red" else "medium",
                due=alert["date"],
                metric=None,
                as_of_date=as_of_date,
                alert_level=alert["level"],
                ticker=alert["ticker"],
            )
        )
    for holding in holdings:
        action = holding.get("next_action")
        if action:
            metric = metric_by_id(holding.get("top_metrics", []), action.get("metric_id"))
            queue.append(
                {
                    **action,
                    "source": "next_action",
                    **score_review_item(
                        priority=action.get("priority", "medium"),
                        due=action.get("due"),
                        metric=metric,
                        as_of_date=as_of_date,
                        alert_level=None,
                        ticker=holding["ticker"],
                        risk_profile=holding.get("risk_profile"),
                    ),
                }
            )
    return sorted(
        queue,
        key=lambda item: (
            -float(item.get("score", 0)),
            PRIORITY_RANK.get(item.get("priority", "medium"), 1),
            item.get("due") or "9999-12-31",
            item.get("ticker", ""),
        ),
    )


def score_review_item(
    *,
    priority: str,
    due: str | None,
    metric: dict[str, Any] | None,
    as_of_date: date,
    alert_level: str | None,
    ticker: str,
    risk_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    score = PRIORITY_SCORE.get(priority, 40)
    reasons = [f"{priority} priority"]
    if alert_level == "red":
        score += 50
        reasons.append("red alert")
    elif alert_level == "yellow":
        score += 25
        reasons.append("yellow alert")

    urgency_score = due_date_score(due, as_of_date)
    if urgency_score:
        score += urgency_score
        reasons.append("due date approaching")

    evidence_state = None
    if metric:
        evidence_state = metric.get("evidence_state", {})
        state = evidence_state.get("state", "unknown")
        state_score = EVIDENCE_STATE_SCORE.get(state, 0)
        score += state_score
        if state_score:
            reasons.append(f"{state} evidence")
        if evidence_state.get("requires_review"):
            score += 10
            reasons.append("evidence requires review")

    if ticker == "MSFT":
        score += 10
        reasons.append("framework trust bottleneck")

    capex_profile = (risk_profile or {}).get("hyperscaler_capex_cycle", {})
    if capex_profile.get("category") == "direct":
        score += 8
        reasons.append("direct capex-cycle exposure")
    if capex_profile.get("sensitivity") == "high":
        score += 5
        reasons.append("high cycle sensitivity")

    return {
        "score": score,
        "score_reasons": reasons,
        "evidence_state": evidence_state,
    }


def due_date_score(due: str | None, as_of_date: date) -> int:
    if not due:
        return 0
    try:
        remaining = (date.fromisoformat(str(due)) - as_of_date).days
    except ValueError:
        return 0
    if remaining < 0:
        return 30
    if remaining <= 30:
        return 15
    if remaining <= 90:
        return 5
    return 0


def metric_by_id(metrics: list[dict[str, Any]], metric_id: str | None) -> dict[str, Any] | None:
    for metric in metrics:
        if metric.get("id") == metric_id:
            return metric
    return metrics[0] if metrics else None


def count_source_statuses(source_health: list[dict[str, Any]]) -> dict[str, int]:
    return {
        status: sum(1 for source in source_health if source.get("status") == status)
        for status in SOURCE_STATUS_ORDER
    }


def latest_evidence_by_metric(
    evidence_log: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for item in sorted(evidence_log, key=lambda value: str(value.get("date", ""))):
        ticker = str(item.get("ticker", ""))
        metric_id = str(item.get("metric_id", ""))
        if ticker and metric_id:
            latest[(ticker, metric_id)] = item
    return latest


def build_evidence_coverage(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [
        metric
        for holding in holdings
        for metric in holding.get("top_metrics", [])
    ]
    covered = [
        metric
        for metric in metrics
        if metric.get("evidence_state", {}).get("state") != "unknown"
    ]
    total = len(metrics)
    return {
        "total_metrics": total,
        "covered_metrics": len(covered),
        "unknown_metrics": total - len(covered),
        "coverage_ratio": round(len(covered) / total, 4) if total else 0.0,
    }


def build_risk_overlay(
    holdings_config: dict[str, Any],
    risk_config: dict[str, Any],
) -> dict[str, Any]:
    holdings = holdings_config.get("holdings", [])
    target_weights = {
        str(holding["ticker"]): normalize_weight(holding.get("target_weight", 0))
        for holding in holdings
    }
    holding_risk_config = risk_config.get("holding_risk", {})
    holding_risk = {
        ticker: holding_risk_config.get(ticker, {})
        for ticker in target_weights
    }

    risk_factors = []
    high_concentration_count = 0
    capex_direct_exposure_pct = 0.0
    for factor in risk_config.get("risk_factors", []):
        exposure_groups = {}
        for group, tickers in factor.get("exposure_groups", {}).items():
            normalized_tickers = [str(ticker) for ticker in tickers]
            target_weight = sum(target_weights.get(ticker, 0.0) for ticker in normalized_tickers)
            exposure_groups[group] = {
                "target_weight": round(target_weight, 4),
                "tickers": normalized_tickers,
            }

        primary_group = factor.get("primary_group", "direct")
        primary_exposure = float(
            exposure_groups.get(primary_group, {}).get("target_weight", 0.0)
        )
        threshold = float(factor.get("threshold_pct", 100.0))
        status = "yellow" if primary_exposure > threshold else "green"
        if status == "yellow":
            high_concentration_count += 1
        if factor.get("id") == "hyperscaler_capex_cycle":
            capex_direct_exposure_pct = primary_exposure

        risk_factors.append(
            {
                "id": factor.get("id", ""),
                "label": factor.get("label", ""),
                "type": factor.get("type", ""),
                "threshold_pct": threshold,
                "primary_group": primary_group,
                "primary_exposure_pct": round(primary_exposure, 4),
                "status": status,
                "review_policy": factor.get("review_policy", ""),
                "thesis_test": factor.get("thesis_test", ""),
                "exposure_groups": exposure_groups,
            }
        )

    framework_gaps = risk_config.get("framework_gaps", [])
    return {
        "policy": risk_config.get("policy", {}),
        "summary": {
            "risk_factor_count": len(risk_factors),
            "high_concentration_count": high_concentration_count,
            "capex_direct_exposure_pct": round(capex_direct_exposure_pct, 4),
            "framework_gap_count": len(framework_gaps),
        },
        "riskFactors": risk_factors,
        "holdingRisk": holding_risk,
        "frameworkGaps": framework_gaps,
    }


def build_decision_discipline(
    *,
    holding_tickers: list[str],
    falsifier_thresholds_config: dict[str, Any],
    bear_cases_config: dict[str, Any],
    valuation_bands_config: dict[str, Any],
) -> dict[str, Any]:
    falsifier_thresholds = falsifier_thresholds_config.get("thresholds", [])
    bear_cases = bear_cases_config.get("bear_cases", [])
    valuation_bands = valuation_bands_config.get("bands", [])
    falsifier_index = index_by_ticker(falsifier_thresholds)
    bear_case_index = index_by_ticker(bear_cases)
    valuation_band_index = index_by_ticker(valuation_bands)
    total = len(holding_tickers)

    return {
        "policy": {
            "falsifier_thresholds": falsifier_thresholds_config.get("policy", {}),
            "bear_cases": bear_cases_config.get("policy", {}),
            "valuation_bands": valuation_bands_config.get("policy", {}),
        },
        "summary": {
            "holding_count": total,
            "operational_falsifier_count": coverage_count(falsifier_index, holding_tickers),
            "bear_case_count": coverage_count(bear_case_index, holding_tickers),
            "valuation_band_count": coverage_count(valuation_band_index, holding_tickers),
            "operational_falsifier_coverage": coverage_ratio(
                falsifier_index, holding_tickers
            ),
            "bear_case_coverage": coverage_ratio(bear_case_index, holding_tickers),
            "valuation_band_coverage": coverage_ratio(valuation_band_index, holding_tickers),
        },
        "falsifierThresholds": falsifier_thresholds,
        "bearCases": bear_cases,
        "valuationBands": valuation_bands,
    }


def index_by_ticker(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item["ticker"]): item
        for item in items
        if item.get("ticker")
    }


def coverage_count(index: dict[str, Any], tickers: list[str]) -> int:
    return sum(1 for ticker in tickers if ticker in index)


def coverage_ratio(index: dict[str, Any], tickers: list[str]) -> float:
    return round(coverage_count(index, tickers) / len(tickers), 4) if tickers else 0.0


def build_provenance_coverage(
    *,
    research_data_path: Path,
    evidence_log: list[dict[str, Any]],
) -> dict[str, Any]:
    text = research_data_path.read_text(encoding="utf-8") if research_data_path.exists() else ""
    evidence_counts = holding_evidence_counts(text)
    claim_entities = claim_entities_by_ticker(text)
    claim_source_ids = claim_source_ids_by_ticker(text)
    source_labels = source_labels_by_id(text)
    material_evidence_bullets = sum(evidence_counts.values())
    claim_linked_bullets = sum(
        min(evidence_counts.get(ticker, 0), len(claim_entities.get(ticker, [])))
        for ticker in evidence_counts
    )
    evidence_log_links = sum(
        1 for item in evidence_log if item.get("source_ids") or item.get("claim_ids")
    )
    weak_sources = build_weak_source_records(
        claim_source_ids=claim_source_ids,
        source_labels=source_labels,
        evidence_log=evidence_log,
    )
    coverage_ratio = (
        round(claim_linked_bullets / material_evidence_bullets, 4)
        if material_evidence_bullets
        else 0.0
    )
    return {
        "schemaVersion": 1,
        "generatedAtUtc": utc_iso(),
        "summary": {
            "materialEvidenceBullets": material_evidence_bullets,
            "claimLinkedEvidenceBullets": claim_linked_bullets,
            "coverageRatio": coverage_ratio,
            "evidenceLogEntries": len(evidence_log),
            "evidenceLogEntriesWithSourceOrClaim": evidence_log_links,
            "weakSourceCount": len(weak_sources),
        },
        "holdingsMissingClaimCoverage": missing_claim_coverage(evidence_counts, claim_entities),
        "holdingEvidenceCounts": evidence_counts,
        "claimCountsByHolding": {
            ticker: len(claim_entities.get(ticker, [])) for ticker in sorted(evidence_counts)
        },
        "weakSources": weak_sources,
    }


def holding_evidence_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    pattern = re.compile(r'\{\s*ticker: "([^"]+)".*?evidence: \[(.*?)\]\s*,\s*risks:', re.S)
    for ticker, evidence_block in pattern.findall(text):
        counts[ticker] = len(re.findall(r'"(?:\\.|[^"\\])*"', evidence_block))
    return counts


def claim_entities_by_ticker(text: str) -> dict[str, list[str]]:
    entities: dict[str, list[str]] = {}
    pattern = re.compile(r'claim_id: "([^"]+)".*?entity: "([^"]+)"', re.S)
    for claim_id, entity in pattern.findall(text):
        entities.setdefault(entity, []).append(claim_id)
    return entities


def claim_source_ids_by_ticker(text: str) -> dict[str, list[str]]:
    source_ids: dict[str, list[str]] = {}
    pattern = re.compile(
        r'claim_id: "([^"]+)".*?source_id: "([^"]+)".*?entity: "([^"]+)"',
        re.S,
    )
    for _claim_id, source_id, entity in pattern.findall(text):
        source_ids.setdefault(entity, []).append(source_id)
    return source_ids


def source_labels_by_id(text: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    pattern = re.compile(r'"([^"]+)": \{\s*label: "([^"]+)"', re.S)
    for source_id, label in pattern.findall(text):
        labels[source_id] = label
    return labels


def missing_claim_coverage(
    evidence_counts: dict[str, int],
    claim_entities: dict[str, list[str]],
) -> list[str]:
    return [
        ticker
        for ticker, count in evidence_counts.items()
        if count and not claim_entities.get(ticker)
    ]


def build_weak_source_records(
    *,
    claim_source_ids: dict[str, list[str]],
    source_labels: dict[str, str],
    evidence_log: list[dict[str, Any]],
) -> list[dict[str, str]]:
    weak = []
    seen = set()
    weak_terms = ("reuters", "investing.com", "secondary")
    for ticker, source_ids in sorted(claim_source_ids.items()):
        for source_id in source_ids:
            label = source_labels.get(source_id, "")
            if any(term in label.lower() for term in weak_terms):
                weak.append(weak_source_record(ticker, source_id, label))
                seen.add((ticker, source_id))
    for item in evidence_log:
        ticker = str(item.get("ticker", ""))
        for source_id in item.get("source_ids", []):
            label = source_labels.get(source_id, "")
            key = (ticker, source_id)
            if key in seen:
                continue
            if any(term in label.lower() for term in weak_terms):
                weak.append(weak_source_record(ticker, source_id, label))
                seen.add(key)
    return weak


def weak_source_record(ticker: str, source_id: str, label: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "source_id": source_id,
        "reason": f"Secondary or syndicated source: {label}",
        "recommended_action": (
            "Supplement with primary filing, company, regulatory, or operator data."
        ),
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


def load_yaml_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_yaml(path)


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
