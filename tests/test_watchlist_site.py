import json
import re
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_memory_watchlist_static_contract() -> None:
    research_data = (ROOT / "site" / "research-data.js").read_text(encoding="utf-8")
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

    assert "watchlist:" in research_data
    assert 'ticker: "MU"' in research_data
    assert 'ticker: "000660.KS"' in research_data
    assert 'status: "watchlist_not_position"' in research_data
    assert 'status: "portfolio_holding_watch"' in research_data
    assert "micron-q2-2026-results" in research_data
    assert "skhynix-high-na-euv" in research_data
    for source_id in (
        "micron-q2-2026-results",
        "micron-q2-2026-deck",
        "micron-jpm-2026",
        "micron-sec-submissions",
        "skhynix-hbm4",
        "skhynix-q1-2026",
        "skhynix-fy2025-results",
        "skhynix-high-na-euv",
        "asml-2025-results",
    ):
        assert f'"{source_id}":' in research_data
    assert "No position change from watchlist data" in research_data
    assert "No target-weight change" in research_data
    assert "Research-only watchlist" in research_data
    assert "comparisonGates" in research_data
    assert "advantage_current_holding" in research_data
    assert "challenger_gap_closing" in research_data
    watchlist_text = re.search(r"\n  watchlist: \{(?P<body>.*?)\n  claims:", research_data, re.S)
    assert watchlist_text
    assert not re.search(r"\b(winner|buy|sell|automatic_rebalance)\b", watchlist_text.group("body"))

    assert 'id="tab-watchlist"' in index
    assert 'id="view-watchlist"' in index
    assert "renderWatchlist();" in app
    assert "function renderWatchlist()" in app


def test_watchlist_rules_do_not_create_shadow_holdings() -> None:
    rules = yaml.safe_load((ROOT / "config" / "watchlist_rules.yml").read_text())
    sec_config = yaml.safe_load((ROOT / "config" / "sec_companies.yml").read_text())
    portfolio = json.loads((ROOT / "site" / "portfolio-data.json").read_text())
    holdings = pd.read_csv(ROOT / "data" / "manual" / "ai_framework_holdings.csv")
    holding_tickers = set(holdings["ticker"])
    portfolio_tickers = {holding["ticker"] for holding in portfolio["holdings"]}

    assert rules["schema_version"] == 1
    assert "MU" not in holding_tickers
    assert "MU" not in portfolio_tickers
    assert "MU" in sec_config["companies"]
    assert "000660.KS" in holding_tickers
    assert "000660.KS" in portfolio_tickers
    assert rules["rules"]["MU"]["status"] == "watchlist_only"
    assert rules["rules"]["000660.KS"]["status"] == "holding_watch"
    assert rules["rules"]["MU"]["promotion_gate"]["requires_decision_log"] is True
    assert rules["rules"]["000660.KS"]["thesis_gate"]["requires_decision_log"] is True

    disallowed = set(rules["policy"]["disallowed_outputs"])
    assert {"winner", "buy", "sell", "automatic_rebalance"} <= disallowed
    allowed_states = set(rules["policy"]["allowed_review_states"])
    for gate in rules["comparison_gates"]:
        assert gate["review_state"] in allowed_states
        assert gate["action"] == "review_only"
