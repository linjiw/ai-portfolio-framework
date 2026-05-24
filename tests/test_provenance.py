from ai_portfolio_framework.provenance import build_provenance_coverage


def test_provenance_coverage_counts_evidence_ids_and_claim_links(tmp_path) -> None:
    research_data_path = tmp_path / "research-data.js"
    research_data_path.write_text(
        """
        window.AI_FRAMEWORK_DATA = {
          holdings: [
            {
              ticker: "MSFT",
              evidence: [
                {
                  id: "msft-evidence-agent",
                  text: "Agent governance surface.",
                  materiality: "high",
                  claim_ids: ["msft-claim"],
                  metric_ids: ["agent_governance_evidence"]
                },
                "Legacy evidence without stable ID."
              ],
              risks: []
            },
            {
              ticker: "CEG",
              evidence: [
                {
                  id: "ceg-evidence-pjm",
                  text: "PJM timing risk.",
                  materiality: "high",
                  claim_ids: ["ceg-claim"],
                  metric_ids: ["pjm_interconnection"]
                }
              ],
              risks: []
            }
          ],
          claims: [
            { claim_id: "msft-claim", source_id: "msft-source", entity: "MSFT" },
            { claim_id: "ceg-claim", source_id: "ceg-source", entity: "CEG" }
          ],
          sources: {
            "msft-source": { label: "Microsoft source", url: "https://example.com/msft" },
            "ceg-source": { label: "Reuters via Investing.com", url: "https://example.com/ceg" }
          }
        };
        """,
        encoding="utf-8",
    )

    payload = build_provenance_coverage(
        research_data_path=research_data_path,
        evidence_log=[
            {
                "ticker": "CEG",
                "metric_id": "pjm_interconnection",
                "source_ids": ["ceg-source"],
                "claim_ids": ["ceg-claim"],
            }
        ],
    )

    summary = payload["summary"]
    assert summary["materialEvidenceBullets"] == 3
    assert summary["evidenceIdCount"] == 2
    assert summary["highMaterialityEvidenceIdCount"] == 2
    assert summary["claimLinkedEvidenceBullets"] == 3
    assert summary["coverageRatio"] == 1.0
    assert payload["evidenceObjectsByHolding"]["MSFT"][0]["id"] == "msft-evidence-agent"
    assert payload["weakSources"][0]["source_id"] == "ceg-source"
