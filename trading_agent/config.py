import os
import re
from typing import List

# 默认：几只流动性较好的 A 股示例（6 位代码，不含交易所后缀）
_DEFAULT_A_SHARE = "600519,600036,000858,601318,600900"


def _normalize_symbol(s: str) -> str:
    s = s.strip().upper()
    # 600519.SS / 000858.SZ -> 600519 / 000858
    m = re.match(r"^(\d{6})\.(SS|SZ|SH)?$", s, re.I)
    if m:
        return m.group(1)
    return s


def get_symbols() -> List[str]:
    raw = os.environ.get("STOCK_SYMBOLS") or _DEFAULT_A_SHARE
    parts = [_normalize_symbol(x) for x in raw.split(",") if x.strip()]
    return parts or ["600519"]


def lookback_days() -> int:
    raw = os.environ.get("STOCK_LOOKBACK_DAYS") or "60"
    return int(raw)


def big_move_pct() -> float:
    raw = os.environ.get("STOCK_BIG_MOVE_PCT") or "2.0"
    return float(raw)
