"""A-share market board definitions and stock universe loading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import baostock as bs
import pandas as pd

from a_share_monitor.session import baostock_session

MARKET_CHOICES = {
    "all": "全A股（沪深主板+科创板+创业板）",
    "main": "沪深主板",
    "star": "科创板（688）",
    "chinext": "创业板（300）",
    "sh": "上海A股",
    "sz": "深圳A股",
}


@dataclass
class StockInfo:
    code: str
    name: str
    board: str


def _digits(code: str) -> str:
    return code.split(".", 1)[1]


def _load_listing_snapshot(trade_date: str | None) -> pd.DataFrame:
    """Walk back up to 10 calendar days to find a non-empty listing snapshot."""
    start = (
        datetime.strptime(trade_date, "%Y-%m-%d")
        if trade_date
        else datetime.now()
    )
    last_error = "unknown error"
    for offset in range(10):
        day = (start - timedelta(days=offset)).strftime("%Y-%m-%d")
        rs = bs.query_all_stock(day=day)
        if rs.error_code != "0":
            last_error = rs.error_msg
            continue
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if rows:
            return pd.DataFrame(rows, columns=rs.fields)
    raise RuntimeError(f"baostock query_all_stock failed: {last_error}")


def classify_board(code: str) -> str | None:
    """Return board label or None if not a tradable A-share stock."""
    market, num = code.split(".")
    if not num.isdigit() or len(num) != 6:
        return None
    if num.startswith("688"):
        return "star"
    if num.startswith("300"):
        return "chinext"
    if market == "sh" and num.startswith("60"):
        return "main"
    if market == "sz" and num.startswith("00"):
        return "main"
    if market == "bj":
        return "bse"
    return None


def load_universe(market: str, trade_date: str | None = None) -> list[StockInfo]:
    """Load tradable stocks for a market board."""
    if market not in MARKET_CHOICES:
        raise ValueError(f"Unknown market '{market}'. Choose from: {', '.join(MARKET_CHOICES)}")

    with baostock_session():
        df = _load_listing_snapshot(trade_date)

    stocks: list[StockInfo] = []
    for _, row in df.iterrows():
        if str(row.get("tradeStatus", "")) != "1":
            continue
        code = str(row["code"])
        name = str(row.get("code_name", ""))
        if "指数" in name or "ETF" in name.upper():
            continue

        board = classify_board(code)
        if board is None:
            continue

        if market == "all" and board in {"star", "chinext", "main"}:
            stocks.append(StockInfo(code=code, name=name, board=board))
        elif market == "main" and board == "main":
            stocks.append(StockInfo(code=code, name=name, board=board))
        elif market == board:
            stocks.append(StockInfo(code=code, name=name, board=board))
        elif market == "sh" and code.startswith("sh."):
            stocks.append(StockInfo(code=code, name=name, board=board or "sh"))
        elif market == "sz" and code.startswith("sz."):
            stocks.append(StockInfo(code=code, name=name, board=board or "sz"))

    stocks.sort(key=lambda s: s.code)
    return stocks


def board_label(board: str) -> str:
    return {
        "star": "科创板",
        "chinext": "创业板",
        "main": "主板",
        "bse": "北交所",
        "sh": "沪市",
        "sz": "深市",
    }.get(board, board)
