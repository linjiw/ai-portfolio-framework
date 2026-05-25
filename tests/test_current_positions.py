import json
from datetime import UTC, datetime
from pathlib import Path

from ai_portfolio_framework.current_positions import (
    build_current_positions_analysis,
    build_current_positions_from_seed,
)

HEADER = (
    "Account Number,Account Name,Symbol,Description,Quantity,Last Price,"
    "Last Price Change,Current Value,Today's Gain/Loss Dollar,"
    "Today's Gain/Loss Percent,Total Gain/Loss Dollar,Total Gain/Loss Percent,"
    "Percent Of Account,Cost Basis Total,Average Cost Basis,Type"
)


def test_current_positions_drop_account_fields_and_classify_rows(tmp_path) -> None:
    csv_path = tmp_path / "positions.csv"
    csv_path.write_text(
        "\n".join(
            [
                HEADER,
                (
                    'Z20695967,Individual,NVDA,NVIDIA CORP,10,$100.00,$0.00,'
                    '$1000.00,$0.00,0.00%,$100.00,10.00%,50.00%,$900.00,$90.00,Margin'
                ),
                (
                    'Z20695967,Individual,MU,MICRON TECHNOLOGY INC,5,$200.00,$0.00,'
                    '$1000.00,$0.00,0.00%,$0.00,0.00%,50.00%,$1000.00,$200.00,Margin'
                ),
                (
                    'Z20695967,Individual,TER280121C175,TER JAN 2028 175 CALL,1,$20.00,$0.00,'
                    '$2000.00,$0.00,0.00%,$0.00,0.00%,100.00%,$1500.00,$15.00,Margin'
                ),
                (
                    'Z20695967,Individual,-TER280121C185,TER JAN 2028 185 CALL,-1,$15.00,$0.00,'
                    '-$1500.00,$0.00,0.00%,$0.00,0.00%,-75.00%,-$1200.00,$12.00,Margin'
                ),
                (
                    'Z20695967,Individual,SPAXX**,FIDELITY GOVERNMENT MONEY MARKET,100,$1.00,'
                    '$0.00,$100.00,$0.00,0.00%,$0.00,0.00%,5.00%,$100.00,$1.00,Cash'
                ),
                "Date downloaded May-25-2026 3:46 a.m ET",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_current_positions_analysis(
        input_path=csv_path,
        output_path=None,
        generated_output_path=None,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    serialized = str(payload)
    assert "Z20695967" not in serialized
    assert "Individual" not in serialized
    assert "Margin" not in serialized
    assert payload["privacy"]["accountIdentifiersIncluded"] is False
    assert payload["downloadedAt"] == "May-25-2026 3:46 a.m ET"

    rows = {row["symbol"]: row for row in payload["positions"]}
    assert rows["NVDA"]["frameworkStatus"] == "framework_holding"
    assert rows["MU"]["frameworkStatus"] == "watchlist"
    assert rows["TER280121C175"]["frameworkStatus"] == "framework_derivative_overlay"
    assert rows["-TER280121C185"]["underlying"] == "TER"
    assert rows["SPAXX**"]["frameworkStatus"] == "cash"

    topics = {item["topic"] for item in payload["reviewQueue"]}
    assert {"memory_watchlist", "derivative_overlay"} <= topics
    assert payload["derivativeOverlay"]["netValueByUnderlying"][0]["underlying"] == "TER"


def test_current_positions_refresh_from_public_seed(tmp_path) -> None:
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "seededFrom": {"downloadedAt": "May-25-2026 3:46 a.m ET"},
                "positions": [
                    {
                        "symbol": "NVDA",
                        "description": "NVIDIA CORP",
                        "quantity": 10,
                        "instrument": "equity",
                        "seedValueUsd": 1000,
                        "costBasisUsd": 900,
                        "fallbackMarkUsd": 100,
                    },
                    {
                        "symbol": "TER280121C175",
                        "description": "TER JAN 2028 CALL",
                        "quantity": 1,
                        "instrument": "long_call",
                        "option": {
                            "underlying": "TER",
                            "expiration": "2028-01-21",
                            "right": "C",
                            "strike": 175,
                        },
                        "seedValueUsd": 2000,
                        "costBasisUsd": 1500,
                        "fallbackMarkUsd": 20,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_current_positions_from_seed(
        seed_path=seed_path,
        output_path=None,
        generated_output_path=None,
        latest_prices={
            "NVDA": {
                "price_native": 120.0,
                "price_date": "2026-05-25",
                "source": "test_price",
            }
        },
        option_prices={
            "TER280121C175": {
                "price": 25.0,
                "price_date": "2026-05-25",
                "source": "test_option",
            }
        },
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    rows = {row["symbol"]: row for row in payload["positions"]}
    assert (
        payload["privacy"]["publicationBoundary"]
        == "public_sanitized_seed_no_account_identifiers"
    )
    assert rows["NVDA"]["currentValueUsd"] == 1200
    assert rows["NVDA"]["priceStatus"] == "refreshed"
    assert rows["TER280121C175"]["currentValueUsd"] == 2500
    assert payload["summary"]["priceStatusCounts"] == {"refreshed": 2}


def test_current_positions_site_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    index = (root / "site" / "index.html").read_text(encoding="utf-8")
    app = (root / "site" / "app.js").read_text(encoding="utf-8")
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    site_builder = (
        root / "src" / "ai_portfolio_framework" / "site_builder.py"
    ).read_text(encoding="utf-8")
    seed_path = root / "data" / "manual" / "current_positions_public_seed.json"

    assert 'id="tab-current"' in index
    assert 'id="view-current"' in index
    assert "loadCurrentPositions();" in app
    assert "current-positions-data.json" in app
    assert "site/current-positions-data.json" not in gitignore
    assert "data/generated/current_positions_analysis.json" in gitignore
    assert 'current_positions_path=output_dir / "current-positions-data.json"' in site_builder
    assert seed_path.exists()
