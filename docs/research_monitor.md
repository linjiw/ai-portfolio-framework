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
data/decision_log.yml
data/evidence_log.yml
data/thesis_changelog.yml
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

`data/decision_log.yml`
: Human review decisions. The monitor includes recent decisions in the generated
  JSON, but it never changes weights or conviction automatically.

`data/evidence_log.yml`
: Human-reviewed evidence events. These entries drive metric `evidence_state`
  fields in generated monitor JSON.

`data/thesis_changelog.yml`
: Thesis wording and evidence-boundary changes. This keeps thesis edits
  separate from portfolio decisions.

## Outputs

```text
site/research-monitor-data.json
site/provenance-coverage.json
data/generated/dashboard_data.json
data/generated/provenance_coverage.json
```

The website reads `site/research-monitor-data.json` from the same static Pages
artifact as the portfolio tracker.

## Tier 0.5 State

The monitor now treats source health as a taxonomy rather than a single issue
count:

```text
healthy
manual_expected
planned
stale
broken
```

Only `stale` and `broken` count as source issues. `manual_expected` and
`planned` are transparency states.

Each holding can define a `next_action`:

```yaml
next_action:
  type: evidence_check
  priority: high
  due: 2026-08-22
  question: Look for evidence of production write-permission adoption.
  success_condition: Official disclosure, customer case study, or product documentation shows governed production actions.
```

Generated `reviewQueue` entries come from these next actions plus any alerts
that require human review.

Metric records derive evidence state from `data/evidence_log.yml`. If a metric
has no evidence entry yet, the generator emits:

```json
{
  "state": "unknown",
  "confidence": "unknown",
  "last_evidence_date": null
}
```

The review queue is scored deterministically from priority, due-date urgency,
alert severity, evidence state, and framework bottleneck relevance. The score is
only a queue-ordering tool; it is not a portfolio action.

Provenance coverage is generated separately. It counts material evidence bullets
in `site/research-data.js`, claim-linked coverage, evidence-log source linkage,
and weak-source records that need stronger primary-source support.

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
