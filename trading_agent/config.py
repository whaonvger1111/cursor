import os
from typing import List

# 默认标的为沪深代表性代码（Yahoo Finance：沪市 .SS，深市 .SZ）
_DEFAULT_A_SHARE = "600519.SS,000858.SZ,000001.SS,399001.SZ"


def get_symbols() -> List[str]:
    raw = os.environ.get("STOCK_SYMBOLS") or _DEFAULT_A_SHARE
    parts = [s.strip().upper() for s in raw.split(",") if s.strip()]
    return parts or ["600519.SS"]


def lookback_days() -> int:
    raw = os.environ.get("STOCK_LOOKBACK_DAYS") or "60"
    return int(raw)


def big_move_pct() -> float:
    # A 股单日波动常大于美股，默认阈值略高
    raw = os.environ.get("STOCK_BIG_MOVE_PCT") or "3.0"
    return float(raw)
