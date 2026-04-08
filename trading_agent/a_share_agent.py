"""
中国 A 股「交易代理」逻辑：行情筛选、简单技术打分、买卖时间建议。

免责声明：本模块仅基于公开行情数据做规则化输出，不构成任何投资建议。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

TZ_CN = ZoneInfo("Asia/Shanghai")


def _safe_float(x: Any) -> float | None:
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _zscore_series(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mu = s.mean()
    sigma = s.std()
    if sigma is None or sigma == 0 or math.isnan(sigma):
        return pd.Series(0.0, index=s.index)
    z = (s - mu) / sigma
    return z.clip(-3, 3)


@dataclass
class SymbolAnalysis:
    code: str
    name: str
    signal: str  # "偏多" | "偏空" | "中性"
    buy_hint: str
    sell_hint: str
    metrics: dict[str, float | str]


def fetch_a_share_spot() -> pd.DataFrame:
    import akshare as ak

    return ak.stock_zh_a_spot_em()


def filter_liquid_main_board(df: pd.DataFrame) -> pd.DataFrame:
    """剔除 ST、停牌、无成交价；保留沪深主板/创业板/科创板常见代码段。"""
    if df.empty:
        return df
    code = df["代码"].astype(str).str.zfill(6)
    name = df["名称"].astype(str)
    mask_code = (
        (
            code.str.startswith(("00", "30", "60", "68"))
            | code.str.startswith("301")  # 创业板注册制 301xxx
        )
        & ~name.str.contains("ST", case=False, na=False)
    )
    sub = df.loc[mask_code].copy()
    sub["_code"] = sub["代码"].astype(str).str.zfill(6)
    price = pd.to_numeric(sub["最新价"], errors="coerce")
    vol = pd.to_numeric(sub["成交量"], errors="coerce")
    sub = sub.loc[price.notna() & (price > 0) & vol.notna() & (vol > 0)]
    return sub


def score_universe(df: pd.DataFrame) -> pd.DataFrame:
    """对当日截面做简单综合打分（量比、换手、涨跌、中期动量）。"""
    out = df.copy()
    for col in ("涨跌幅", "量比", "换手率", "60日涨跌幅"):
        if col not in out.columns:
            out[col] = np.nan
    pct = pd.to_numeric(out["涨跌幅"], errors="coerce")
    lb = pd.to_numeric(out["量比"], errors="coerce")
    turn = pd.to_numeric(out["换手率"], errors="coerce")
    mom60 = pd.to_numeric(out["60日涨跌幅"], errors="coerce")

    z1 = _zscore_series(lb.fillna(lb.median()))
    z2 = _zscore_series(turn.fillna(turn.median()))
    z3 = _zscore_series(pct.fillna(0))
    z4 = _zscore_series(mom60.fillna(0))
    out["_score"] = 0.30 * z1 + 0.20 * z2 + 0.25 * z3 + 0.25 * z4
    return out.sort_values("_score", ascending=False)


def _ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def fetch_daily_hist(symbol: str, days: int = 120, retries: int = 3) -> pd.DataFrame:
    import akshare as ak

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.sort_values("日期").tail(days)
            return df
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    if last_err is not None:
        raise last_err
    return pd.DataFrame()


def analyze_symbol_history(
    symbol: str,
    name: str = "",
    hist: pd.DataFrame | None = None,
) -> SymbolAnalysis:
    """基于日线：MA5/MA20 与 RSI，给出偏多与偏空提示及时间段建议。"""
    if hist is None or hist.empty:
        hist = fetch_daily_hist(symbol)
    if hist is None or hist.empty or len(hist) < 25:
        return SymbolAnalysis(
            code=symbol,
            name=name,
            signal="中性",
            buy_hint="历史数据不足，无法判断。",
            sell_hint="历史数据不足，无法判断。",
            metrics={},
        )

    close = pd.to_numeric(hist["收盘"], errors="coerce")
    ma5 = _ma(close, 5)
    ma20 = _ma(close, 20)
    rsi = _rsi(close, 14)

    last = hist.iloc[-1]
    c = _safe_float(last["收盘"])
    m5 = _safe_float(ma5.iloc[-1])
    m20 = _safe_float(ma20.iloc[-1])
    r = _safe_float(rsi.iloc[-1])
    prev_m5 = _safe_float(ma5.iloc[-2]) if len(ma5) > 1 else None
    prev_m20 = _safe_float(ma20.iloc[-2]) if len(ma5) > 1 else None

    golden = (
        prev_m5 is not None
        and prev_m20 is not None
        and prev_m5 <= prev_m20
        and m5 is not None
        and m20 is not None
        and m5 > m20
    )
    death = (
        prev_m5 is not None
        and prev_m20 is not None
        and prev_m5 >= prev_m20
        and m5 is not None
        and m20 is not None
        and m5 < m20
    )

    metrics = {
        "收盘": c if c is not None else float("nan"),
        "MA5": m5 if m5 is not None else float("nan"),
        "MA20": m20 if m20 is not None else float("nan"),
        "RSI14": r if r is not None else float("nan"),
    }

    # 信号规则（可解释的简单规则）
    if golden and r is not None and r < 72:
        signal = "偏多"
    elif death or (r is not None and r > 76):
        signal = "偏空"
    elif m5 is not None and m20 is not None and m5 > m20 and r is not None and r < 80:
        signal = "偏多"
    elif m5 is not None and m20 is not None and m5 < m20:
        signal = "偏空"
    else:
        signal = "中性"

    buy_hint = (
        "下一交易日关注时段：9:35–10:30（回踩分时均线）、14:30–14:55（趋势确认）。"
        "若当日或次日收盘价仍站稳 MA5 且 RSI 未超买，可视为买点参考。"
    )
    if signal == "偏空":
        buy_hint = "当前技术结构偏弱，不建议追涨；若参与仅考虑轻仓且严格止损。"

    sell_hint = (
        "减仓参考时段：10:00–11:00 冲高无力时、14:30–14:55 若跌破分时均线。"
        "日线若 MA5 下穿 MA20 或 RSI>76，宜优先考虑减仓。"
    )
    if signal == "偏多":
        sell_hint = (
            "持仓者可关注 14:50 前是否滞涨；若次日高开低走且量能萎缩，可部分止盈。"
        )

    return SymbolAnalysis(
        code=symbol,
        name=name,
        signal=signal,
        buy_hint=buy_hint,
        sell_hint=sell_hint,
        metrics=metrics,
    )


def session_context_now() -> str:
    now = datetime.now(TZ_CN)
    return (
        f"北京时间 {now.strftime('%Y-%m-%d %H:%M')} "
        f"（A股常规交易 9:30–11:30，13:00–15:00）"
    )
