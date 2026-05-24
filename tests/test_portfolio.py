from datetime import date

import pandas as pd

from ai_portfolio_framework import portfolio


def test_portfolio_handles_cash_and_krw_fx(tmp_path) -> None:
    config_path = tmp_path / "lots.json"
    summary_path = tmp_path / "summary.csv"
    holdings = pd.DataFrame(
        [
            {"ticker": "MSFT", "holding_name": "Microsoft", "target_weight": 50},
            {"ticker": "000660.KS", "holding_name": "SK Hynix", "target_weight": 40},
            {"ticker": "CASH", "holding_name": "Cash", "target_weight": 10},
        ]
    )
    initial_prices = {
        "MSFT": {"price_native": 100.0, "price_date": "2026-05-22", "source": "test"},
        "000660.KS": {"price_native": 200_000.0, "price_date": "2026-05-22", "source": "test"},
        "KRW=X": {"price_native": 1_000.0, "price_date": "2026-05-22", "source": "test"},
    }

    config = portfolio.load_or_create_config(
        holdings=holdings,
        latest_prices=initial_prices,
        initial_capital=1000.0,
        start_date=date(2026, 5, 22),
        holdings_path=tmp_path / "holdings.csv",
        config_path=config_path,
        force_reinitialize=True,
    )

    lots = {lot.ticker: lot for lot in config.lots}
    assert lots["MSFT"].quantity == 5
    assert lots["000660.KS"].quantity == 2
    assert lots["CASH"].quantity == 100

    current_prices = {
        "MSFT": {"price_native": 110.0, "price_date": "2026-05-23", "source": "test"},
        "000660.KS": {"price_native": 220_000.0, "price_date": "2026-05-23", "source": "test"},
        "KRW=X": {"price_native": 1_100.0, "price_date": "2026-05-23", "source": "test"},
    }
    snapshot = portfolio.build_snapshot(
        config=config,
        latest_prices=current_prices,
        snapshot_date=date(2026, 5, 23),
    )
    summary = portfolio.build_summary(
        config=config,
        snapshot=snapshot,
        snapshot_date=date(2026, 5, 23),
        summary_path=summary_path,
    )

    assert round(float(snapshot["market_value_usd"].sum()), 2) == 1050.0
    assert round(float(summary.iloc[0]["pnl_usd"]), 2) == 50.0
    assert round(float(summary.iloc[0]["return_pct"]), 2) == 5.0
    assert round(float(summary.iloc[0]["annualized_return_pct"]), 2) == 5.0
    assert summary.iloc[0]["annualized_return_basis"] == "since_start"
    assert int(summary.iloc[0]["annualized_return_days"]) == 1


def test_portfolio_price_tickers_include_fx() -> None:
    assert portfolio.portfolio_price_tickers(["MSFT", "000660.KS", "CASH"]) == [
        "000660.KS",
        "KRW=X",
        "MSFT",
    ]


def test_annual_return_metric_uses_trailing_year_when_available(tmp_path) -> None:
    summary_path = tmp_path / "summary.csv"
    summary_path.write_text(
        "\n".join(
            [
                ",".join(portfolio.SUMMARY_COLUMNS),
                "2025-05-23,900,800,100,1000,-100,-10,0,0,-10,since_start,0,2025-05-23T00:00:00Z",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    metric = portfolio.build_annual_return_metric(
        total_value=990.0,
        return_pct=-1.0,
        snapshot_date=date(2026, 5, 24),
        start_date=date(2025, 5, 23),
        summary_path=summary_path,
    )

    assert metric["basis"] == "trailing_1y"
    assert metric["days"] == 366
    assert round(float(metric["return_pct"]), 2) == 10.0


def test_two_day_history_uses_since_start_return_kpi(tmp_path) -> None:
    metric = portfolio.build_annual_return_metric(
        total_value=997.505209,
        return_pct=-0.249479,
        snapshot_date=date(2026, 5, 24),
        start_date=date(2026, 5, 22),
        summary_path=tmp_path / "missing-summary.csv",
    )
    return_kpi = portfolio.build_return_kpi(
        {
            "annualized_return_pct": metric["return_pct"],
            "annualized_return_basis": metric["basis"],
            "annualized_return_days": metric["days"],
        }
    )

    assert metric["basis"] == "since_start"
    assert metric["return_pct"] == -0.249479
    assert return_kpi == {
        "label": "Since start",
        "value": -0.00249479,
        "value_pct": -0.249479,
        "horizonDays": 2,
        "method": "cumulative_since_start",
        "isAnnualized": False,
    }


def test_364_day_history_still_uses_since_start(tmp_path) -> None:
    metric = portfolio.build_annual_return_metric(
        total_value=1100.0,
        return_pct=10.0,
        snapshot_date=date(2026, 5, 23),
        start_date=date(2025, 5, 24),
        summary_path=tmp_path / "summary.csv",
    )

    assert metric["basis"] == "since_start"
    assert metric["days"] == 364
    assert metric["return_pct"] == 10.0


def test_365_day_history_uses_nearest_year_ago_snapshot(tmp_path) -> None:
    summary_path = tmp_path / "summary.csv"
    summary_path.write_text(
        "\n".join(
            [
                ",".join(portfolio.SUMMARY_COLUMNS),
                "2025-05-24,1000,900,100,1000,0,0,0,0,0,since_start,0,2025-05-24T00:00:00Z",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    metric = portfolio.build_annual_return_metric(
        total_value=1084.0,
        return_pct=8.4,
        snapshot_date=date(2026, 5, 24),
        start_date=date(2025, 5, 24),
        summary_path=summary_path,
    )
    return_kpi = portfolio.build_return_kpi(
        {
            "annualized_return_pct": metric["return_pct"],
            "annualized_return_basis": metric["basis"],
            "annualized_return_days": metric["days"],
        }
    )

    assert metric["basis"] == "trailing_1y"
    assert metric["days"] == 365
    assert round(float(metric["return_pct"]), 2) == 8.4
    assert return_kpi["label"] == "Trailing 1Y"
    assert return_kpi["method"] == "nearest_snapshot_trailing_1y"
    assert return_kpi["isAnnualized"] is False


def test_short_history_csv_migration_removes_legacy_annualized_semantics() -> None:
    config = portfolio.PortfolioConfig(
        base_currency="USD",
        initial_capital_usd=1000.0,
        portfolio_start_date="2026-05-22",
        created_at_utc="2026-05-22T00:00:00Z",
        holdings_source="test",
        lots=[],
    )
    old_history = pd.DataFrame(
        [
            {
                "snapshot_date": "2026-05-23",
                "total_value_usd": 997.505209,
                "invested_value_usd": 897.505209,
                "cash_value_usd": 100.0,
                "cost_basis_usd": 1000.0,
                "pnl_usd": -2.494791,
                "return_pct": -0.249479,
                "daily_pnl_usd": -1.097418,
                "daily_return_pct": -0.109895,
                "annualized_return_pct": -59.817417,
            }
        ]
    )

    migrated = portfolio.normalize_summary_return_metrics(old_history, config=config)
    row = migrated.iloc[0]

    assert row["annualized_return_basis"] == "since_start"
    assert int(row["annualized_return_days"]) == 1
    assert round(float(row["annualized_return_pct"]), 6) == -0.249479
