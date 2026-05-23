# Research Monitor

This repo now separates the public portfolio tracker from the research-monitor
layer.

The monitor is deterministic first. It does not call an LLM and does not produce
buy or sell instructions. Its job is to keep the framework auditable:

- define what each holding is supposed to prove,
- map watch items and falsifiers to a small metric dictionary,
- run simple data and market rules,
- surface source-health gaps instead of hiding them,
- leave thesis changes and weight changes to human review.

## Configuration

The monitor reads four YAML files:

```text
config/holdings.yml
config/metrics_catalog.yml
config/alert_rules.yml
config/sources.yml
```

`holdings.yml`
: Portfolio structure, target weights, review cadence, layers, and conviction.

`metrics_catalog.yml`
: One core question per holding, plus three to four metrics, watch rule, and
  falsifier.

`alert_rules.yml`
: Deterministic checks such as stale price, missing price, weight drift, and
  portfolio drawdown.

`sources.yml`
: Source-health definitions. Automated sources are checked against timestamps;
  planned and manual feeds are intentionally visible.

## Outputs

```text
site/research-monitor-data.json
data/generated/dashboard_data.json
```

The website reads `site/research-monitor-data.json` from the same static Pages
artifact as the portfolio tracker.

## LLM Boundary

LLMs are a later phase. They should read filings, transcripts, company releases,
and official docs, then return structured draft evidence:

```json
{
  "ticker": "MSFT",
  "metric_id": "agent_governance_evidence",
  "direction": "stronger",
  "evidence": "Management discussed governed agent adoption.",
  "confidence": "medium",
  "requires_human_review": true
}
```

LLMs should not execute trades, rewrite weights, resolve falsifiers, or create
uncited claims.
