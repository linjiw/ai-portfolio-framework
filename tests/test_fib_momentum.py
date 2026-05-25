import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ai_portfolio_framework.fib_momentum import (
    analyze_price_history,
    build_fib_momentum_data,
    build_monitor_universe,
    signal_for_score,
)
from ai_portfolio_framework.validate_site import validate_fib_momentum_json

ROOT = Path(__file__).resolve().parents[1]


def synthetic_history(start: float = 100.0, end: float = 130.0) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=150, freq="B")
    trend = np.linspace(start, end, len(dates))
    wave = np.sin(np.linspace(0, 8, len(dates))) * 0.8
    close = trend + wave
    return pd.DataFrame(
        {
            "Close": close,
            "High": close * 1.012,
            "Low": close * 0.988,
            "Volume": np.linspace(1_000_000, 1_400_000, len(dates)),
        },
        index=dates,
    )


def test_signal_thresholds_match_configured_bands() -> None:
    assert signal_for_score(80)[0] == "strong_bullish"
    assert signal_for_score(60)[0] == "bullish"
    assert signal_for_score(40)[0] == "neutral"
    assert signal_for_score(25)[0] == "bearish"
    assert signal_for_score(24.9)[0] == "strong_bearish"


def test_analyze_price_history_scores_bullish_stack() -> None:
    result = analyze_price_history("MSFT", synthetic_history())

    assert result.ticker == "MSFT"
    assert result.date == "2026-07-29"
    assert result.trend_score > 80
    assert result.signal in {"strong_bullish", "bullish"}
    assert result.metrics["emaStack"] in {"full_bull", "bull"}
    assert result.metrics["macdHist"] is not None


def test_build_monitor_universe_merges_portfolio_watchlist_and_current_positions(tmp_path) -> None:
    watchlist_path = tmp_path / "watchlist.yml"
    current_path = tmp_path / "current.json"
    holdings_path = tmp_path / "holdings.csv"
    watchlist_path.write_text(
        yaml.safe_dump(
            {
                "rules": {
                    "MU": {
                        "status": "watchlist_only",
                        "relationship": "possible_hbm_challenger",
                    },
                    "MSFT": {"status": "holding_watch", "relationship": "existing_holding"},
                }
            }
        ),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "symbol": "TER280121C175",
                        "underlying": "TER",
                        "description": "TER JAN 2028 CALL",
                        "instrument": "long_call",
                        "currentValueUsd": 500.0,
                        "currentWeightPct": 5.0,
                    },
                    {
                        "symbol": "SPAXX**",
                        "description": "FIDELITY GOVERNMENT MONEY MARKET",
                        "instrument": "cash",
                        "currentValueUsd": 100.0,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    targets = build_monitor_universe(
        portfolio_data_path=tmp_path / "missing-portfolio.json",
        watchlist_rules_path=watchlist_path,
        holdings_path=holdings_path,
        current_positions_path=current_path,
        portfolio_data={
            "holdings": [
                {"ticker": "MSFT", "holding_name": "Microsoft", "target_weight": 18},
                {"ticker": "CASH", "holding_name": "Cash", "target_weight": 10},
            ]
        },
    )

    assert set(targets) == {"MSFT", "MU", "TER"}
    assert targets["MSFT"].sources == {"portfolio", "watchlist"}
    assert targets["MSFT"].target_weight_pct == 18
    assert targets["MU"].sources == {"watchlist"}
    assert targets["TER"].sources == {"current_position"}
    assert targets["TER"].current_value_usd == 500


def test_build_fib_momentum_data_writes_network_free_json(tmp_path) -> None:
    watchlist_path = tmp_path / "watchlist.yml"
    current_path = tmp_path / "current.json"
    output_path = tmp_path / "fib.json"
    watchlist_path.write_text(
        yaml.safe_dump({"rules": {"MU": {"status": "watchlist_only"}}}),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "symbol": "TER",
                        "description": "TERADYNE INC",
                        "instrument": "equity",
                        "currentValueUsd": 300.0,
                        "currentWeightPct": 3.0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = build_fib_momentum_data(
        portfolio_data_path=tmp_path / "missing-portfolio.json",
        watchlist_rules_path=watchlist_path,
        holdings_path=tmp_path / "missing-holdings.csv",
        current_positions_path=current_path,
        output_path=output_path,
        generated_output_path=None,
        portfolio_data={"holdings": [{"ticker": "MSFT", "holding_name": "Microsoft"}]},
        price_history_by_ticker={
            "MSFT": synthetic_history(100, 130),
            "MU": synthetic_history(50, 70),
            "TER": synthetic_history(80, 95),
        },
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved == payload
    assert payload["generatedAtUtc"] == "2026-05-25T00:00:00Z"
    assert payload["summary"]["scannedCount"] == 3
    assert payload["summary"]["failureCount"] == 0
    assert {row["ticker"] for row in payload["rows"]} == {"MSFT", "MU", "TER"}
    assert all(row["actionBoundary"] == "review_only_no_automatic_trade" for row in payload["rows"])
    assert validate_fib_momentum_json(tmp_path, output_path) == []


def test_fib_momentum_site_contract() -> None:
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

    assert "fibMomentumStatus" in index
    assert "fibMomentumRows" in index
    assert "loadFibMomentum();" in app
    assert "fib-momentum-data.json" in app
