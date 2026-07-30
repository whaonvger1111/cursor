"""Technical indicators for A-share signal monitoring."""

from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["close"]

    for window in (5, 10, 20, 60):
        out[f"ma{window}"] = close.rolling(window).mean()

    ema12 = ema(close, 12)
    ema26 = ema(close, 26)
    out["macd_dif"] = ema12 - ema26
    out["macd_dea"] = ema(out["macd_dif"], 9)
    out["macd_hist"] = 2 * (out["macd_dif"] - out["macd_dea"])

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["rsi14"] = 100 - (100 / (1 + rs))

    out["vol_ma20"] = out["volume"].rolling(20).mean()
    out["high_20"] = out["high"].rolling(20).max()
    out["low_20"] = out["low"].rolling(20).min()
    return out
