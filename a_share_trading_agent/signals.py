"""技术指标与买卖时间窗（规则化、可解释，非预测模型）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass
class SignalSummary:
    action: Literal["关注买入", "持有观望", "关注减仓"]
    score: float
    rsi14: float | None
    ma5: float | None
    ma20: float | None
    note: str


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    denom = avg_loss.clip(lower=1e-12)
    rs = avg_gain / denom
    return 100 - (100 / (1 + rs))


def summarize_signal(df: pd.DataFrame) -> SignalSummary:
    """
    基于日线：RSI + 均线位置给出简单分档。
    规则偏保守，用于辅助观察，非自动交易信号。
    """
    if df.empty or len(df) < 25:
        return SignalSummary(
            action="持有观望",
            score=0.0,
            rsi14=None,
            ma5=None,
            ma20=None,
            note="历史数据不足，无法计算可靠指标。",
        )
    close = df["close"]
    r = rsi(close, 14)
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    last_rsi = float(r.iloc[-1])
    last_ma5 = float(ma5.iloc[-1])
    last_ma20 = float(ma20.iloc[-1])
    last_close = float(close.iloc[-1])

    score = 0.0
    # 趋势
    if last_ma5 > last_ma20:
        score += 1.0
    else:
        score -= 0.5
    # RSI 区间
    if last_rsi < 35:
        score += 1.0
    elif last_rsi > 65:
        score -= 1.0
    # 价格与均线
    if last_close > last_ma5:
        score += 0.5
    else:
        score -= 0.25

    if score >= 1.0:
        action: Literal["关注买入", "持有观望", "关注减仓"] = "关注买入"
        note = "均线多头或 RSI 偏低位等条件叠加后得分偏高，可结合盘面与基本面再确认。"
    elif score <= -0.5:
        action = "关注减仓"
        note = "趋势偏弱或超买/承压，注意回撤与止盈止损纪律。"
    else:
        action = "持有观望"
        note = "信号中性，可等待更明确的趋势或量能配合。"

    return SignalSummary(
        action=action,
        score=score,
        rsi14=last_rsi,
        ma5=last_ma5,
        ma20=last_ma20,
        note=note,
    )


def cn_trading_session_hints() -> str:
    """A 股交易时段说明（用于“时间点”文字说明）。"""
    return (
        "沪深 A 股连续竞价：09:30–11:30、13:00–15:00；"
        "集合竞价：09:15–09:25（确定开盘价）；"
        "尾盘集合竞价：14:57–15:00（深市等）。"
        "若脚本在 09:30 后运行，可结合当日开盘与分时再确认；"
        "日线级信号通常以收盘价或次日开盘为执行参考，而非单根分钟线。"
    )
