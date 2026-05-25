"""Sanitized current-position analysis for the framework site."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
import yfinance as yf

from ai_portfolio_framework.config import CONFIG_DIR, GENERATED_DATA_DIR, MANUAL_DIR, SITE_DIR
from ai_portfolio_framework.portfolio import fetch_latest_price

DEFAULT_OUTPUT_PATH = SITE_DIR / "current-positions-data.json"
DEFAULT_GENERATED_OUTPUT_PATH = GENERATED_DATA_DIR / "current_positions_analysis.json"
DEFAULT_SEED_PATH = MANUAL_DIR / "current_positions_public_seed.json"
HOLDINGS_PATH = MANUAL_DIR / "ai_framework_holdings.csv"
WATCHLIST_RULES_PATH = CONFIG_DIR / "watchlist_rules.yml"

INDEX_ETFS = {"QQQ", "SPY", "VOO", "SPMO", "TQQQ"}
DEFENSIVE_OR_HEDGE = {"GLD", "PFE", "MRK", "NVO", "LLY", "SPAXX**"}
AI_ADJACENT = {"AMZN", "ASML", "AMD", "ARM", "INTC", "LITE", "CRWV", "DRAM", "AAPL", "RKLB"}
OPTION_RE = re.compile(
    r"^-?(?P<underlying>[A-Z]+)(?P<expiry>\d{6})(?P<right>[CP])(?P<strike>\d+(?:\.\d+)?)$"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sanitized current-position analysis JSON.")
    parser.add_argument("--input", type=Path, default=None, help="Fidelity positions CSV export.")
    parser.add_argument(
        "--seed",
        type=Path,
        default=DEFAULT_SEED_PATH,
        help="Sanitized public current-position seed used when --input is omitted.",
    )
    parser.add_argument(
        "--write-seed",
        action="store_true",
        help="When importing a CSV, also write a sanitized public seed JSON.",
    )
    parser.add_argument(
        "--no-refresh-prices",
        action="store_true",
        help="Use seed marks without refreshing public market prices.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--generated-output", type=Path, default=DEFAULT_GENERATED_OUTPUT_PATH)
    parser.add_argument(
        "--skip-fib-momentum",
        action="store_true",
        help="Do not refresh the Fibonacci EMA monitor after importing positions.",
    )
    args = parser.parse_args()

    if args.input:
        payload = build_current_positions_analysis(
            input_path=args.input,
            output_path=args.output,
            generated_output_path=args.generated_output,
            seed_output_path=args.seed if args.write_seed else None,
        )
    else:
        payload = build_current_positions_from_seed(
            seed_path=args.seed,
            output_path=args.output,
            generated_output_path=args.generated_output,
            refresh_prices=not args.no_refresh_prices,
        )
    summary = payload["summary"]
    print(
        "Built current positions analysis: "
        f"positions={summary['positionCount']} total=${summary['totalValueUsd']:.2f} "
        f"framework={summary['frameworkMappedWeightPct']:.2f}% "
        f"outside={summary['outsideFrameworkWeightPct']:.2f}%"
    )
    if not args.skip_fib_momentum:
        from ai_portfolio_framework.fib_momentum import build_fib_momentum_data

        fib_payload = build_fib_momentum_data(current_positions_path=args.output)
        fib_summary = fib_payload["summary"]
        print(
            "Refreshed Fibonacci EMA monitor: "
            f"rows={fib_summary['scannedCount']} failures={fib_summary['failureCount']}"
        )


def build_current_positions_analysis(
    *,
    input_path: Path,
    output_path: Path | None = DEFAULT_OUTPUT_PATH,
    generated_output_path: Path | None = DEFAULT_GENERATED_OUTPUT_PATH,
    seed_output_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    rows = load_fidelity_positions(input_path)
    payload = build_current_positions_payload(
        rows=rows,
        source_file=input_path.name,
        downloaded_at=extract_downloaded_at(input_path),
        publication_boundary="public_sanitized_no_account_identifiers",
        output_path=output_path,
        generated_output_path=generated_output_path,
        now=now,
    )
    if seed_output_path:
        write_json(seed_output_path, seed_from_payload(payload, seed_source=input_path.name))
    return payload


def build_current_positions_from_seed(
    *,
    seed_path: Path = DEFAULT_SEED_PATH,
    output_path: Path | None = DEFAULT_OUTPUT_PATH,
    generated_output_path: Path | None = DEFAULT_GENERATED_OUTPUT_PATH,
    refresh_prices: bool = True,
    latest_prices: dict[str, dict[str, Any]] | None = None,
    option_prices: dict[str, dict[str, Any]] | None = None,
    snapshot_date: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not seed_path.exists():
        raise FileNotFoundError(f"Current-position seed not found: {seed_path}")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    rows = load_seed_positions(
        seed,
        refresh_prices=refresh_prices,
        latest_prices=latest_prices,
        option_prices=option_prices,
        snapshot_date=snapshot_date or datetime.now(UTC).date(),
    )
    return build_current_positions_payload(
        rows=rows,
        source_file=seed_path.name,
        downloaded_at=seed.get("seededFrom", {}).get("downloadedAt"),
        publication_boundary="public_sanitized_seed_no_account_identifiers",
        output_path=output_path,
        generated_output_path=generated_output_path,
        now=now,
    )


def build_current_positions_payload(
    *,
    rows: list[dict[str, Any]],
    source_file: str,
    downloaded_at: str | None,
    publication_boundary: str,
    output_path: Path | None,
    generated_output_path: Path | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    framework = load_framework_map()
    watchlist = load_watchlist_map()
    positions = [enrich_position(row, framework, watchlist) for row in rows]
    grouped = aggregate_positions(positions, framework, watchlist)
    summary = build_summary(grouped)
    payload = {
        "schemaVersion": 1,
        "generatedAtUtc": (now or datetime.now(UTC)).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "sourceFile": source_file,
        "downloadedAt": downloaded_at,
        "privacy": {
            "accountIdentifiersIncluded": False,
            "sourceAccountFieldsDropped": ["Account Number", "Account Name", "Type"],
            "publicationBoundary": publication_boundary,
        },
        "summary": summary,
        "classifications": build_classifications(grouped),
        "frameworkCoverage": build_framework_coverage(grouped, framework),
        "derivativeOverlay": build_derivative_overlay(positions),
        "reviewQueue": build_review_queue(grouped, summary),
        "positions": grouped,
    }
    if output_path:
        write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    return payload


def seed_from_payload(payload: dict[str, Any], *, seed_source: str) -> dict[str, Any]:
    rows = []
    for row in payload.get("positions") or []:
        rows.append(
            {
                "symbol": row["symbol"],
                "description": row["description"],
                "quantity": row["quantity"],
                "instrument": row["instrument"],
                "underlying": row.get("underlying"),
                "option": row.get("option"),
                "seedValueUsd": row["currentValueUsd"],
                "costBasisUsd": row["costBasisUsd"],
                "fallbackMarkUsd": fallback_mark(row),
            }
        )
    return {
        "schemaVersion": 1,
        "generatedAtUtc": utc_iso(),
        "source": "sanitized_current_positions_public_seed",
        "seededFrom": {
            "sourceFile": seed_source,
            "downloadedAt": payload.get("downloadedAt"),
        },
        "privacy": {
            "accountIdentifiersIncluded": False,
            "sourceAccountFieldsDropped": ["Account Number", "Account Name", "Account Type"],
            "publicationBoundary": "public_sanitized_no_account_identifiers",
        },
        "positions": rows,
    }


def load_fidelity_positions(input_path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(input_path, dtype=str, index_col=False)
    rows = []
    for _, raw in frame.iterrows():
        symbol = clean_string(raw.get("Symbol"))
        current_value = parse_money(raw.get("Current Value"))
        if not symbol or current_value is None:
            continue
        if symbol.lower().startswith("date downloaded"):
            continue
        rows.append(
            {
                "symbol": symbol,
                "description": clean_string(raw.get("Description")) or symbol,
                "quantity": parse_number(raw.get("Quantity")),
                "lastPrice": parse_money(raw.get("Last Price")),
                "lastPriceChange": parse_money(raw.get("Last Price Change")),
                "currentValueUsd": current_value,
                "todayGainLossUsd": parse_money(raw.get("Today's Gain/Loss Dollar")),
                "todayGainLossPct": parse_pct(raw.get("Today's Gain/Loss Percent")),
                "totalGainLossUsd": parse_money(raw.get("Total Gain/Loss Dollar")),
                "totalGainLossPct": parse_pct(raw.get("Total Gain/Loss Percent")),
                "percentOfAccount": parse_pct(raw.get("Percent Of Account")),
                "costBasisUsd": parse_money(raw.get("Cost Basis Total")),
                "averageCostBasis": parse_money(raw.get("Average Cost Basis")),
                "accountType": clean_string(raw.get("Type")) or "unclassified",
                "priceDate": None,
                "priceSource": "brokerage_csv",
                "priceStatus": "imported",
                "priceError": None,
            }
        )
    return rows


def load_seed_positions(
    seed: dict[str, Any],
    *,
    refresh_prices: bool,
    latest_prices: dict[str, dict[str, Any]] | None,
    option_prices: dict[str, dict[str, Any]] | None,
    snapshot_date: date,
) -> list[dict[str, Any]]:
    rows = []
    latest_prices = latest_prices or {}
    option_prices = option_prices or {}
    for item in seed.get("positions") or []:
        rows.append(
            refresh_seed_position(
                item,
                refresh_prices=refresh_prices,
                latest_prices=latest_prices,
                option_prices=option_prices,
                snapshot_date=snapshot_date,
            )
        )
    return rows


def refresh_seed_position(
    item: dict[str, Any],
    *,
    refresh_prices: bool,
    latest_prices: dict[str, dict[str, Any]],
    option_prices: dict[str, dict[str, Any]],
    snapshot_date: date,
) -> dict[str, Any]:
    symbol = str(item["symbol"])
    instrument = str(item.get("instrument") or "equity")
    quantity = parse_number(item.get("quantity")) or 0.0
    cost_basis = parse_money(item.get("costBasisUsd")) or 0.0
    seed_value = parse_money(item.get("seedValueUsd")) or 0.0
    fallback = parse_money(item.get("fallbackMarkUsd"))
    price = fallback
    price_date = item.get("seedPriceDate")
    price_source = "seed_fallback"
    price_status = "seed_mark"
    price_error = None

    if instrument in {"cash", "pending"}:
        current_value = seed_value
        price_status = "fixed_value"
    elif refresh_prices:
        try:
            if item.get("option"):
                quote = get_option_quote(item, option_prices=option_prices)
            else:
                quote = get_equity_quote(
                    symbol,
                    latest_prices=latest_prices,
                    as_of_date=snapshot_date,
                )
            price = quote["price"]
            price_date = quote.get("price_date")
            price_source = quote.get("source", "yfinance")
            price_status = "refreshed"
            current_value = position_value(quantity=quantity, price=price, instrument=instrument)
        except Exception as exc:  # pragma: no cover - surfaced in generated JSON
            price_error = str(exc)
            current_value = seed_value
            price_status = "fallback_after_refresh_error"
    else:
        current_value = seed_value

    if instrument not in {"cash", "pending"} and (price is None or price <= 0):
        current_value = seed_value
        price_status = "fallback_missing_mark"

    total_gain_loss = current_value - cost_basis if cost_basis else None
    return {
        "symbol": symbol,
        "description": clean_string(item.get("description")) or symbol,
        "quantity": quantity,
        "lastPrice": price,
        "lastPriceChange": None,
        "currentValueUsd": current_value,
        "todayGainLossUsd": None,
        "todayGainLossPct": None,
        "totalGainLossUsd": total_gain_loss,
        "totalGainLossPct": safe_pct(total_gain_loss or 0, cost_basis) if cost_basis else None,
        "percentOfAccount": None,
        "costBasisUsd": cost_basis,
        "averageCostBasis": None,
        "accountType": "sanitized_public_seed",
        "priceDate": price_date,
        "priceSource": price_source,
        "priceStatus": price_status,
        "priceError": price_error,
    }


def enrich_position(
    row: dict[str, Any],
    framework: dict[str, dict[str, Any]],
    watchlist: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    symbol = row["symbol"].strip()
    option = parse_option_symbol(symbol)
    instrument = infer_instrument(symbol, row, option)
    mapped_symbol = option["underlying"] if option else symbol
    mapping = framework.get(mapped_symbol)
    watch = watchlist.get(mapped_symbol)
    framework_status = framework_status_for(symbol, mapped_symbol, instrument, mapping, watch)
    return {
        **row,
        "symbol": symbol,
        "displaySymbol": symbol.lstrip(" -"),
        "instrument": instrument,
        "underlying": mapped_symbol if option else None,
        "option": option,
        "frameworkStatus": framework_status,
        "frameworkBucket": (
            mapping.get("bucket") if mapping else watch.get("theme") if watch else None
        ),
        "frameworkLayers": mapping.get("layers", []) if mapping else layer_guess(mapped_symbol),
        "targetWeightPct": mapping.get("targetWeightPct") if mapping else None,
        "decisionRead": decision_read(symbol, mapped_symbol, instrument, mapping, watch),
        "actionBoundary": "review_only_no_automatic_rebalance",
    }


def aggregate_positions(
    positions: list[dict[str, Any]],
    framework: dict[str, dict[str, Any]],
    watchlist: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in positions:
        key = row["symbol"]
        bucket = grouped.setdefault(
            key,
            {
                "symbol": row["symbol"],
                "displaySymbol": row["displaySymbol"],
                "description": row["description"],
                "instrument": row["instrument"],
                "underlying": row["underlying"],
                "option": row["option"],
                "currentValueUsd": 0.0,
                "absoluteExposureUsd": 0.0,
                "quantity": 0.0,
                "todayGainLossUsd": 0.0,
                "totalGainLossUsd": 0.0,
                "costBasisUsd": 0.0,
                "lastPrice": row.get("lastPrice"),
                "priceDate": row.get("priceDate"),
                "priceSource": row.get("priceSource"),
                "priceStatus": row.get("priceStatus"),
                "priceError": row.get("priceError"),
                "frameworkStatus": row["frameworkStatus"],
                "frameworkBucket": row["frameworkBucket"],
                "frameworkLayers": row["frameworkLayers"],
                "targetWeightPct": row["targetWeightPct"],
                "decisionRead": row["decisionRead"],
                "actionBoundary": row["actionBoundary"],
            },
        )
        bucket["currentValueUsd"] += row["currentValueUsd"]
        bucket["absoluteExposureUsd"] += abs(row["currentValueUsd"])
        bucket["quantity"] += float(row["quantity"] or 0)
        bucket["todayGainLossUsd"] += float(row["todayGainLossUsd"] or 0)
        bucket["totalGainLossUsd"] += float(row["totalGainLossUsd"] or 0)
        bucket["costBasisUsd"] += float(row["costBasisUsd"] or 0)
        for field in ("lastPrice", "priceDate", "priceSource", "priceStatus", "priceError"):
            bucket[field] = row.get(field) or bucket.get(field)

    total = sum(item["currentValueUsd"] for item in grouped.values())
    rows = []
    for item in grouped.values():
        symbol_for_map = item["underlying"] or item["symbol"]
        target = item["targetWeightPct"]
        current_weight = safe_pct(item["currentValueUsd"], total)
        rule_state = rule_state_for(item, current_weight, target, watchlist.get(symbol_for_map))
        rows.append(
            {
                **item,
                "currentWeightPct": current_weight,
                "absoluteExposurePct": safe_pct(item["absoluteExposureUsd"], total),
                "driftVsTargetPct": None if target is None else current_weight - float(target),
                "ruleState": rule_state,
                "reviewReason": review_reason_for(item, current_weight, target, rule_state),
            }
        )
    return sorted(rows, key=lambda row: abs(row["currentValueUsd"]), reverse=True)


def build_summary(positions: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(row["currentValueUsd"] for row in positions)
    gross = sum(abs(row["currentValueUsd"]) for row in positions)
    cash = sum(row["currentValueUsd"] for row in positions if row["frameworkStatus"] == "cash")
    pending = sum(row["currentValueUsd"] for row in positions if row["instrument"] == "pending")
    options = sum(row["currentValueUsd"] for row in positions if row["instrument"].endswith("call"))
    framework = sum(
        row["currentValueUsd"]
        for row in positions
        if row["frameworkStatus"] in {"framework_holding", "framework_derivative_overlay"}
    )
    watchlist = total_for_status(positions, "watchlist")
    index_etf = total_for_status(positions, "index_overlay")
    outside = total_for_status(positions, "outside_framework")
    defensive = total_for_status(positions, "defensive_or_hedge")
    top = positions[0] if positions else {}
    top5 = sum(row["currentValueUsd"] for row in positions[:5])
    price_status_counts: dict[str, int] = {}
    for row in positions:
        status = str(row.get("priceStatus") or "unknown")
        price_status_counts[status] = price_status_counts.get(status, 0) + 1
    return {
        "totalValueUsd": total,
        "grossExposureUsd": gross,
        "grossExposurePct": safe_pct(gross, total),
        "cashUsd": cash,
        "cashWeightPct": safe_pct(cash, total),
        "pendingUsd": pending,
        "optionNetUsd": options,
        "optionNetWeightPct": safe_pct(options, total),
        "frameworkMappedUsd": framework,
        "frameworkMappedWeightPct": safe_pct(framework, total),
        "watchlistUsd": watchlist,
        "watchlistWeightPct": safe_pct(watchlist, total),
        "indexOverlayUsd": index_etf,
        "indexOverlayWeightPct": safe_pct(index_etf, total),
        "outsideFrameworkUsd": outside,
        "outsideFrameworkWeightPct": safe_pct(outside, total),
        "defensiveOrHedgeUsd": defensive,
        "defensiveOrHedgeWeightPct": safe_pct(defensive, total),
        "topPosition": top.get("displaySymbol"),
        "topPositionWeightPct": top.get("currentWeightPct", 0),
        "topFiveWeightPct": safe_pct(top5, total),
        "positionCount": len(positions),
        "priceStatusCounts": price_status_counts,
        "reviewState": "review_required",
        "reviewBoundary": "analysis_only_no_trade_instruction",
    }


def total_for_status(positions: list[dict[str, Any]], status: str) -> float:
    return sum(row["currentValueUsd"] for row in positions if row["frameworkStatus"] == status)


def build_classifications(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = {
        "framework_holding": "Framework holdings",
        "framework_derivative_overlay": "Framework derivative overlays",
        "watchlist": "Watchlist names",
        "index_overlay": "Index / momentum overlays",
        "defensive_or_hedge": "Defensive / hedge",
        "outside_framework": "Outside framework",
        "cash": "Cash",
        "pending": "Pending activity",
    }
    total = sum(row["currentValueUsd"] for row in positions)
    rows = []
    for status, label in labels.items():
        value = sum(row["currentValueUsd"] for row in positions if row["frameworkStatus"] == status)
        if abs(value) < 0.005:
            continue
        rows.append(
            {
                "status": status,
                "label": label,
                "valueUsd": value,
                "weightPct": safe_pct(value, total),
                "count": sum(1 for row in positions if row["frameworkStatus"] == status),
            }
        )
    return rows


def build_framework_coverage(
    positions: list[dict[str, Any]],
    framework: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    held_symbols = {row["underlying"] or row["symbol"] for row in positions}
    framework_tickers = {ticker for ticker in framework if ticker != "CASH"}
    matched = sorted(held_symbols & framework_tickers)
    missing = sorted(framework_tickers - held_symbols)
    over = []
    under = []
    for row in positions:
        if row["targetWeightPct"] is None or row["frameworkStatus"] not in {
            "framework_holding",
            "framework_derivative_overlay",
        }:
            continue
        drift = row["driftVsTargetPct"]
        if drift is not None and drift > 3:
            over.append(row["displaySymbol"])
        if drift is not None and drift < -3:
            under.append(row["displaySymbol"])
    return {
        "matchedFrameworkTickers": matched,
        "missingFrameworkTickers": missing,
        "overTargetTickers": over,
        "underTargetTickers": under,
        "coverageRatio": len(matched) / len(framework_tickers) if framework_tickers else 0,
    }


def build_derivative_overlay(positions: list[dict[str, Any]]) -> dict[str, Any]:
    option_rows = [row for row in positions if row["option"]]
    by_underlying: dict[str, float] = {}
    for row in option_rows:
        by_underlying[row["underlying"]] = by_underlying.get(row["underlying"], 0.0) + row[
            "currentValueUsd"
        ]
    return {
        "optionCount": len(option_rows),
        "netValueByUnderlying": [
            {"underlying": key, "netValueUsd": value}
            for key, value in sorted(
                by_underlying.items(),
                key=lambda item: abs(item[1]),
                reverse=True,
            )
        ],
        "notes": [
            "Options are shown at current market value, not delta-adjusted notional.",
            (
                "Negative market value on short calls is a liability; positive market value "
                "on long calls is an asset."
            ),
            (
                "TER exposure is expressed primarily through a long-call/short-call spread, "
                "not through common stock."
            ),
        ],
    }


def build_review_queue(
    positions: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    queue = []
    if summary["topPositionWeightPct"] > 20:
        queue.append(
            {
                "priority": "high",
                "topic": "concentration",
                "question": (
                    "NVDA/common + index overlays create a high AI-beta concentration; "
                    "review against framework capex-cycle risk."
                ),
                "actionBoundary": "review_only",
            }
        )
    if summary["indexOverlayWeightPct"] > 25:
        queue.append(
            {
                "priority": "medium",
                "topic": "index_overlay",
                "question": (
                    "Index and momentum ETFs are material; decide whether they are "
                    "liquidity ballast, beta, or accidental double-counting."
                ),
                "actionBoundary": "review_only",
            }
        )
    if any(row["symbol"] == "MU" for row in positions):
        queue.append(
            {
                "priority": "high",
                "topic": "memory_watchlist",
                "question": (
                    "MU is now a real current position while framework status is "
                    "watchlist-only; run the promotion gate before any framework inclusion."
                ),
                "actionBoundary": "no_framework_promotion_without_decision_log",
            }
        )
    if any(row["underlying"] == "TER" for row in positions):
        queue.append(
            {
                "priority": "medium",
                "topic": "derivative_overlay",
                "question": (
                    "TER thesis exposure is expressed through options; review whether this "
                    "matches the framework's semitest + robotics optionality role."
                ),
                "actionBoundary": "review_only",
            }
        )
    outside = [
        row["displaySymbol"] for row in positions if row["frameworkStatus"] == "outside_framework"
    ]
    if outside:
        queue.append(
            {
                "priority": "medium",
                "topic": "outside_framework",
                "question": (
                    "Classify outside-framework names as deliberate diversifiers, "
                    "watchlist candidates, or positions to exclude from the framework lens."
                ),
                "symbols": outside[:12],
                "actionBoundary": "review_only",
            }
        )
    stale_marks = summary.get("priceStatusCounts", {}).get("fallback_after_refresh_error", 0)
    if stale_marks:
        queue.append(
            {
                "priority": "medium",
                "topic": "price_refresh",
                "question": (
                    f"{stale_marks} position marks used seed fallback after a refresh error; "
                    "review stale option or ticker prices before relying on current weights."
                ),
                "actionBoundary": "review_only",
            }
        )
    return queue


def get_equity_quote(
    symbol: str,
    *,
    latest_prices: dict[str, dict[str, Any]],
    as_of_date: date,
) -> dict[str, Any]:
    if symbol in latest_prices:
        quote = latest_prices[symbol]
    else:
        quote = fetch_latest_price(symbol, as_of_date=as_of_date)
    return {
        "price": float(quote["price_native"]),
        "price_date": quote.get("price_date"),
        "source": quote.get("source", "yfinance"),
    }


def get_option_quote(
    item: dict[str, Any],
    *,
    option_prices: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    symbol = str(item["symbol"])
    display = symbol.lstrip(" -")
    if symbol in option_prices:
        return option_prices[symbol]
    if display in option_prices:
        return option_prices[display]

    option = item.get("option") or parse_option_symbol(symbol)
    if not option:
        raise ValueError(f"option details missing for {symbol}")
    underlying = option["underlying"]
    expiration = option["expiration"]
    right = option["right"]
    strike = float(option["strike"])
    chain = yf.Ticker(underlying).option_chain(expiration)
    frame = chain.calls if right == "C" else chain.puts
    if frame.empty:
        raise ValueError(f"empty option chain for {underlying} {expiration}")
    target_contract = yahoo_option_contract_symbol(option)
    row = frame[frame["contractSymbol"] == target_contract]
    if row.empty:
        strike_distance = (frame["strike"].astype(float) - strike).abs()
        row = frame.loc[[strike_distance.idxmin()]]
        if abs(float(row.iloc[0]["strike"]) - strike) > 0.01:
            raise ValueError(f"strike {strike} not found for {underlying} {expiration}")
    latest = row.iloc[0]
    bid = coerce_positive(latest.get("bid"))
    ask = coerce_positive(latest.get("ask"))
    last = coerce_positive(latest.get("lastPrice"))
    if bid and ask:
        price = (bid + ask) / 2
        source = "yfinance_option_mid"
    elif last:
        price = last
        source = "yfinance_option_last"
    else:
        raise ValueError(f"no usable option mark for {display}")
    return {
        "price": float(price),
        "price_date": index_date_label(latest.get("lastTradeDate")),
        "source": source,
    }


def yahoo_option_contract_symbol(option: dict[str, Any]) -> str:
    expiry = str(option["expiration"]).replace("-", "")[2:]
    strike = int(round(float(option["strike"]) * 1000))
    return f"{option['underlying']}{expiry}{option['right']}{strike:08d}"


def position_value(*, quantity: float, price: float, instrument: str) -> float:
    multiplier = 100.0 if instrument.endswith("call") or instrument.endswith("put") else 1.0
    return quantity * price * multiplier


def fallback_mark(row: dict[str, Any]) -> float | None:
    quantity = float(row.get("quantity") or 0)
    value = float(row.get("currentValueUsd") or 0)
    instrument = str(row.get("instrument") or "")
    if quantity == 0:
        return None
    multiplier = 100.0 if instrument.endswith("call") or instrument.endswith("put") else 1.0
    return abs(value / (quantity * multiplier))


def coerce_positive(value: Any) -> float | None:
    numeric = parse_number(value)
    if numeric is None or numeric <= 0:
        return None
    return numeric


def infer_instrument(symbol: str, row: dict[str, Any], option: dict[str, Any] | None) -> str:
    if symbol == "Pending activity":
        return "pending"
    is_money_market_cash = (
        row["accountType"].lower() == "cash" and "money market" in row["description"].lower()
    )
    if symbol == "SPAXX**" or is_money_market_cash:
        return "cash"
    if option:
        side = "short" if (row["quantity"] or 0) < 0 else "long"
        return f"{side}_{'call' if option['right'] == 'C' else 'put'}"
    if symbol in INDEX_ETFS:
        return "etf"
    return "equity"


def framework_status_for(
    symbol: str,
    mapped_symbol: str,
    instrument: str,
    mapping: dict[str, Any] | None,
    watch: dict[str, Any] | None,
) -> str:
    if instrument == "cash":
        return "cash"
    if instrument == "pending":
        return "pending"
    if symbol in INDEX_ETFS:
        return "index_overlay"
    if symbol in DEFENSIVE_OR_HEDGE:
        return "defensive_or_hedge"
    if mapping and instrument.endswith("call"):
        return "framework_derivative_overlay"
    if mapping:
        return "framework_holding"
    if watch:
        return "watchlist"
    return "outside_framework"


def decision_read(
    symbol: str,
    mapped_symbol: str,
    instrument: str,
    mapping: dict[str, Any] | None,
    watch: dict[str, Any] | None,
) -> str:
    if mapping and instrument.endswith("call"):
        return (
            "Framework exposure through derivatives; review option structure separately "
            "from target common-stock weight."
        )
    if mapping:
        return (
            "Matches an existing framework holding; compare current weight against target "
            "and review band."
        )
    if watch:
        return (
            "Current real position, but framework status remains watchlist-only until "
            "promotion gate is passed."
        )
    if symbol in INDEX_ETFS:
        return "Portfolio beta overlay; not a control-right holding."
    if symbol in DEFENSIVE_OR_HEDGE:
        return "Diversifier or hedge outside the AI trusted-execution thesis."
    if mapped_symbol in AI_ADJACENT or symbol in AI_ADJACENT:
        return (
            "AI-adjacent name outside the current framework; classify as candidate, "
            "hedge, or exclude."
        )
    return (
        "Outside current framework; needs explicit rationale if retained in the "
        "framework view."
    )


def rule_state_for(
    item: dict[str, Any],
    current_weight: float,
    target: float | None,
    watch: dict[str, Any] | None,
) -> str:
    if item["frameworkStatus"] == "watchlist" or watch:
        return "promotion_gate_required"
    if item["frameworkStatus"] == "outside_framework":
        return "classification_required"
    if item["instrument"].endswith("call"):
        return "derivative_review"
    if target is None:
        return "informational"
    drift = current_weight - float(target)
    if abs(drift) > 3:
        return "weight_drift_review"
    return "within_framework_band"


def review_reason_for(
    item: dict[str, Any],
    current_weight: float,
    target: float | None,
    rule_state: str,
) -> str:
    if rule_state == "promotion_gate_required":
        return "Real position exists while framework status is watchlist-only."
    if rule_state == "classification_required":
        return "Name is outside the current control-right framework."
    if rule_state == "derivative_review":
        return "Option exposure should be reviewed separately from common-stock target weights."
    if rule_state == "weight_drift_review" and target is not None:
        return f"Current weight {current_weight:.2f}% versus framework target {float(target):.2f}%."
    return "No immediate rule issue; keep in regular review cadence."


def parse_option_symbol(symbol: str) -> dict[str, Any] | None:
    clean = symbol.strip().replace(" ", "")
    match = OPTION_RE.match(clean)
    if not match:
        return None
    expiry_raw = match.group("expiry")
    return {
        "underlying": match.group("underlying"),
        "expiration": f"20{expiry_raw[:2]}-{expiry_raw[2:4]}-{expiry_raw[4:6]}",
        "right": match.group("right"),
        "strike": float(match.group("strike")),
    }


def load_framework_map() -> dict[str, dict[str, Any]]:
    frame = pd.read_csv(HOLDINGS_PATH)
    rows = {}
    for _, row in frame.iterrows():
        ticker = str(row["ticker"])
        rows[ticker] = {
            "name": row["holding_name"],
            "bucket": row["bucket"],
            "targetWeightPct": float(row["target_weight"]),
            "layers": [
                normalize_layer(layer)
                for layer in str(row.get("control_layers", "")).split(";")
                if layer
            ],
        }
    return rows


def load_watchlist_map() -> dict[str, dict[str, Any]]:
    if not WATCHLIST_RULES_PATH.exists():
        return {}
    payload = yaml.safe_load(WATCHLIST_RULES_PATH.read_text(encoding="utf-8")) or {}
    rows = {}
    for ticker, rule in (payload.get("rules") or {}).items():
        if rule.get("status") == "watchlist_only":
            rows[str(ticker)] = {
                "theme": rule.get("theme", "watchlist"),
                "relationship": rule.get("relationship"),
            }
    return rows


def layer_guess(symbol: str) -> list[str]:
    guesses = {
        "AMZN": ["capacity", "authority"],
        "ASML": ["capacity"],
        "AMD": ["capacity", "cost"],
        "ARM": ["capacity"],
        "INTC": ["capacity"],
        "AAPL": ["authority", "outcome"],
        "MU": ["capacity"],
    }
    return guesses.get(symbol, [])


def normalize_layer(value: str) -> str:
    return value.strip().replace("_", " ").title()


def parse_money(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("$", "").replace(",", "").replace("+", "")
    if negative:
        text = f"-{text[1:-1]}"
    try:
        return float(text)
    except ValueError:
        return None


def parse_pct(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).replace("%", "").replace("+", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_number(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def clean_string(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    return text or None


def safe_pct(value: float, total: float) -> float:
    return 0.0 if abs(total) < 0.000001 else (value / total) * 100


def extract_downloaded_at(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines()[-8:]:
        clean = line.strip().strip('"')
        if clean.startswith("Date downloaded"):
            return clean.replace("Date downloaded", "").strip()
    return None


def index_date_label(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)


def utc_iso(now: datetime | None = None) -> str:
    return (
        (now or datetime.now(UTC))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
