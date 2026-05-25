from datetime import UTC, datetime
from pathlib import Path

from ai_portfolio_framework.current_positions import build_current_positions_analysis

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


def test_current_positions_site_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    index = (root / "site" / "index.html").read_text(encoding="utf-8")
    app = (root / "site" / "app.js").read_text(encoding="utf-8")
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")

    assert 'id="tab-current"' in index
    assert 'id="view-current"' in index
    assert "loadCurrentPositions();" in app
    assert "current-positions-data.json" in app
    assert "site/current-positions-data.json" in gitignore
    assert "data/generated/current_positions_analysis.json" in gitignore
