"""Fibonacci EMA momentum scanner for framework holdings and watchlists."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
import yfinance as yf

from ai_portfolio_framework.config import CONFIG_DIR, GENERATED_DATA_DIR, MANUAL_DIR, SITE_DIR

FIB_PERIODS = [5, 8, 13, 21, 34, 55, 89]
CORE_PERIODS = [8, 21, 55]
MIN_PRICE_ROWS = 34
DEFAULT_WEIGHTS = {"trend": 0.40, "momentum": 0.30, "volatility": 0.15, "volume": 0.15}
SIGNAL_BANDS = [
    (75.0, "strong_bullish", "Strong bullish setup", "intensify_positive_review"),
    (60.0, "bullish", "Bullish setup", "positive_review"),
    (40.0, "neutral", "Neutral / watch", "neutral_review"),
    (25.0, "bearish", "Bearish risk review", "risk_review"),
    (-math.inf, "strong_bearish", "Strong bearish risk review", "high_risk_review"),
]
SOURCE_ORDER = ["portfolio", "watchlist", "current_position"]
EXCLUDED_TICKERS = {"CASH", "SPAXX**", "Pending activity"}

DEFAULT_PORTFOLIO_DATA_PATH = SITE_DIR / "portfolio-data.json"
DEFAULT_CURRENT_POSITIONS_PATH = SITE_DIR / "current-positions-data.json"
DEFAULT_WATCHLIST_RULES_PATH = CONFIG_DIR / "watchlist_rules.yml"
DEFAULT_HOLDINGS_PATH = MANUAL_DIR / "ai_framework_holdings.csv"
DEFAULT_OUTPUT_PATH = SITE_DIR / "fib-momentum-data.json"
DEFAULT_GENERATED_OUTPUT_PATH = GENERATED_DATA_DIR / "fib_momentum_scan.json"


@dataclass
class MonitorTarget:
    ticker: str
    name: str
    sources: set[str] = field(default_factory=set)
    target_weight_pct: float | None = None
    current_value_usd: float | None = None
    current_weight_pct: float | None = None
    relationship: str | None = None


@dataclass
class SignalResult:
    ticker: str
    date: str
    close: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    volume_score: float
    composite_score: float
    signal: str
    signal_label: str
    review_equivalent: str
    notes: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Fibonacci EMA momentum monitor data.")
    parser.add_argument("--period", default="1y", help="Yahoo Finance history period.")
    parser.add_argument("--interval", default="1d", help="Yahoo Finance history interval.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--generated-output", type=Path, default=DEFAULT_GENERATED_OUTPUT_PATH)
    parser.add_argument(
        "--exclude-current-positions",
        action="store_true",
        help="Do not include local current-position underlyings even if present.",
    )
    args = parser.parse_args()

    payload = build_fib_momentum_data(
        period=args.period,
        interval=args.interval,
        output_path=args.output,
        generated_output_path=args.generated_output,
        current_positions_path=None
        if args.exclude_current_positions
        else DEFAULT_CURRENT_POSITIONS_PATH,
    )
    summary = payload["summary"]
    print(
        "Built Fibonacci EMA momentum monitor: "
        f"rows={summary['scannedCount']} failures={summary['failureCount']} "
        f"top={summary.get('topTicker') or 'n/a'}"
    )


def build_fib_momentum_data(
    *,
    portfolio_data_path: Path = DEFAULT_PORTFOLIO_DATA_PATH,
    watchlist_rules_path: Path = DEFAULT_WATCHLIST_RULES_PATH,
    holdings_path: Path = DEFAULT_HOLDINGS_PATH,
    current_positions_path: Path | None = DEFAULT_CURRENT_POSITIONS_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    generated_output_path: Path | None = DEFAULT_GENERATED_OUTPUT_PATH,
    period: str = "1y",
    interval: str = "1d",
    portfolio_data: dict[str, Any] | None = None,
    price_history_by_ticker: dict[str, pd.DataFrame] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    targets = build_monitor_universe(
        portfolio_data_path=portfolio_data_path,
        watchlist_rules_path=watchlist_rules_path,
        holdings_path=holdings_path,
        current_positions_path=current_positions_path,
        portfolio_data=portfolio_data,
    )
    scan_payload = scan_targets(
        targets,
        period=period,
        interval=interval,
        price_history_by_ticker=price_history_by_ticker,
    )
    rows = scan_payload["rows"]
    failures = scan_payload["failures"]
    payload = {
        "schemaVersion": 1,
        "generatedAtUtc": utc_iso(now),
        "asOfDate": latest_scan_date(rows),
        "period": period,
        "interval": interval,
        "framework": {
            "name": "fibonacci_ema_momentum",
            "emaPeriods": FIB_PERIODS,
            "corePeriods": CORE_PERIODS,
            "macd": {"fast": 8, "slow": 21, "signal": 5},
            "rsiPeriod": 13,
            "weights": DEFAULT_WEIGHTS,
            "thresholds": [
                {
                    "minComposite": min_score if math.isfinite(min_score) else None,
                    "signal": signal,
                    "label": label,
                    "reviewEquivalent": review_equivalent,
                }
                for min_score, signal, label, review_equivalent in SIGNAL_BANDS
            ],
            "actionBoundary": "technical_review_only_no_trade_instruction",
        },
        "summary": summarize_rows(rows, failures),
        "rows": rows,
        "failures": failures,
    }
    write_json(output_path, payload)
    if generated_output_path:
        write_json(generated_output_path, payload)
    return payload


def build_monitor_universe(
    *,
    portfolio_data_path: Path = DEFAULT_PORTFOLIO_DATA_PATH,
    watchlist_rules_path: Path = DEFAULT_WATCHLIST_RULES_PATH,
    holdings_path: Path = DEFAULT_HOLDINGS_PATH,
    current_positions_path: Path | None = DEFAULT_CURRENT_POSITIONS_PATH,
    portfolio_data: dict[str, Any] | None = None,
) -> dict[str, MonitorTarget]:
    targets: dict[str, MonitorTarget] = {}
    portfolio_payload = portfolio_data or load_json_optional(portfolio_data_path)

    portfolio_rows = portfolio_payload.get("holdings") or []
    if not portfolio_rows and holdings_path.exists():
        portfolio_rows = load_manual_holdings(holdings_path)
    for row in portfolio_rows:
        ticker = normalize_ticker(row.get("ticker"))
        if not is_price_ticker(ticker):
            continue
        target = targets.setdefault(
            ticker,
            MonitorTarget(ticker=ticker, name=str(row.get("holding_name") or ticker)),
        )
        target.sources.add("portfolio")
        target.name = str(row.get("holding_name") or row.get("name") or target.name)
        target.target_weight_pct = coerce_float(row.get("target_weight"))

    for ticker, rule in load_watchlist_rules(watchlist_rules_path).items():
        ticker = normalize_ticker(ticker)
        if not is_price_ticker(ticker):
            continue
        target = targets.setdefault(ticker, MonitorTarget(ticker=ticker, name=ticker))
        target.sources.add("watchlist")
        target.relationship = str(rule.get("relationship") or rule.get("theme") or "")

    for row in load_current_position_rows(current_positions_path):
        ticker = normalize_ticker(row.get("underlying") or row.get("symbol"))
        if not is_price_ticker(ticker):
            continue
        target = targets.setdefault(
            ticker,
            MonitorTarget(ticker=ticker, name=str(row.get("description") or ticker)),
        )
        target.sources.add("current_position")
        if target.name == ticker and row.get("description"):
            target.name = str(row["description"])
        value = coerce_float(row.get("currentValueUsd"))
        weight = coerce_float(row.get("currentWeightPct"))
        if value is not None:
            target.current_value_usd = (target.current_value_usd or 0.0) + value
        if weight is not None:
            target.current_weight_pct = (target.current_weight_pct or 0.0) + weight

    return dict(sorted(targets.items()))


def scan_targets(
    targets: dict[str, MonitorTarget],
    *,
    period: str = "1y",
    interval: str = "1d",
    price_history_by_ticker: dict[str, pd.DataFrame] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    rows = []
    failures = []
    price_history_by_ticker = price_history_by_ticker or {}
    for ticker, target in targets.items():
        try:
            history = price_history_by_ticker.get(ticker)
            if history is None:
                history = fetch_price_history(ticker, period=period, interval=interval)
            result = analyze_price_history(ticker, history)
            rows.append(result_to_row(result, target))
        except Exception as exc:  # pragma: no cover - surfaced in generated JSON
            failures.append(
                {
                    "ticker": ticker,
                    "name": target.name,
                    "sources": ordered_sources(target.sources),
                    "error": str(exc),
                }
            )
    rows.sort(key=lambda row: row["compositeScore"], reverse=True)
    return {"rows": rows, "failures": failures}


def fetch_price_history(ticker: str, *, period: str, interval: str) -> pd.DataFrame:
    frame = yf.download(
        ticker,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    if frame.empty:
        raise ValueError("no price history returned")
    return frame


def analyze_price_history(
    ticker: str,
    history: pd.DataFrame,
    *,
    weights: dict[str, float] | None = None,
    as_of: date | str | None = None,
) -> SignalResult:
    frame = normalize_price_history(history)
    history_rows = len(frame)
    frame = compute_indicators(frame)
    if as_of is not None:
        as_of_date = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
        frame = frame[frame.index.map(lambda value: value.date() <= as_of_date)]
    frame = frame.dropna(subset=["Close"])
    if frame.empty:
        raise ValueError("no analyzable close price")

    row = frame.iloc[-1]
    trend, trend_notes = trend_score(row)
    momentum, momentum_notes = momentum_score(row)
    volatility, volatility_notes = volatility_score(row)
    volume, volume_notes = volume_score(row)
    w = weights or DEFAULT_WEIGHTS
    composite = (
        w["trend"] * trend
        + w["momentum"] * momentum
        + w["volatility"] * volatility
        + w["volume"] * volume
    )
    signal, label, review_equivalent = signal_for_score(composite)
    return SignalResult(
        ticker=ticker,
        date=index_date_label(row.name),
        close=float(row["Close"]),
        trend_score=trend,
        momentum_score=momentum,
        volatility_score=volatility,
        volume_score=volume,
        composite_score=float(composite),
        signal=signal,
        signal_label=label,
        review_equivalent=review_equivalent,
        notes=(
            history_notes(history_rows)
            + trend_notes
            + momentum_notes
            + volatility_notes
            + volume_notes
        ),
        metrics=extract_metrics(row, history_rows=history_rows),
    )


def normalize_price_history(history: pd.DataFrame) -> pd.DataFrame:
    frame = history.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    rename = {column: str(column).strip().title() for column in frame.columns}
    frame = frame.rename(columns=rename)
    required = {"Close", "High", "Low"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing price columns: {sorted(missing)}")
    if "Volume" not in frame.columns:
        frame["Volume"] = np.nan
    frame = frame[["Close", "High", "Low", "Volume"]].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=["Close", "High", "Low"])
    if len(frame) < MIN_PRICE_ROWS:
        raise ValueError(f"need at least {MIN_PRICE_ROWS} price rows")
    return frame


def compute_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    for period in FIB_PERIODS:
        df[f"EMA{period}"] = df["Close"].ewm(span=period, adjust=False).mean()
        df[f"EMA{period}_slope"] = df[f"EMA{period}"].pct_change(3) * 100
    add_rsi(df, 13)
    add_rsi(df, 21)
    add_macd_fib(df)
    add_atr(df, 14)
    add_volume_metrics(df)
    add_bbands(df, 20)
    return df


def add_rsi(df: pd.DataFrame, period: int) -> None:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df[f"RSI{period}"] = 100 - 100 / (1 + rs)


def add_macd_fib(df: pd.DataFrame) -> None:
    ema_fast = df["Close"].ewm(span=8, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=21, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_sig"] = df["MACD"].ewm(span=5, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_sig"]


def add_atr(df: pd.DataFrame, period: int) -> None:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1)
    df["ATR"] = tr.max(axis=1).ewm(alpha=1 / period, adjust=False).mean()
    df["ATR_pct"] = df["ATR"] / df["Close"] * 100


def add_volume_metrics(df: pd.DataFrame) -> None:
    volume = df["Volume"]
    sign = np.sign(df["Close"].diff()).fillna(0)
    df["OBV"] = (sign * volume.fillna(0)).cumsum()
    df["OBV_EMA21"] = df["OBV"].ewm(span=21, adjust=False).mean()
    df["Vol_avg21"] = volume.rolling(21).mean()
    df["Rel_Vol"] = volume / df["Vol_avg21"].replace(0, np.nan)


def add_bbands(df: pd.DataFrame, period: int) -> None:
    middle = df["Close"].rolling(period).mean()
    std = df["Close"].rolling(period).std()
    df["BB_mid"] = middle
    df["BB_up"] = middle + 2 * std
    df["BB_lo"] = middle - 2 * std
    df["BB_width"] = (df["BB_up"] - df["BB_lo"]) / middle
    df["BB_width_pct"] = df["BB_width"].rolling(100).rank(pct=True) * 100


def trend_score(row: pd.Series) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 50.0
    close = row["Close"]
    ema8 = row["EMA8"]
    ema21 = row["EMA21"]
    ema55 = row["EMA55"]
    ema89 = row["EMA89"]
    if close > ema8 > ema21 > ema55 > ema89:
        score = 90.0
        notes.append("Full bull EMA stack: Close > 8 > 21 > 55 > 89.")
    elif close > ema8 > ema21 > ema55:
        score = 80.0
        notes.append("Bull EMA stack: Close > 8 > 21 > 55.")
    elif close > ema21 > ema55:
        score = 65.0
        notes.append("Mid-term bullish alignment.")
    elif close < ema8 < ema21 < ema55 < ema89:
        score = 10.0
        notes.append("Full bear EMA stack: Close < 8 < 21 < 55 < 89.")
    elif close < ema8 < ema21 < ema55:
        score = 20.0
        notes.append("Bear EMA stack: Close < 8 < 21 < 55.")
    elif close < ema21 < ema55:
        score = 35.0
        notes.append("Mid-term bearish alignment.")
    else:
        notes.append("Mixed EMA alignment / consolidation.")

    slope = row.get("EMA21_slope")
    if is_finite_number(slope):
        adjustment = float(np.clip(float(slope) * 2, -10, 10))
        score += adjustment
        notes.append(f"EMA21 3-period slope {float(slope):+.2f}% adds {adjustment:+.1f}.")
    return bounded_score(score), notes


def momentum_score(row: pd.Series) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 50.0
    hist = row.get("MACD_hist")
    if is_finite_number(hist):
        if hist > 0:
            score += 15
            notes.append(f"MACD(8,21,5) histogram positive ({float(hist):+.2f}).")
        else:
            score -= 15
            notes.append(f"MACD(8,21,5) histogram negative ({float(hist):+.2f}).")

    rsi = row.get("RSI13")
    if is_finite_number(rsi):
        rsi_value = float(rsi)
        if 50 < rsi_value < 70:
            score += 15
            notes.append(f"RSI(13) in bull zone ({rsi_value:.1f}).")
        elif rsi_value >= 70:
            notes.append(f"RSI(13) extended / overbought ({rsi_value:.1f}).")
        elif 30 < rsi_value <= 50:
            score -= 10
            notes.append(f"RSI(13) below bull zone ({rsi_value:.1f}).")
        else:
            notes.append(f"RSI(13) oversold ({rsi_value:.1f}); watch for reversal.")
    return bounded_score(score), notes


def volatility_score(row: pd.Series) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 50.0
    width_pct = row.get("BB_width_pct")
    if is_finite_number(width_pct):
        value = float(width_pct)
        if value < 20:
            score = 85.0
            notes.append(f"BB width percentile {value:.0f}: squeeze setup.")
        elif value < 40:
            score = 65.0
            notes.append(f"BB width percentile {value:.0f}: low volatility.")
        elif value > 80:
            score = 30.0
            notes.append(f"BB width percentile {value:.0f}: elevated volatility.")
        else:
            notes.append(f"BB width percentile {value:.0f}: normal volatility.")
    return bounded_score(score), notes


def volume_score(row: pd.Series) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 50.0
    obv = row.get("OBV")
    obv_ema = row.get("OBV_EMA21")
    if is_finite_number(obv) and is_finite_number(obv_ema):
        if obv > obv_ema:
            score += 20
            notes.append("OBV above OBV EMA21: accumulation confirmation.")
        else:
            score -= 20
            notes.append("OBV below OBV EMA21: distribution risk.")
    rel_volume = row.get("Rel_Vol")
    if is_finite_number(rel_volume):
        value = float(rel_volume)
        if value > 1.5:
            score += 10
            notes.append(f"Relative volume {value:.1f}x 21-period average.")
        elif value < 0.6:
            score -= 5
            notes.append(f"Thin relative volume {value:.1f}x 21-period average.")
    return bounded_score(score), notes


def signal_for_score(score: float) -> tuple[str, str, str]:
    for minimum, signal, label, review_equivalent in SIGNAL_BANDS:
        if score >= minimum:
            return signal, label, review_equivalent
    raise AssertionError("unreachable signal band")


def result_to_row(result: SignalResult, target: MonitorTarget) -> dict[str, Any]:
    return {
        "ticker": result.ticker,
        "name": target.name,
        "sources": ordered_sources(target.sources),
        "sourceLabel": source_label(target.sources),
        "date": result.date,
        "close": round(result.close, 4),
        "targetWeightPct": target.target_weight_pct,
        "currentValueUsd": target.current_value_usd,
        "currentWeightPct": target.current_weight_pct,
        "relationship": target.relationship,
        "trendScore": round(result.trend_score, 1),
        "momentumScore": round(result.momentum_score, 1),
        "volatilityScore": round(result.volatility_score, 1),
        "volumeScore": round(result.volume_score, 1),
        "compositeScore": round(result.composite_score, 1),
        "signal": result.signal,
        "signalLabel": result.signal_label,
        "reviewEquivalent": result.review_equivalent,
        "metrics": clean_for_json(result.metrics),
        "notes": result.notes[:8],
        "actionBoundary": "review_only_no_automatic_trade",
    }


def extract_metrics(row: pd.Series, *, history_rows: int) -> dict[str, Any]:
    close = float(row["Close"])
    metrics = {
        "ema5": row.get("EMA5"),
        "ema8": row.get("EMA8"),
        "ema13": row.get("EMA13"),
        "ema21": row.get("EMA21"),
        "ema34": row.get("EMA34"),
        "ema55": row.get("EMA55"),
        "ema89": row.get("EMA89"),
        "ema21SlopePct": row.get("EMA21_slope"),
        "macd": row.get("MACD"),
        "macdSignal": row.get("MACD_sig"),
        "macdHist": row.get("MACD_hist"),
        "rsi13": row.get("RSI13"),
        "rsi21": row.get("RSI21"),
        "atrPct": row.get("ATR_pct"),
        "bbWidthPct": row.get("BB_width_pct"),
        "relVolume": row.get("Rel_Vol"),
        "obvAboveEma21": bool(row.get("OBV", 0) > row.get("OBV_EMA21", 0)),
        "priceVsEma8Pct": pct(close - float(row["EMA8"]), float(row["EMA8"])),
        "priceVsEma21Pct": pct(close - float(row["EMA21"]), float(row["EMA21"])),
        "priceVsEma55Pct": pct(close - float(row["EMA55"]), float(row["EMA55"])),
        "emaStack": ema_stack_label(row),
        "historyRows": history_rows,
        "historyQuality": "seasoned" if history_rows >= max(FIB_PERIODS) else "short",
    }
    return {key: rounded_or_none(value) for key, value in metrics.items()}


def history_notes(history_rows: int) -> list[str]:
    if history_rows >= max(FIB_PERIODS):
        return []
    return [
        (
            f"Short history ({history_rows} rows); EMA89 and BB percentile are less seasoned."
        )
    ]


def ema_stack_label(row: pd.Series) -> str:
    close = row["Close"]
    if close > row["EMA8"] > row["EMA21"] > row["EMA55"] > row["EMA89"]:
        return "full_bull"
    if close > row["EMA8"] > row["EMA21"] > row["EMA55"]:
        return "bull"
    if close < row["EMA8"] < row["EMA21"] < row["EMA55"] < row["EMA89"]:
        return "full_bear"
    if close < row["EMA8"] < row["EMA21"] < row["EMA55"]:
        return "bear"
    return "mixed"


def summarize_rows(rows: list[dict[str, Any]], failures: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {signal: 0 for _, signal, _, _ in SIGNAL_BANDS if signal != "strong_bearish"}
    counts["strong_bearish"] = 0
    for row in rows:
        counts[row["signal"]] = counts.get(row["signal"], 0) + 1
    composites = [float(row["compositeScore"]) for row in rows]
    top = rows[0] if rows else {}
    bottom = min(rows, key=lambda row: row["compositeScore"]) if rows else {}
    return {
        "scannedCount": len(rows),
        "failureCount": len(failures),
        "signalCounts": counts,
        "averageComposite": round(sum(composites) / len(composites), 1) if composites else None,
        "topTicker": top.get("ticker"),
        "topComposite": top.get("compositeScore"),
        "weakestTicker": bottom.get("ticker"),
        "weakestComposite": bottom.get("compositeScore"),
        "reviewOnly": True,
    }


def latest_scan_date(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    return max(str(row["date"]) for row in rows)


def load_manual_holdings(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    return [
        {
            "ticker": row["ticker"],
            "holding_name": row.get("holding_name") or row.get("name") or row["ticker"],
            "target_weight": row.get("target_weight"),
        }
        for _, row in frame.iterrows()
    ]


def load_watchlist_rules(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload.get("rules") or {}


def load_current_position_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    payload = load_json_optional(path)
    rows = []
    for row in payload.get("positions") or []:
        instrument = str(row.get("instrument") or "")
        if instrument in {"cash", "pending"}:
            continue
        rows.append(row)
    return rows


def load_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(clean_for_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def clean_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_for_json(item) for item in value]
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, np.generic):
        return clean_for_json(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def ordered_sources(sources: Iterable[str]) -> list[str]:
    source_set = set(sources)
    ordered = [source for source in SOURCE_ORDER if source in source_set]
    ordered.extend(sorted(source_set - set(ordered)))
    return ordered


def source_label(sources: Iterable[str]) -> str:
    labels = {
        "portfolio": "Portfolio",
        "watchlist": "Watchlist",
        "current_position": "Current position",
    }
    return " / ".join(labels.get(source, source) for source in ordered_sources(sources))


def normalize_ticker(value: Any) -> str:
    return str(value or "").strip().lstrip("-").upper()


def is_price_ticker(ticker: str) -> bool:
    return bool(ticker) and ticker not in EXCLUDED_TICKERS and not ticker.endswith("=X")


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def bounded_score(value: float) -> float:
    return float(np.clip(value, 0, 100))


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator * 100


def is_finite_number(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric)


def rounded_or_none(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if not is_finite_number(value):
        return None
    return round(float(value), 4)


def index_date_label(value: Any) -> str:
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


if __name__ == "__main__":
    main()
