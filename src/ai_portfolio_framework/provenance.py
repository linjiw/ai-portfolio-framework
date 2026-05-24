"""Claim and evidence provenance helpers for the static research dataset."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def build_provenance_coverage(
    *,
    research_data_path: Path,
    evidence_log: list[dict[str, Any]],
) -> dict[str, Any]:
    text = research_data_path.read_text(encoding="utf-8") if research_data_path.exists() else ""
    evidence_counts = holding_evidence_counts(text)
    evidence_objects = evidence_objects_by_ticker(text)
    claim_entities = claim_entities_by_ticker(text)
    claim_source_ids = claim_source_ids_by_ticker(text)
    source_labels = source_labels_by_id(text)
    material_evidence_bullets = sum(evidence_counts.values())
    direct_claim_linked = sum(
        1
        for objects in evidence_objects.values()
        for item in objects
        if item.get("claim_ids")
    )
    legacy_claim_linked = sum(
        min(
            legacy_evidence_count(
                evidence_counts.get(ticker, 0),
                len(evidence_objects.get(ticker, [])),
            ),
            len(claim_entities.get(ticker, [])),
        )
        for ticker in evidence_counts
    )
    claim_linked_bullets = min(material_evidence_bullets, direct_claim_linked + legacy_claim_linked)
    evidence_log_links = sum(
        1 for item in evidence_log if item.get("source_ids") or item.get("claim_ids")
    )
    weak_sources = build_weak_source_records(
        claim_source_ids=claim_source_ids,
        source_labels=source_labels,
        evidence_log=evidence_log,
    )
    coverage_ratio = (
        round(claim_linked_bullets / material_evidence_bullets, 4)
        if material_evidence_bullets
        else 0.0
    )
    evidence_id_count = sum(len(objects) for objects in evidence_objects.values())
    high_materiality_evidence_ids = sum(
        1
        for objects in evidence_objects.values()
        for item in objects
        if item.get("materiality") == "high"
    )
    return {
        "schemaVersion": 1,
        "generatedAtUtc": utc_iso(),
        "summary": {
            "materialEvidenceBullets": material_evidence_bullets,
            "claimLinkedEvidenceBullets": claim_linked_bullets,
            "coverageRatio": coverage_ratio,
            "evidenceIdCount": evidence_id_count,
            "highMaterialityEvidenceIdCount": high_materiality_evidence_ids,
            "evidenceLogEntries": len(evidence_log),
            "evidenceLogEntriesWithSourceOrClaim": evidence_log_links,
            "weakSourceCount": len(weak_sources),
        },
        "holdingsMissingClaimCoverage": missing_claim_coverage(evidence_counts, claim_entities),
        "holdingEvidenceCounts": evidence_counts,
        "claimCountsByHolding": {
            ticker: len(claim_entities.get(ticker, [])) for ticker in sorted(evidence_counts)
        },
        "evidenceObjectsByHolding": evidence_objects,
        "weakSources": weak_sources,
    }


def holding_evidence_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ticker, evidence_block in holding_evidence_blocks(text).items():
        objects = evidence_objects_from_block(evidence_block)
        object_text_spans = [item["span"] for item in objects]
        legacy_block = remove_spans(evidence_block, object_text_spans)
        legacy_string_count = len(re.findall(r'"(?:\\.|[^"\\])*"', legacy_block))
        counts[ticker] = len(objects) + legacy_string_count
    return counts


def evidence_objects_by_ticker(text: str) -> dict[str, list[dict[str, Any]]]:
    return {
        ticker: [
            {
                "id": item["id"],
                "text": item.get("text", ""),
                "materiality": item.get("materiality", ""),
                "claim_ids": item.get("claim_ids", []),
                "metric_ids": item.get("metric_ids", []),
            }
            for item in evidence_objects_from_block(block)
        ]
        for ticker, block in holding_evidence_blocks(text).items()
    }


def holding_evidence_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    pattern = re.compile(r'\{\s*ticker: "([^"]+)".*?evidence: \[(.*?)\]\s*,\s*risks:', re.S)
    for ticker, evidence_block in pattern.findall(text):
        blocks[ticker] = evidence_block
    return blocks


def evidence_objects_from_block(block: str) -> list[dict[str, Any]]:
    objects = []
    pattern = re.compile(r'\{\s*id: "([^"]+)"(.*?)\n\s*\}', re.S)
    for match in pattern.finditer(block):
        body = match.group(2)
        objects.append(
            {
                "id": match.group(1),
                "text": field_string(body, "text"),
                "materiality": field_string(body, "materiality"),
                "claim_ids": field_array(body, "claim_ids"),
                "metric_ids": field_array(body, "metric_ids"),
                "span": match.span(),
            }
        )
    return objects


def field_string(body: str, field: str) -> str:
    match = re.search(rf'{field}: "((?:\\.|[^"\\])*)"', body)
    return decode_js_string(match.group(1)) if match else ""


def field_array(body: str, field: str) -> list[str]:
    match = re.search(rf"{field}: \[(.*?)\]", body, re.S)
    if not match:
        return []
    return [
        decode_js_string(value)
        for value in re.findall(r'"((?:\\.|[^"\\])*)"', match.group(1))
    ]


def remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    result = []
    cursor = 0
    for start, end in sorted(spans):
        result.append(text[cursor:start])
        cursor = end
    result.append(text[cursor:])
    return "".join(result)


def legacy_evidence_count(total_count: int, object_count: int) -> int:
    return max(0, total_count - object_count)


def claim_entities_by_ticker(text: str) -> dict[str, list[str]]:
    entities: dict[str, list[str]] = {}
    pattern = re.compile(r'claim_id: "([^"]+)".*?entity: "([^"]+)"', re.S)
    for claim_id, entity in pattern.findall(text):
        entities.setdefault(entity, []).append(claim_id)
    return entities


def claim_source_ids_by_ticker(text: str) -> dict[str, list[str]]:
    source_ids: dict[str, list[str]] = {}
    pattern = re.compile(
        r'claim_id: "([^"]+)".*?source_id: "([^"]+)".*?entity: "([^"]+)"',
        re.S,
    )
    for _claim_id, source_id, entity in pattern.findall(text):
        source_ids.setdefault(entity, []).append(source_id)
    return source_ids


def source_labels_by_id(text: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    pattern = re.compile(r'"([^"]+)": \{\s*label: "([^"]+)"', re.S)
    for source_id, label in pattern.findall(text):
        labels[source_id] = decode_js_string(label)
    return labels


def source_urls_by_id(text: str) -> dict[str, str]:
    urls: dict[str, str] = {}
    pattern = (
        r'"([^"]+)": \{\s*label: "(?:\\.|[^"\\])*",\s*url: "((?:\\.|[^"\\])*)"'
    )
    for source_id, url in re.findall(pattern, text):
        urls[source_id] = decode_js_string(url)
    return urls


def missing_claim_coverage(
    evidence_counts: dict[str, int],
    claim_entities: dict[str, list[str]],
) -> list[str]:
    return [
        ticker
        for ticker, count in evidence_counts.items()
        if count and not claim_entities.get(ticker)
    ]


def build_weak_source_records(
    *,
    claim_source_ids: dict[str, list[str]],
    source_labels: dict[str, str],
    evidence_log: list[dict[str, Any]],
) -> list[dict[str, str]]:
    weak = []
    seen = set()
    weak_terms = ("reuters", "investing.com", "secondary")
    for ticker, source_ids in sorted(claim_source_ids.items()):
        for source_id in source_ids:
            label = source_labels.get(source_id, "")
            if any(term in label.lower() for term in weak_terms):
                weak.append(weak_source_record(ticker, source_id, label))
                seen.add((ticker, source_id))
    for item in evidence_log:
        ticker = str(item.get("ticker", ""))
        for source_id in item.get("source_ids", []):
            label = source_labels.get(source_id, "")
            key = (ticker, source_id)
            if key in seen:
                continue
            if any(term in label.lower() for term in weak_terms):
                weak.append(weak_source_record(ticker, source_id, label))
                seen.add(key)
    return weak


def weak_source_record(ticker: str, source_id: str, label: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "source_id": source_id,
        "reason": f"Secondary or syndicated source: {label}",
        "recommended_action": (
            "Supplement with primary filing, company, regulatory, or operator data."
        ),
    }


def decode_js_string(value: str) -> str:
    return value.replace('\\"', '"').replace("\\/", "/")


def utc_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
