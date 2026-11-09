"""日K 指标、分板、电力/银行判定、A 硬触发。"""

from __future__ import annotations

import math
import re
from typing import Any

try:
    from .config import GAP_UP_MAX, POWER_INDUSTRY_EXACT
except ImportError:
    from config import GAP_UP_MAX, POWER_INDUSTRY_EXACT


def to_float(v: Any) -> float | None:
    if v is None or v == "" or v == "-" or v == "--":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def board_of(code: str) -> str | None:
    if code.startswith("688"):
        return "科创板"
    if code.startswith(("300", "301")):
        return "创业板"
    if code.startswith(("60", "000", "001", "002", "003")):
        return "主板"
    return None


def is_st(name: str) -> bool:
    n = (name or "").upper()
    return "ST" in n or "退" in (name or "")


def is_power_stock(name: str, industry: str | None) -> bool:
    """电力股=发电/供电公用事业，不含电力设备。"""
    ind = industry or ""
    if ind in POWER_INDUSTRY_EXACT:
        return True
    if ind == "电力" or ind.startswith("电力"):
        return True
    if any(k in ind for k in ("火力发电", "水力发电", "核力发电", "光伏发电", "风力发电", "热电")):
        return "设备" not in ind
    if re.search(r"(电力|水电|火电|核电|电网|热电)$", name or ""):
        if "设备" in (name or "") or "电器" in (name or ""):
            return False
        return True
    return False


def is_bank(industry: str | None, name: str) -> bool:
    ind = industry or ""
    return "银行" in ind or (name or "").endswith("银行")


def parse_kline_row(line: str) -> dict | None:
    p = (line or "").split(",")
    if len(p) < 11:
        return None
    close = to_float(p[2])
    if close is None or close <= 0:
        return None
    return {
        "date": p[0],
        "open": to_float(p[1]),
        "close": close,
        "high": to_float(p[3]),
        "low": to_float(p[4]),
        "volume": to_float(p[5]),
        "amount": to_float(p[6]),
        "pct": to_float(p[8]),
        "turnover": to_float(p[10]),
    }


def gap_up_pct(open_px: float | None, prev_close: float | None) -> float | None:
    if open_px is None or prev_close is None or prev_close <= 0:
        return None
    return open_px / prev_close - 1.0


def is_gap_up_over(open_px: float | None, prev_close: float | None, cap: float = GAP_UP_MAX) -> bool:
    g = gap_up_pct(open_px, prev_close)
    return g is not None and g > cap


def metrics_from_bars(bars: list[dict]) -> dict:
    out: dict[str, Any] = {
        "n_bars": len(bars),
        "k_asof": bars[-1]["date"] if bars else None,
        "k_close": bars[-1]["close"] if bars else None,
        "k_open": bars[-1]["open"] if bars else None,
        "k_prev_close": bars[-2]["close"] if len(bars) >= 2 else None,
        "ret_5d": None,
        "ret_20d": None,
        "dev_ma20": None,
        "pctile_60d": None,
        "ma5": None,
        "ma20": None,
        "ma60": None,
        "above_ma20": False,
        "above_ma60": False,
        "ma5_gt_ma20": False,
        "max_1d_drop_5d": None,
        "max_1d_drop_20d": None,
        "pulse": None,
        "limit_up_5d": False,
        "near_board_5d": False,
        "avg_turnover_5d": None,
        "avg_amount_5d": None,
    }
    if len(bars) < 6:
        return out
    closes = [b["close"] for b in bars]
    pcts = [b.get("pct") for b in bars]
    c = closes[-1]

    def ret(n: int) -> float | None:
        if len(closes) > n and closes[-(n + 1)] > 0:
            return c / closes[-(n + 1)] - 1.0
        return None

    out["ret_5d"] = ret(5)
    out["ret_20d"] = ret(20)

    if len(closes) >= 5:
        out["ma5"] = sum(closes[-5:]) / 5.0
    if len(closes) >= 20:
        ma20 = sum(closes[-20:]) / 20.0
        out["ma20"] = ma20
        if ma20 > 0:
            out["dev_ma20"] = c / ma20 - 1.0
            out["above_ma20"] = c > ma20
    if len(closes) >= 60:
        ma60 = sum(closes[-60:]) / 60.0
        out["ma60"] = ma60
        out["above_ma60"] = c > ma60
        window = closes[-60:]
        out["pctile_60d"] = sum(1 for x in window if x <= c) / len(window)
    if out["ma5"] and out["ma20"]:
        out["ma5_gt_ma20"] = out["ma5"] > out["ma20"]

    last5_pct = [p for p in pcts[-5:] if p is not None]
    last20_pct = [p for p in pcts[-20:] if p is not None]
    out["max_1d_drop_5d"] = min(last5_pct) / 100.0 if last5_pct else None
    out["max_1d_drop_20d"] = min(last20_pct) / 100.0 if last20_pct else None

    tos = [b.get("turnover") for b in bars[-5:] if b.get("turnover") is not None]
    amts = [b.get("amount") for b in bars[-5:] if b.get("amount") is not None]
    out["avg_turnover_5d"] = (sum(tos) / len(tos)) if tos else None
    out["avg_amount_5d"] = (sum(amts) / len(amts)) if amts else None

    pulse = False
    r5 = out["ret_5d"]
    d5 = out["max_1d_drop_5d"]
    if r5 is not None and r5 <= -0.06 and d5 is not None and d5 < 0:
        if abs(d5) >= 0.70 * abs(r5):
            pulse = True
    r20 = out["ret_20d"]
    d20 = out["max_1d_drop_20d"]
    if r20 is not None and r20 <= -0.12 and d20 is not None and d20 < 0:
        if abs(d20) >= 0.80 * abs(r20):
            pulse = True
    out["pulse"] = pulse
    return out


def a_hits_of(m: dict) -> list[str]:
    hits = []
    r5, r20 = m.get("ret_5d"), m.get("ret_20d")
    if (r20 is not None and r20 <= -0.12) or (r5 is not None and r5 <= -0.06):
        hits.append("①")
    if m.get("dev_ma20") is not None and m["dev_ma20"] <= -0.06:
        hits.append("②")
    if m.get("pctile_60d") is not None and m["pctile_60d"] <= 0.40:
        hits.append("③")
    return hits


def limit_threshold(board: str) -> float:
    return 19.6 if board in ("创业板", "科创板") else 9.8


def apply_limit_flags(m: dict, bars: list[dict], board: str) -> dict:
    th = limit_threshold(board)
    limit_up_5d = False
    near_board_5d = False
    for b in bars[-5:]:
        p = b.get("pct")
        if p is None:
            continue
        if p >= th:
            limit_up_5d = True
        if p >= th - 1.0:
            near_board_5d = True
    m["limit_up_5d"] = limit_up_5d
    m["near_board_5d"] = near_board_5d
    return m


def fmt_pct(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "缺失"
    return f"{x * 100:.{digits}f}%"


def fmt_num(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "缺失"
    return f"{x:.{digits}f}"


def median(xs: list[float]) -> float | None:
    vals = sorted(xs)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0
