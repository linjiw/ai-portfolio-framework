from datetime import UTC, datetime

import yaml

from ai_portfolio_framework.link_health import build_link_health_snapshot


def write_yaml(path, payload) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_build_link_health_separates_weak_source_from_broken_link(tmp_path) -> None:
    research_data_path = tmp_path / "research-data.js"
    rules_path = tmp_path / "rules.yml"
    output_path = tmp_path / "link-health.json"
    history_path = tmp_path / "link-history.jsonl"

    research_data_path.write_text(
        """
        window.AI_FRAMEWORK_DATA = {
          sources: {
            "primary-source": { label: "Primary Source", url: "https://example.com/ok" },
            "ceg-tmi-pjm": { label: "Reuters via Investing.com", url: "https://example.com/weak" },
            "broken-source": { label: "Broken Source", url: "https://example.com/missing" }
          }
        };
        """,
        encoding="utf-8",
    )
    write_yaml(
        rules_path,
        {
            "link_health": {
                "timeout_seconds": 1,
                "history_limit": 10,
                "weak_source_terms": ["reuters", "investing.com"],
                "primary_support_required": [
                    {"source_id": "ceg-tmi-pjm", "reason": "Needs primary source"}
                ],
                "source_maintenance": {
                    "ceg-tmi-pjm": {
                        "quality": "weak_source",
                        "fallback_required": True,
                        "preferred_primary_types": ["PJM", "company_filing"],
                        "archive_url": None,
                        "replacement_source_id": None,
                    },
                    "primary-source": {
                        "quality": "accepted",
                        "archive_recommended": True,
                        "fallback_required": False,
                    },
                },
            }
        },
    )

    def fake_checker(url, timeout):
        if url.endswith("/missing"):
            return {"link_status": "not_found", "http_status": 404, "final_url": url}
        return {"link_status": "ok", "http_status": 200, "final_url": url}

    payload = build_link_health_snapshot(
        research_data_path=research_data_path,
        rules_config_path=rules_path,
        output_path=output_path,
        generated_output_path=None,
        history_path=history_path,
        now=datetime(2026, 5, 24, tzinfo=UTC),
        checker=fake_checker,
    )

    rows = {row["source_id"]: row for row in payload["sources"]}
    assert payload["summary"]["total"] == 3
    assert payload["summary"]["weak_source"] == 1
    assert payload["summary"]["broken"] == 1
    assert rows["ceg-tmi-pjm"]["link_status"] == "ok"
    assert rows["ceg-tmi-pjm"]["source_quality_status"] == "weak_source"
    assert rows["ceg-tmi-pjm"]["fallback_required"] is True
    assert rows["ceg-tmi-pjm"]["preferred_primary_types"] == ["PJM", "company_filing"]
    assert rows["primary-source"]["archive_recommended"] is True
    assert rows["broken-source"]["source_quality_status"] == "accepted"
    assert rows["broken-source"]["link_status"] == "not_found"
    assert output_path.exists()
    assert history_path.exists()
