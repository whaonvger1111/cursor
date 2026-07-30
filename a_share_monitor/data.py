"""Fetch A-share quotes and historical bars."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

import baostock as bs
import pandas as pd
import requests

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


def fetch_history(bs_code: str, days: int = 180) -> pd.DataFrame:
    """Load adjusted daily OHLCV bars."""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
    fields = "date,open,high,low,close,volume,amount,pctChg"

    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock login failed: {lg.error_msg}")

    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields,
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

        df = pd.DataFrame(rows, columns=rs.fields)
        if df.empty:
            raise RuntimeError(f"No history returned for {bs_code}")

        for col in ("open", "high", "low", "close", "volume", "amount", "pctChg"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["close"]).sort_values("date").tail(days)
        return df.reset_index(drop=True)
    finally:
        bs.logout()


def fetch_quotes(bs_codes: list[str]) -> dict[str, Quote]:
    """Fetch latest intraday quotes from Tencent."""
    if not bs_codes:
        return {}

    symbols = ",".join(to_tencent_symbol(code) for code in bs_codes)
    resp = requests.get(TENCENT_QUOTE_URL.format(codes=symbols), timeout=15)
    resp.raise_for_status()

    quotes: dict[str, Quote] = {}
    for line in resp.text.strip().split(";"):
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
