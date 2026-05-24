from datetime import UTC, datetime

import yaml

from ai_portfolio_framework.sec_filings import build_sec_filings


def write_yaml(path, payload) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_build_sec_filings_marks_new_relevant_filing_for_review(tmp_path) -> None:
    config_path = tmp_path / "sec.yml"
    output_path = tmp_path / "sec-filings.json"

    write_yaml(
        config_path,
        {
            "policy": {"default_user_agent": "test-agent"},
            "companies": {
                "MSFT": {
                    "cik": "0000789019",
                    "forms": ["10-Q", "8-K"],
                    "review_relevant_forms": ["10-Q"],
                    "last_reviewed_at": "2026-04-01",
                }
            },
        },
    )

    def fake_fetch(url, headers):
        assert url.endswith("CIK0000789019.json")
        assert headers["User-Agent"] == "test-agent"
        return {
            "filings": {
                "recent": {
                    "form": ["8-K", "10-Q", "10-K"],
                    "accessionNumber": [
                        "0000789019-26-000001",
                        "0000789019-26-000002",
                        "0000789019-25-000099",
                    ],
                    "filingDate": ["2026-05-02", "2026-04-24", "2025-07-30"],
                    "reportDate": ["2026-05-02", "2026-03-31", "2025-06-30"],
                    "primaryDocument": ["msft-8k.htm", "msft-10q.htm", "msft-10k.htm"],
                    "primaryDocDescription": ["8-K", "10-Q", "10-K"],
                }
            }
        }

    payload = build_sec_filings(
        config_path=config_path,
        output_path=output_path,
        generated_output_path=None,
        fetch_json=fake_fetch,
        now=datetime(2026, 5, 24, tzinfo=UTC),
    )

    company = payload["companies"][0]
    assert payload["summary"]["healthy_company_count"] == 1
    assert payload["summary"]["review_required_count"] == 1
    assert company["latest_relevant_filing"]["form"] == "10-Q"
    assert company["latest_relevant_filing"]["url"].endswith("/000078901926000002/msft-10q.htm")
    assert company["review_required"] is True
    assert output_path.exists()
