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

The monitor reads structured YAML files:

```text
config/holdings.yml
config/metrics_catalog.yml
config/alert_rules.yml
config/sources.yml
config/source_rules.yml
config/sec_companies.yml
config/risk_factors.yml
config/falsifier_thresholds.yml
config/bear_cases.yml
config/valuation_bands.yml
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

`source_rules.yml`
: Link-health rules that separate link availability from evidence quality.
  Forbidden and timeout states are brittle-source signals, not claim failures.

`sec_companies.yml`
: CIKs, tracked SEC forms, review-relevant forms, and last-reviewed dates for
  US-listed holdings and ADRs.

`risk_factors.yml`
: Portfolio-level risk overlays that cut across thesis buckets. The first
  overlay tracks hyperscaler AI capex exposure, separating direct, lagged, and
  hedge target weights.

`falsifier_thresholds.yml`
: Operational review thresholds for each falsifier. These are human-review
  triggers only; they do not execute trades or change weights automatically.

`bear_cases.yml`
: One explicit opposing argument per holding, including what would strengthen
  or weaken that bear case.

`valuation_bands.yml`
: Valuation review bands. These make the valuation gate inspectable without
  turning it into an automatic rebalance rule.

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
site/sec-filings.json
site/link-health.json
data/generated/dashboard_data.json
data/generated/provenance_coverage.json
data/generated/sec_filings.json
data/generated/link_health_snapshot.json
data/link_health_history.jsonl
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

## Tier 0.8 State

The monitor now adds research and decision-process hardening without changing
holdings or target weights.

### Risk overlay

The primary overlay is `hyperscaler_capex_cycle`. It intentionally ignores the
existing thesis buckets and asks a simpler risk question:

```text
How much target exposure depends directly on hyperscaler AI capex durability?
```

The current framework maps direct, lagged, and hedge groups. A direct exposure
above the configured threshold creates a framework-risk review state, not a
portfolio action.

### Operational falsifiers

Every holding now has a threshold record with:

```yaml
ticker: MSFT
metric_id: production_write_permission
cadence: semiannual
source: official product docs, customer case studies, security disclosures, earnings transcripts
threshold: Fewer than 2 independent primary-source examples of governed production write actions by 2027-12-31.
decision_rule: If threshold is missed, open thesis_revision review within 30 days and keep Trust bottleneck flagged.
```

The important rule is that a threshold breach requires a decision-log entry. It
does not imply an automatic sell, trim, add, or weight rewrite.

### Bear-case tracking

Each holding has a structured bear case with `strengthens_if` and `weakens_if`
fields. This keeps quarterly review from becoming only confirming-evidence
collection.

### Valuation gates

Valuation bands are stored as review ranges and remain `not_evaluated` until a
separate valuation snapshot is wired in. The monitor can show that the valuation
gate exists and is coverage-complete, while still preventing any automatic
portfolio action.

## Tier 1.0 State

The monitor now starts free-data ingestion without changing the LLM boundary.

### SEC filing feed

`scripts/fetch_sec_filings.py` reads `config/sec_companies.yml`, calls SEC
submissions JSON endpoints, and writes:

```text
site/sec-filings.json
data/generated/sec_filings.json
```

The request user agent can be overridden with `SEC_USER_AGENT` in CI or a local
shell. The checked-in default is only a project placeholder for the public demo.

The first version only tracks filing events:

```json
{
  "ticker": "MSFT",
  "source": "sec_edgar",
  "latest_relevant_filing": {
    "form": "10-Q",
    "filing_date": "2026-04-24",
    "accession_number": "...",
    "url": "..."
  },
  "review_required": true,
  "reason": "Latest relevant SEC filing is newer than last reviewed date."
}
```

It does not extract revenue, margin, capex, or evidence state. A new relevant
filing can enter the review queue as `filing_review`, where a human reviewer
decides whether it maps to evidence, bear-case movement, or no thesis change.

### Link-health snapshots

`scripts/check_link_health.py` checks source URLs from `site/research-data.js`
and writes:

```text
site/link-health.json
data/generated/link_health_snapshot.json
data/link_health_history.jsonl
```

The monitor separates two concepts:

```text
weak_source = source is available but evidence quality needs stronger primary support
broken_link = source URL is unavailable or errored
```

`forbidden` and `timeout` are not treated as claim failures. They indicate a
brittle, bot-blocked, or slow source that may need archive or primary-source
backup.

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
