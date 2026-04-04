from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd


@dataclass
class QuoteBundle:
    symbol: str
    history: pd.DataFrame
    error: Optional[str] = None


def fetch_history(symbol: str, lookback_days: int) -> QuoteBundle:
    try:
        import yfinance as yf
    except ImportError as e:
        return QuoteBundle(symbol, pd.DataFrame(), error=f"missing yfinance: {e}")

    try:
        t = yf.Ticker(symbol)
        end = datetime.now(timezone.utc)
        hist = t.history(period=f"{max(lookback_days, 5)}d", auto_adjust=True)
        if hist is None or hist.empty:
            return QuoteBundle(symbol, pd.DataFrame(), error="no price data")
        return QuoteBundle(symbol, hist)
    except Exception as e:
        return QuoteBundle(symbol, pd.DataFrame(), error=str(e))
