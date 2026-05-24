"""Source link-health snapshots for the research monitor."""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from ai_portfolio_framework.config import (
    CONFIG_DIR,
    DATA_DIR,
    GENERATED_DATA_DIR,
    SITE_DIR,
    ensure_directories,
)
from ai_portfolio_framework.research_monitor import source_labels_by_id

RESEARCH_DATA_PATH = SITE_DIR / "research-data.js"
SOURCE_RULES_CONFIG_PATH = CONFIG_DIR / "source_rules.yml"
GENERATED_LINK_HEALTH_PATH = GENERATED_DATA_DIR / "link_health_snapshot.json"
SITE_LINK_HEALTH_PATH = SITE_DIR / "link-health.json"
LINK_HEALTH_HISTORY_PATH = DATA_DIR / "link_health_history.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check research source link health.")
    parser.add_argument("--research-data", type=Path, default=RESEARCH_DATA_PATH)
    parser.add_argument("--rules", type=Path, default=SOURCE_RULES_CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=SITE_LINK_HEALTH_PATH)
    parser.add_argument("--generated-output", type=Path, default=GENERATED_LINK_HEALTH_PATH)
    parser.add_argument("--history", type=Path, default=LINK_HEALTH_HISTORY_PATH)
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()

    payload = build_link_health_snapshot(
        research_data_path=args.research_data,
        rules_config_path=args.rules,
        output_path=args.output,
        generated_output_path=args.generated_output,
        history_path=None if args.no_history else args.history,
    )
    summary = payload["summary"]
    print(
        "Checked source links: "
        f"total={summary['total']} ok={summary['ok']} redirected={summary['redirected']} "
        f"forbidden={summary['forbidden']} timeout={summary['timeout']} "
        f"not_found={summary['not_found']} broken={summary['broken']}"
    )


def build_link_health_snapshot(
    *,
    research_data_path: Path = RESEARCH_DATA_PATH,
    rules_config_path: Path = SOURCE_RULES_CONFIG_PATH,
    output_path: Path | None = SITE_LINK_HEALTH_PATH,
    generated_output_path: Path | None = GENERATED_LINK_HEALTH_PATH,
    history_path: Path | None = LINK_HEALTH_HISTORY_PATH,
    now: datetime | None = None,
    checker: Any | None = None,
) -> dict[str, Any]:
    """Check source URLs and persist a link-health snapshot."""

    ensure_directories()
    checked_at = (now or datetime.now(UTC)).replace(microsecond=0)
    rules = load_yaml_optional(rules_config_path).get("link_health", {})
    timeout = float(rules.get("timeout_seconds", 12))
    sources = parse_sources(research_data_path)
    primary_support_required = {
        str(item["source_id"]): item.get("reason", "")
        for item in rules.get("primary_support_required", [])
        if item.get("source_id")
    }
    weak_terms = tuple(str(term).lower() for term in rules.get("weak_source_terms", []))
    check = checker or check_source_url

    rows = []
    with ThreadPoolExecutor(max_workers=min(8, max(len(sources), 1))) as executor:
        futures = {
            executor.submit(
                build_source_record,
                source=source,
                checked_at=checked_at,
                timeout=timeout,
                weak_terms=weak_terms,
                primary_support_required=primary_support_required,
                checker=check,
            ): source
            for source in sources
        }
        for future in as_completed(futures):
            rows.append(future.result())

    rows = sorted(rows, key=lambda row: row["source_id"])
    payload = {
        "schemaVersion": 1,
        "checkedAtUtc": checked_at.isoformat().replace("+00:00", "Z"),
        "summary": summarize_sources(rows),
        "policy": {
            "forbidden": rules.get("status_policy", {}).get("forbidden", ""),
            "timeout": rules.get("status_policy", {}).get("timeout", ""),
            "not_found": rules.get("status_policy", {}).get("not_found", ""),
        },
        "sources": rows,
    }
    if output_path:
        write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    if history_path:
        append_history(history_path, payload, history_limit=int(rules.get("history_limit", 120)))
    return payload


def build_source_record(
    *,
    source: dict[str, str],
    checked_at: datetime,
    timeout: float,
    weak_terms: tuple[str, ...],
    primary_support_required: dict[str, str],
    checker: Any,
) -> dict[str, Any]:
    result = checker(source["url"], timeout)
    explicit_reason = primary_support_required.get(source["source_id"])
    weak_by_label = any(
        term in f"{source['source_id']} {source['label']}".lower() for term in weak_terms
    )
    source_quality_status = "weak_source" if explicit_reason or weak_by_label else "accepted"
    quality_reason = explicit_reason or (
        "Secondary or syndicated source" if weak_by_label else ""
    )
    return {
        "source_id": source["source_id"],
        "label": source["label"],
        "url": source["url"],
        "link_status": result["link_status"],
        "http_status": result.get("http_status"),
        "final_url": result.get("final_url"),
        "source_quality_status": source_quality_status,
        "primary_support_required": source_quality_status == "weak_source",
        "quality_reason": quality_reason,
        "last_checked_at": checked_at.isoformat().replace("+00:00", "Z"),
    }


