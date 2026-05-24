from pathlib import Path

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
    assert "No position change from watchlist data" in research_data
    assert "No target-weight change" in research_data

    assert 'id="tab-watchlist"' in index
    assert 'id="view-watchlist"' in index
    assert "renderWatchlist();" in app
    assert "function renderWatchlist()" in app
