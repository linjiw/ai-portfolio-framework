from datetime import date

import yaml

from ai_portfolio_framework.research_monitor import build_research_monitor_data


def write_yaml(path, payload) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_research_monitor_flags_stale_price_and_weight_drift(tmp_path) -> None:
    holdings_path = tmp_path / "holdings.yml"
    metrics_path = tmp_path / "metrics.yml"
    rules_path = tmp_path / "rules.yml"
    sources_path = tmp_path / "sources.yml"
    output_path = tmp_path / "monitor.json"

    write_yaml(
        holdings_path,
        {
            "portfolio": {"name": "test", "base_currency": "USD"},
            "holdings": [
                {
                    "ticker": "MSFT",
                    "name": "Microsoft",
                    "target_weight": 0.50,
                    "bucket": "Core",
                    "layers": ["Authority"],
                },
                {
                    "ticker": "CASH",
                    "name": "Cash",
                    "target_weight": 0.50,
                    "bucket": "Cash",
                    "layers": ["Risk control"],
                },
            ],
        },
    )
    write_yaml(
        metrics_path,
        {
            "MSFT": {
                "core_question": "Can MSFT control agent authority?",
                "metrics": [{"id": "agent", "name": "Agent evidence"}],
                "watch_rule": "No fresh evidence",
                "falsifier": ["No production permission"],
            },
            "CASH": {
                "core_question": "Does cash retain option value?",
                "metrics": [{"id": "drawdown", "name": "Drawdown"}],
            },
        },
    )
    write_yaml(
        rules_path,
        {
            "rules": [
                {
                    "id": "stale_price",
                    "category": "data",
                    "level": "yellow",
                    "threshold_days": 3,
                    "message": "Price stale",
                },
                {
                    "id": "missing_price",
                    "category": "data",
                    "level": "red",
                    "message": "Missing price",
                    "requires_human_review": True,
                },
                {
                    "id": "weight_drift",
                    "category": "market",
                    "level": "yellow",
                    "threshold_relative_pct": 15.0,
                    "message": "Weight drift",
                },
                {
                    "id": "portfolio_drawdown_watch",
                    "category": "market",
                    "level": "yellow",
                    "lookback_days": 20,
                    "threshold_pct": -12.0,
                    "message": "Drawdown",
                },
            ]
        },
    )
    write_yaml(
        sources_path,
        {
            "sources": [
                {
                    "id": "yfinance",
                    "label": "Yahoo Finance via yfinance",
                    "tier": "market_data",
                    "cadence": "daily",
                    "update_mode": "automated",
                },
                {
                    "id": "local_calculation",
                    "label": "Local portfolio calculation",
                    "tier": "system",
                    "cadence": "daily",
                    "update_mode": "automated",
                },
            ]
        },
    )
    portfolio_data = {
        "asOfDate": date(2026, 5, 23).isoformat(),
        "updatedAtUtc": "2026-05-23T12:00:00Z",
        "summary": {"total_value_usd": 1000.0},
        "holdings": [
            {
                "ticker": "MSFT",
                "market_value_usd": 600.0,
                "price_date": "2026-05-19",
                "source": "yfinance",
            },
            {
                "ticker": "CASH",
                "market_value_usd": 400.0,
                "price_date": "2026-05-23",
                "source": "cash",
            },
        ],
        "history": [{"snapshot_date": "2026-05-23", "total_value_usd": 1000.0}],
    }

    payload = build_research_monitor_data(
        holdings_config_path=holdings_path,
        metrics_catalog_path=metrics_path,
        alert_rules_path=rules_path,
        sources_config_path=sources_path,
        output_path=output_path,
        generated_output_path=None,
        portfolio_data=portfolio_data,
    )

    rule_ids = {alert["rule_id"] for alert in payload["alerts"]}
    assert {"stale_price", "weight_drift"} <= rule_ids
    assert payload["summary"]["highest_alert"] == "yellow"
    assert payload["summary"]["source_status_counts"]["stale"] == 1
    assert output_path.exists()
