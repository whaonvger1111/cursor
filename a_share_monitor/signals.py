"""Detect trading signals from indicator-enriched bars."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    code: str
    name: str
    signal_type: str
    direction: str
    strength: str
    price: float
    detail: str


def _cross_up(prev_a: float, prev_b: float, cur_a: float, cur_b: float) -> bool:
    return prev_a <= prev_b and cur_a > cur_b


def _cross_down(prev_a: float, prev_b: float, cur_a: float, cur_b: float) -> bool:
    return prev_a >= prev_b and cur_a < cur_b


def detect_signals(code: str, name: str, df: pd.DataFrame) -> list[Signal]:
    if len(df) < 60:
        return []

    prev = df.iloc[-2]
    cur = df.iloc[-1]
    price = float(cur["close"])
    signals: list[Signal] = []

    if _cross_up(prev["ma5"], prev["ma20"], cur["ma5"], cur["ma20"]):
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="MA_CROSS",
                direction="BUY",
                strength="medium",
                price=price,
                detail="MA5 上穿 MA20（金叉）",
            )
        )
    elif _cross_down(prev["ma5"], prev["ma20"], cur["ma5"], cur["ma20"]):
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="MA_CROSS",
                direction="SELL",
                strength="medium",
                price=price,
                detail="MA5 下穿 MA20（死叉）",
            )
        )

    if _cross_up(prev["macd_dif"], prev["macd_dea"], cur["macd_dif"], cur["macd_dea"]):
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="MACD_CROSS",
                direction="BUY",
                strength="medium",
                price=price,
                detail="MACD DIF 上穿 DEA",
            )
        )
    elif _cross_down(prev["macd_dif"], prev["macd_dea"], cur["macd_dif"], cur["macd_dea"]):
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="MACD_CROSS",
                direction="SELL",
                strength="medium",
                price=price,
                detail="MACD DIF 下穿 DEA",
            )
        )

    rsi = float(cur["rsi14"])
    if rsi <= 30:
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="RSI",
                direction="BUY",
                strength="weak",
                price=price,
                detail=f"RSI14 超卖 ({rsi:.1f})",
            )
        )
    elif rsi >= 70:
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="RSI",
                direction="SELL",
                strength="weak",
                price=price,
                detail=f"RSI14 超买 ({rsi:.1f})",
            )
        )

    if price >= float(cur["high_20"]) * 0.998:
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="BREAKOUT",
                direction="BUY",
                strength="strong",
                price=price,
                detail="突破 20 日高点",
            )
        )
    elif price <= float(cur["low_20"]) * 1.002:
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="BREAKOUT",
                direction="SELL",
                strength="strong",
                price=price,
                detail="跌破 20 日低点",
            )
        )

    vol_ma = float(cur["vol_ma20"])
    if vol_ma > 0 and float(cur["volume"]) >= vol_ma * 1.8:
        direction = "BUY" if float(cur["pctChg"]) >= 0 else "SELL"
        signals.append(
            Signal(
                code=code,
                name=name,
                signal_type="VOLUME_SPIKE",
                direction=direction,
                strength="medium",
                price=price,
                detail=f"成交量放大至 20 日均量 {float(cur['volume']) / vol_ma:.1f}x",
            )
        )

    return signals
