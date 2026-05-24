"""SEC EDGAR filing-event ingestion for the research monitor."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections.abc import Callable
from datetime import UTC, date, datetime
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

SEC_COMPANIES_CONFIG_PATH = CONFIG_DIR / "sec_companies.yml"
FILING_REVIEW_LOG_PATH = DATA_DIR / "filing_review_log.yml"
GENERATED_SEC_FILINGS_PATH = GENERATED_DATA_DIR / "sec_filings.json"
SITE_SEC_FILINGS_PATH = SITE_DIR / "sec-filings.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
OPEN_DISPOSITIONS = {"not_reviewed", ""}
CLOSED_DISPOSITIONS = {
    "no_thesis_change",
    "evidence_update",
    "bear_case_update",
    "falsifier_watch",
    "thesis_revision",
    "valuation_review",
}
VALID_DISPOSITIONS = OPEN_DISPOSITIONS | CLOSED_DISPOSITIONS

JsonFetcher = Callable[[str, dict[str, str]], dict[str, Any]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SEC filing events for configured holdings.")
    parser.add_argument("--config", type=Path, default=SEC_COMPANIES_CONFIG_PATH)
    parser.add_argument("--review-log", type=Path, default=FILING_REVIEW_LOG_PATH)
    parser.add_argument("--output", type=Path, default=SITE_SEC_FILINGS_PATH)
    parser.add_argument("--generated-output", type=Path, default=GENERATED_SEC_FILINGS_PATH)
    args = parser.parse_args()

    payload = build_sec_filings(
        config_path=args.config,
        filing_review_log_path=args.review_log,
        output_path=args.output,
        generated_output_path=args.generated_output,
    )
    summary = payload["summary"]
    print(
        "Fetched SEC filings: "
        f"companies={summary['company_count']} healthy={summary['healthy_company_count']} "
        f"review_required={summary['review_required_count']}"
    )


def build_sec_filings(
    *,
    config_path: Path = SEC_COMPANIES_CONFIG_PATH,
    filing_review_log_path: Path = FILING_REVIEW_LOG_PATH,
    output_path: Path | None = SITE_SEC_FILINGS_PATH,
    generated_output_path: Path | None = GENERATED_SEC_FILINGS_PATH,
    fetch_json: JsonFetcher | None = None,
    now: datetime | None = None,
    request_pause_seconds: float = 0.12,
) -> dict[str, Any]:
    """Build a JSON filing-event snapshot from SEC submissions APIs."""

    ensure_directories()
    config = load_yaml(config_path)
    review_log = load_yaml_list(filing_review_log_path)
    review_index = filing_review_index(review_log)
    fetched_at = (now or datetime.now(UTC)).replace(microsecond=0)
    headers = request_headers(config)
    fetcher = fetch_json or fetch_json_url

    companies = []
    for ticker, company_config in config.get("companies", {}).items():
        companies.append(
            build_company_filings(
                ticker=str(ticker),
                company_config=company_config,
                fetcher=fetcher,
                headers=headers,
                fetched_at=fetched_at,
                review_index=review_index,
            )
        )
        if fetch_json is None and request_pause_seconds > 0:
            time.sleep(request_pause_seconds)

    summary = summarize_companies(companies)
    payload = {
        "schemaVersion": 1,
        "generatedAtUtc": fetched_at.isoformat().replace("+00:00", "Z"),
        "source": "sec_edgar",
        "policy": config.get("policy", {}),
        "summary": summary,
        "companies": companies,
        "nonSecHoldings": config.get("non_sec_holdings", {}),
        "filingReviewLog": review_log,
    }
    if output_path:
        write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    return payload


def build_company_filings(
    *,
    ticker: str,
    company_config: dict[str, Any],
    fetcher: JsonFetcher,
    headers: dict[str, str],
    fetched_at: datetime,
    review_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cik = normalize_cik(company_config["cik"])
    forms = {str(form) for form in company_config.get("forms", [])}
    review_forms = {str(form) for form in company_config.get("review_relevant_forms", forms)}
    last_reviewed_at = parse_date(company_config.get("last_reviewed_at"))
    url = SEC_SUBMISSIONS_URL.format(cik=cik)

    try:
        raw = fetcher(url, headers)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "ticker": ticker,
            "cik": cik,
            "source": "sec_edgar",
            "status": "stale",
            "fetched_at_utc": fetched_at.isoformat().replace("+00:00", "Z"),
            "latest_filings": [],
            "latest_relevant_filing": None,
            "review_required": False,
            "reason": f"SEC submissions fetch failed: {type(exc).__name__}",
        }

    recent = raw.get("filings", {}).get("recent", {})
    filings = recent_filings(
        ticker=ticker,
        cik=cik,
        recent=recent,
        accepted_forms=forms,
        limit=8,
    )
    latest_relevant = next((filing for filing in filings if filing["form"] in review_forms), None)
    latest_review = review_for_filing(latest_relevant, review_index)
    if latest_relevant:
        latest_relevant["review_disposition"] = (
            latest_review.get("disposition", "not_reviewed") if latest_review else "not_reviewed"
        )
        latest_relevant["review_id"] = latest_review.get("review_id") if latest_review else None
        latest_relevant["reviewed_at"] = latest_review.get("reviewed_at") if latest_review else None
        latest_relevant["review_summary"] = latest_review.get("summary") if latest_review else None
    review_required = is_review_required(latest_relevant, last_reviewed_at, latest_review)
    reason = ""
    if review_required and latest_relevant:
        reason = "Latest relevant SEC filing is newer than last reviewed date."
    elif latest_review and latest_relevant:
        reason = (
            "Latest relevant SEC filing has human review disposition: "
            f"{latest_review.get('disposition')}."
        )
    elif latest_relevant:
        reason = "Latest relevant SEC filing is not newer than last reviewed date."
    else:
        reason = "No configured SEC form found in recent filings."

    return {
        "ticker": ticker,
        "cik": cik,
        "source": "sec_edgar",
        "status": "healthy",
        "fetched_at_utc": fetched_at.isoformat().replace("+00:00", "Z"),
        "last_reviewed_at": last_reviewed_at.isoformat() if last_reviewed_at else None,
        "review_relevant_forms": sorted(review_forms),
        "latest_filings": filings,
        "latest_relevant_filing": latest_relevant,
        "review_required": review_required,
        "reason": reason,
    }


def recent_filings(
    *,
    ticker: str,
    cik: str,
    recent: dict[str, list[Any]],
    accepted_forms: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_documents = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])
    rows = []
    for index, form in enumerate(forms):
        form = str(form)
        if accepted_forms and form not in accepted_forms:
            continue
        accession = str(value_at(accessions, index))
        filing_date = str(value_at(filing_dates, index))
        primary_document = str(value_at(primary_documents, index))
        rows.append(
            {
                "source_id": source_id(ticker, form, filing_date, accession),
                "ticker": ticker,
                "form": form,
                "filing_date": filing_date,
                "report_date": str(value_at(report_dates, index) or ""),
                "accession_number": accession,
                "primary_document": primary_document,
                "primary_doc_description": str(value_at(descriptions, index) or ""),
                "url": filing_url(cik, accession, primary_document),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def is_review_required(
    filing: dict[str, Any] | None,
    last_reviewed_at: date | None,
    review_record: dict[str, Any] | None = None,
) -> bool:
    if not filing:
        return False
    if review_record:
        disposition = str(review_record.get("disposition", "not_reviewed"))
        if disposition in CLOSED_DISPOSITIONS:
            return False
    filing_date = parse_date(filing.get("filing_date"))
    if not filing_date:
        return False
    return last_reviewed_at is None or filing_date > last_reviewed_at


def summarize_companies(companies: list[dict[str, Any]]) -> dict[str, Any]:
    healthy = sum(1 for company in companies if company.get("status") == "healthy")
    review_required = sum(1 for company in companies if company.get("review_required"))
    reviewed_current = sum(
        1
        for company in companies
        if (company.get("latest_relevant_filing") or {}).get("review_disposition")
        in CLOSED_DISPOSITIONS
    )
    failed = len(companies) - healthy
    return {
        "company_count": len(companies),
        "healthy_company_count": healthy,
        "failed_company_count": failed,
        "review_required_count": review_required,
        "current_filing_reviewed_count": reviewed_current,
        "latest_filing_count": sum(len(company.get("latest_filings", [])) for company in companies),
    }


def fetch_json_url(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def request_headers(config: dict[str, Any]) -> dict[str, str]:
    policy = config.get("policy", {})
    env_name = str(policy.get("user_agent_env", "SEC_USER_AGENT"))
    user_agent = os.environ.get(env_name) or policy.get("default_user_agent")
    return {
        "User-Agent": str(user_agent),
        "Accept": "application/json",
    }


def filing_url(cik: str, accession: str, primary_document: str) -> str:
    clean_accession = accession.replace("-", "")
    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{int(cik)}/{clean_accession}/{primary_document}"
    )


def source_id(ticker: str, form: str, filing_date: str, accession: str) -> str:
    clean_form = form.lower().replace("-", "").replace("/", "")
    clean_accession = accession.replace("-", "")[-8:]
    return f"sec-{ticker.lower()}-{filing_date}-{clean_form}-{clean_accession}"


def normalize_cik(value: str | int) -> str:
    return str(value).zfill(10)


def filing_review_index(review_log: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in review_log:
        disposition = str(record.get("disposition", "not_reviewed"))
        if disposition not in VALID_DISPOSITIONS:
            raise ValueError(f"Invalid filing review disposition: {disposition}")
        for key in filing_review_keys(record):
            index[key] = record
    return index


def review_for_filing(
    filing: dict[str, Any] | None,
    review_index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if not filing:
        return None
    for key in filing_review_keys(filing):
        if key in review_index:
            return review_index[key]
    return None


def filing_review_keys(record: dict[str, Any]) -> list[str]:
    keys = []
    source = record.get("source_id")
    accession = record.get("accession_number")
    ticker = record.get("ticker")
    form = record.get("form")
    filing_date = record.get("filing_date")
    if source:
        keys.append(f"source:{source}")
    if accession:
        keys.append(f"accession:{accession}")
    if ticker and form and filing_date:
        keys.append(f"triple:{ticker}:{form}:{filing_date}")
    return keys


def value_at(values: list[Any], index: int) -> Any:
    return values[index] if index < len(values) else ""


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value))


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing SEC company config: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_yaml_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(payload, list):
        raise ValueError(f"Expected list in {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
