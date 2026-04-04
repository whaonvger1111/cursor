from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import pandas as pd

from trading_agent.config import big_move_pct
from trading_agent.fetch_quotes import QuoteBundle, fetch_history


@dataclass
class SymbolAnalysis:
    symbol: str
    last_close: float | None
    prev_close: float | None
    day_change_pct: float | None
    ma5: float | None
    ma20: float | None
    vs_ma5: str
    vs_ma20: str
    note: str
    error: str | None = None


def _last_two_closes(hist: pd.DataFrame) -> tuple[float | None, float | None]:
    if hist.empty or "Close" not in hist.columns:
        return None, None
    closes = hist["Close"].dropna()
    if len(closes) < 1:
        return None, None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    return last, prev


def _ma(hist: pd.DataFrame, window: int) -> float | None:
    if hist.empty or "Close" not in hist.columns:
        return None
    s = hist["Close"].dropna()
    if len(s) < window:
        return None
    return float(s.iloc[-window:].mean())


def _position_vs_ma(price: float | None, ma: float | None) -> str:
    if price is None or ma is None or ma == 0:
        return "n/a"
    if price > ma:
        return "above"
    if price < ma:
        return "below"
    return "at"


def analyze_symbol(symbol: str, lookback_days: int, move_threshold: float) -> SymbolAnalysis:
    bundle = fetch_history(symbol, lookback_days)
    if bundle.error:
        return SymbolAnalysis(
            symbol=symbol,
            last_close=None,
            prev_close=None,
            day_change_pct=None,
            ma5=None,
            ma20=None,
            vs_ma5="n/a",
            vs_ma20="n/a",
            note="",
            error=bundle.error,
        )

    hist = bundle.history
    last, prev = _last_two_closes(hist)
    day_pct: float | None = None
    if last is not None and prev is not None and prev != 0:
        day_pct = (last / prev - 1.0) * 100.0

    ma5 = _ma(hist, 5)
    ma20 = _ma(hist, 20)

    notes: List[str] = []
    if day_pct is not None and abs(day_pct) >= move_threshold:
        notes.append(f"large move vs threshold ({move_threshold:.1f}%): {day_pct:+.2f}%")

    if last is not None and ma5 is not None and ma20 is not None:
        if last > ma5 and last > ma20:
            notes.append("price above both MA5 and MA20 (short-term strength)")
        elif last < ma5 and last < ma20:
            notes.append("price below both MA5 and MA20 (short-term weakness)")

    return SymbolAnalysis(
        symbol=symbol,
        last_close=last,
        prev_close=prev,
        day_change_pct=day_pct,
        ma5=ma5,
        ma20=ma20,
        vs_ma5=_position_vs_ma(last, ma5),
        vs_ma20=_position_vs_ma(last, ma20),
        note="; ".join(notes) if notes else "no notable rule-based flags",
        error=None,
    )


def run_analysis(symbols: List[str], lookback_days: int) -> str:
    thr = big_move_pct()
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"Daily stock analysis (UTC time: {now})")
    lines.append(f"Symbols: {', '.join(symbols)}")
    lines.append("")

    for sym in symbols:
        a = analyze_symbol(sym, lookback_days, thr)
        lines.append(f"=== {a.symbol} ===")
        if a.error:
            lines.append(f"  ERROR: {a.error}")
            lines.append("")
            continue
        lc = f"{a.last_close:.4f}" if a.last_close is not None else "n/a"
        pc = f"{a.prev_close:.4f}" if a.prev_close is not None else "n/a"
        dpc = f"{a.day_change_pct:+.2f}%" if a.day_change_pct is not None else "n/a"
        m5 = f"{a.ma5:.4f}" if a.ma5 is not None else "n/a"
        m20 = f"{a.ma20:.4f}" if a.ma20 is not None else "n/a"
        lines.append(f"  last close: {lc}  prev close: {pc}  day change: {dpc}")
        lines.append(f"  MA5: {m5} ({a.vs_ma5})   MA20: {m20} ({a.vs_ma20})")
        lines.append(f"  summary: {a.note}")
        lines.append("")

    lines.append(
        "Disclaimer: rule-based summary from public quotes, not investment advice."
    )
    return "\n".join(lines)
