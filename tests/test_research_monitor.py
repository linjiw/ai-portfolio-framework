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
    risk_path = tmp_path / "risk.yml"
    falsifier_path = tmp_path / "falsifiers.yml"
    bear_path = tmp_path / "bears.yml"
    valuation_path = tmp_path / "valuation.yml"
    evidence_path = tmp_path / "evidence.yml"
    research_data_path = tmp_path / "research-data.js"
    output_path = tmp_path / "monitor.json"
    provenance_path = tmp_path / "provenance.json"

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
                "next_action": {
                    "type": "evidence_check",
                    "metric_id": "agent",
                    "priority": "high",
                    "due": "2026-05-30",
                    "question": "Check agent evidence",
                },
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
        evidence_path,
        [
            {
                "date": "2026-05-23",
                "ticker": "MSFT",
                "metric_id": "agent",
                "direction": "deteriorating",
                "state_after": "deteriorating",
                "confidence": "medium",
                "summary": "Evidence got worse",
                "source_ids": ["msft-source"],
                "claim_ids": ["msft-claim"],
                "requires_review": True,
            }
        ],
    )
    research_data_path.write_text(
        """
        window.AI_FRAMEWORK_DATA = {
          holdings: [
            { ticker: "MSFT", evidence: ["one", "two"], risks: [] }
          ],
          claims: [
            { claim_id: "msft-claim", source_id: "msft-source", entity: "MSFT" }
          ],
          sources: {
            "msft-source": { label: "Microsoft source", url: "https://example.com" }
          }
        };
        """,
        encoding="utf-8",
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
    write_yaml(
        risk_path,
        {
            "policy": {"boundary": "Review only"},
            "risk_factors": [
                {
                    "id": "hyperscaler_capex_cycle",
                    "label": "Hyperscaler capex",
                    "threshold_pct": 40.0,
                    "primary_group": "direct",
                    "exposure_groups": {
                        "direct": ["MSFT"],
                        "hedge": ["CASH"],
                    },
                }
            ],
            "holding_risk": {
                "MSFT": {
                    "hyperscaler_capex_cycle": {
                        "category": "direct",
                        "sensitivity": "high",
                        "rationale": "Test risk",
                    }
                },
                "CASH": {
                    "hyperscaler_capex_cycle": {
                        "category": "hedge",
                        "sensitivity": "inverse_or_uncorrelated",
                        "rationale": "Test hedge",
                    }
                },
            },
            "framework_gaps": [{"id": "security", "label": "Security", "status": "watch"}],
        },
    )
    write_yaml(
        falsifier_path,
        {
            "policy": {"boundary": "Review only"},
            "thresholds": [
                {
                    "ticker": "MSFT",
                    "metric_id": "agent",
                    "threshold": "No production evidence",
                    "decision_rule": "Open review",
                },
                {
                    "ticker": "CASH",
                    "metric_id": "drawdown",
                    "threshold": "No option value",
                    "decision_rule": "Open review",
                },
            ],
        },
    )
    write_yaml(
        bear_path,
        {
            "policy": {"boundary": "Review only"},
            "bear_cases": [
                {"ticker": "MSFT", "bear_case": "Agent evidence stays weak"},
                {"ticker": "CASH", "bear_case": "Cash drag dominates"},
            ],
        },
    )
    write_yaml(
        valuation_path,
        {
            "policy": {"boundary": "Review only"},
            "bands": [
                {
                    "ticker": "MSFT",
                    "metric": "forward_pe",
                    "reasonable_band": "20-30x",
                    "review_high": "> 35x",
                    "review_low": "< 18x",
                },
                {
                    "ticker": "CASH",
                    "metric": "opportunity_cost",
                    "reasonable_band": "policy reserve",
                    "review_high": "cash drag",
                    "review_low": "drawdown risk",
                },
            ],
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
        risk_factors_config_path=risk_path,
        falsifier_thresholds_config_path=falsifier_path,
        bear_cases_config_path=bear_path,
        valuation_bands_config_path=valuation_path,
        evidence_log_path=evidence_path,
        research_data_path=research_data_path,
        output_path=output_path,
        generated_output_path=None,
        provenance_output_path=provenance_path,
        generated_provenance_output_path=None,
        portfolio_data=portfolio_data,
    )

    rule_ids = {alert["rule_id"] for alert in payload["alerts"]}
    assert {"stale_price", "weight_drift"} <= rule_ids
    assert payload["summary"]["highest_alert"] == "yellow"
    assert payload["summary"]["source_status_counts"]["stale"] == 1
    assert payload["summary"]["evidence_coverage"]["covered_metrics"] == 1
    assert payload["summary"]["risk_overlay"]["capex_direct_exposure_pct"] == 50.0
    assert payload["summary"]["decision_discipline"]["operational_falsifier_count"] == 2
    assert payload["reviewQueue"][0]["score"] > 0
    assert payload["reviewQueue"][0]["metric_id"] == "agent"
    assert "direct capex-cycle exposure" in payload["reviewQueue"][0]["score_reasons"]
    assert payload["holdings"][0]["top_metrics"][0]["evidence_state"]["state"] == "deteriorating"
    assert payload["holdings"][0]["falsifier_threshold"]["threshold"] == "No production evidence"
    assert payload["riskOverlay"]["riskFactors"][0]["status"] == "yellow"
    assert output_path.exists()
    assert provenance_path.exists()
