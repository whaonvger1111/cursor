"""Utilities for China A-share ticker normalization (Shanghai / Shenzhen)."""

from __future__ import annotations

from typing import Optional, Tuple

def normalize_a_share_code(raw: str) -> str:
    """Return 6-digit code string without exchange suffix, uppercased."""
    s = raw.strip().upper()
    if "." in s:
        code, suf = s.split(".", 1)
        code = code.strip()
        suf = suf.strip().upper()
        if suf in ("SS", "SH"):
            return code
        if suf in ("SZ",):
            return code
    return s


def parse_yahoo_style_symbol(symbol: str) -> Tuple[str, Optional[str]]:
    """
    Parse Yahoo-style symbols like 600519.SS / 000001.SZ into (code, 'SH'|'SZ'|None).
    """
    s = symbol.strip().upper()
    if "." not in s:
        return s, None
    code, suf = s.split(".", 1)
    code = code.strip()
    suf = suf.strip().upper()
    if suf in ("SS", "SH"):
        return code, "SH"
    if suf == "SZ":
        return code, "SZ"
    return code, None


def infer_exchange(code: str) -> Optional[str]:
    """Infer SH or SZ from a 6-digit A-share code (common A-share numbering)."""
    if len(code) != 6 or not code.isdigit():
        return None
    # Shanghai A-shares: 6xxxxxx (incl. 688 STAR); Shenzhen: 0xxxxx / 3xxxxx (main, SME, ChiNext)
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    return None


def to_em_symbol(symbol: str) -> str:
    """
    AkShare Eastmoney APIs often expect SH600519 / SZ000001 style symbols.
    """
    code, ex = parse_yahoo_style_symbol(symbol)
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"Invalid A-share code in symbol: {symbol!r}")
    exchange = ex or infer_exchange(code)
    if not exchange:
        raise ValueError(
            f"Cannot infer exchange for code {code}. "
            "Use Yahoo-style suffix: e.g. 600519.SS or 000001.SZ."
        )
    return f"{exchange}{code}"


def is_a_share_symbol(symbol: str) -> bool:
    """
    True if the symbol looks like a China A-share (6-digit SH/SZ code, optional .SS/.SZ).
    """
    if not symbol or not isinstance(symbol, str):
        return False
    code, ex = parse_yahoo_style_symbol(symbol)
    if len(code) != 6 or not code.isdigit():
        return False
    if ex in ("SH", "SZ"):
        return True
    return infer_exchange(code) is not None