def check_source_url(url: str, timeout: float) -> dict[str, Any]:
    headers = {
        "User-Agent": "ai-portfolio-framework link-health checker",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        return request_url(url, timeout=timeout, headers=headers, method="HEAD")
    except HTTPError as exc:
        if exc.code in {403, 405}:
            try:
                return request_url(url, timeout=timeout, headers=headers, method="GET")
            except HTTPError as get_exc:
                return status_from_http_error(get_exc, url)
            except TimeoutError:
                return {"link_status": "timeout", "http_status": None, "final_url": url}
            except URLError as get_exc:
                return status_from_url_error(get_exc, url)
        return status_from_http_error(exc, url)
    except TimeoutError:
        return {"link_status": "timeout", "http_status": None, "final_url": url}
    except URLError as exc:
        return status_from_url_error(exc, url)


def request_url(
    url: str,
    *,
    timeout: float,
    headers: dict[str, str],
    method: str,
) -> dict[str, Any]:
    request = Request(url, headers=headers, method=method)
    if method == "GET":
        request.add_header("Range", "bytes=0-2048")
    with urlopen(request, timeout=timeout) as response:
        status = int(response.status)
        final_url = response.geturl()
        if final_url.rstrip("/") != url.rstrip("/"):
            link_status = "redirected"
        elif 200 <= status < 400:
            link_status = "ok"
        else:
            link_status = status_from_code(status)
        return {"link_status": link_status, "http_status": status, "final_url": final_url}


def status_from_http_error(exc: HTTPError, url: str) -> dict[str, Any]:
    return {"link_status": status_from_code(exc.code), "http_status": exc.code, "final_url": url}


def status_from_url_error(exc: URLError, url: str) -> dict[str, Any]:
    reason = str(exc.reason).lower()
    if "timed out" in reason or "timeout" in reason:
        return {"link_status": "timeout", "http_status": None, "final_url": url}
    return {"link_status": "error", "http_status": None, "final_url": url}


def status_from_code(status: int) -> str:
    if status == 403:
        return "forbidden"
    if status == 404:
        return "not_found"
    if 300 <= status < 400:
        return "redirected"
    if 200 <= status < 300:
        return "ok"
    return "error"


def summarize_sources(rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(rows),
        "ok": 0,
        "redirected": 0,
        "timeout": 0,
        "forbidden": 0,
        "not_found": 0,
        "error": 0,
        "broken": 0,
        "weak_source": 0,
    }
    for row in rows:
        status = row.get("link_status", "error")
        if status in summary:
            summary[status] += 1
        if status in {"not_found", "error"}:
            summary["broken"] += 1
        if row.get("source_quality_status") == "weak_source":
            summary["weak_source"] += 1
    return summary


def parse_sources(research_data_path: Path) -> list[dict[str, str]]:
    text = research_data_path.read_text(encoding="utf-8")
    labels = source_labels_by_id(text)
    urls = source_urls_by_id(text)
    return [
        {"source_id": source_id, "label": label, "url": urls[source_id]}
        for source_id, label in labels.items()
        if urls.get(source_id)
    ]


def source_urls_by_id(text: str) -> dict[str, str]:
    urls: dict[str, str] = {}
    pattern = (
        r'"([^"]+)": \{\s*label: "(?:\\.|[^"\\])*",\s*url: "((?:\\.|[^"\\])*)"'
    )
    for source_id, url in re.findall(pattern, text):
        urls[source_id] = decode_js_string(url)
    return urls


def decode_js_string(value: str) -> str:
    return value.replace('\\"', '"').replace("\\/", "/")


def append_history(path: Path, payload: dict[str, Any], *, history_limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "checkedAtUtc": payload["checkedAtUtc"],
        "summary": payload["summary"],
        "weak_source_ids": [
            row["source_id"]
            for row in payload["sources"]
            if row.get("source_quality_status") == "weak_source"
        ],
        "broken_source_ids": [
            row["source_id"]
            for row in payload["sources"]
            if row.get("link_status") in {"not_found", "error"}
        ],
    }
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [line for line in existing if line.strip()]
    lines.append(json.dumps(record, sort_keys=True))
    if history_limit > 0:
        lines = lines[-history_limit:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_yaml_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
