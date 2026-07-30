"""Fetch A-share quotes and historical bars."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

import baostock as bs
import pandas as pd
import requests

from a_share_monitor.session import baostock_session

TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q={codes}"


@dataclass
class Quote:
    code: str
    name: str
    price: float
    prev_close: float
    open_price: float
    high: float
    low: float
    volume: int
    amount: float
    change_pct: float
    updated_at: str


def normalize_code(code: str) -> str:
    """Convert user input like 600519 / sh600519 to baostock format sh.600519."""
    code = code.strip().lower().replace(".", "")
    if code.startswith(("sh", "sz")):
        market, digits = code[:2], code[2:]
    elif code.startswith(("6", "9")):
        market, digits = "sh", code
    else:
        market, digits = "sz", code
    digits = re.sub(r"\D", "", digits)
    if len(digits) != 6:
        raise ValueError(f"Invalid A-share code: {code}")
    return f"{market}.{digits}"


def to_tencent_symbol(bs_code: str) -> str:
    market, digits = bs_code.split(".")
    return f"{market}{digits}"


HISTORY_FIELDS = "date,open,high,low,close,volume,amount,pctChg"


def _history_window(days: int) -> tuple[str, str]:
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
    return start, end


def _parse_history_df(df: pd.DataFrame, days: int) -> pd.DataFrame:
    if df.empty:
        raise RuntimeError("No history returned")
    for col in ("open", "high", "low", "close", "volume", "amount", "pctChg"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna(subset=["close"]).sort_values("date").tail(days).reset_index(drop=True)


def fetch_history(bs_code: str, days: int = 180) -> pd.DataFrame:
    """Load adjusted daily OHLCV bars."""
    with baostock_session():
        return fetch_history_logged_in(bs_code, days=days)


def fetch_history_logged_in(bs_code: str, days: int = 180) -> pd.DataFrame:
    """Load history assuming baostock is already logged in."""
    start, end = _history_window(days)
    rs = bs.query_history_k_data_plus(
        bs_code,
        HISTORY_FIELDS,
        start_date=start,
        end_date=end,
        frequency="d",
        adjustflag="2",
    )
    if rs.error_code != "0":
        raise RuntimeError(f"baostock query failed: {rs.error_msg}")

    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    return _parse_history_df(pd.DataFrame(rows, columns=rs.fields), days)


def fetch_quotes(bs_codes: list[str]) -> dict[str, Quote]:
    """Fetch latest intraday quotes from Tencent."""
    if not bs_codes:
        return {}

    quotes: dict[str, Quote] = {}
    chunk_size = 80
    for i in range(0, len(bs_codes), chunk_size):
        chunk = bs_codes[i : i + chunk_size]
        symbols = ",".join(to_tencent_symbol(code) for code in chunk)
        resp = requests.get(TENCENT_QUOTE_URL.format(codes=symbols), timeout=20)
        resp.raise_for_status()
        quotes.update(_parse_tencent_quotes(resp.text))
    return quotes


def _parse_tencent_quotes(text: str) -> dict[str, Quote]:
    quotes: dict[str, Quote] = {}
    for line in text.strip().split(";"):
        line = line.strip()
        if not line or "~" not in line:
            continue
        payload = line.split("=", 1)[1].strip('"')
        parts = payload.split("~")
        if len(parts) < 46:
            continue

        symbol = parts[2]
        market = "sh" if symbol.startswith(("6", "9")) else "sz"
        bs_code = f"{market}.{symbol[-6:]}"
        prev_close = float(parts[4] or 0)
        price = float(parts[3] or 0)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0

        quotes[bs_code] = Quote(
            code=bs_code,
            name=parts[1],
            price=price,
            prev_close=prev_close,
            open_price=float(parts[5] or 0),
            high=float(parts[33] or 0),
            low=float(parts[34] or 0),
            volume=int(float(parts[6] or 0)),
            amount=float(parts[37] or 0),
            change_pct=change_pct,
            updated_at=parts[30],
        )
    return quotes
