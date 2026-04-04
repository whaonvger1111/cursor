import os
from typing import List


def get_symbols() -> List[str]:
    raw = os.environ.get("STOCK_SYMBOLS") or "AAPL,MSFT,GOOGL"
    parts = [s.strip().upper() for s in raw.split(",") if s.strip()]
    return parts or ["AAPL"]


def lookback_days() -> int:
    raw = os.environ.get("STOCK_LOOKBACK_DAYS") or "60"
    return int(raw)


def big_move_pct() -> float:
    raw = os.environ.get("STOCK_BIG_MOVE_PCT") or "2.0"
    return float(raw)
