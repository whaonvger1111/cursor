from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd


@dataclass
class QuoteBundle:
    symbol: str
    history: pd.DataFrame
    error: Optional[str] = None


def _is_a_share_code(symbol: str) -> bool:
    return len(symbol) == 6 and symbol.isdigit()


def _fetch_a_share_history(symbol: str, lookback_days: int) -> QuoteBundle:
    try:
        import akshare as ak  # type: ignore
    except ImportError as e:
        return QuoteBundle(symbol, pd.DataFrame(), error=f"缺少 akshare: {e}")

    last_err: str | None = None
    for attempt in range(3):
        try:
            days = max(int(lookback_days), 30)
            end = datetime.now(timezone.utc).date()
            start = end - timedelta(days=days + 60)
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if df is None or df.empty:
                return QuoteBundle(symbol, pd.DataFrame(), error="无行情数据")
            # akshare 列名：日期, 开盘, 收盘, 最高, 最低, 成交量, ...
            col_date = "日期" if "日期" in df.columns else df.columns[0]
            rename = {
                col_date: "Date",
                "开盘": "Open",
                "收盘": "Close",
                "最高": "High",
                "最低": "Low",
                "成交量": "Volume",
            }
            for k in rename:
                if k not in df.columns:
                    return QuoteBundle(
                        symbol, pd.DataFrame(), error=f"行情列缺失: {k}"
                    )
            out = df.rename(columns=rename)[
                ["Date", "Open", "High", "Low", "Close", "Volume"]
            ].copy()
            out["Date"] = pd.to_datetime(out["Date"])
            out = out.sort_values("Date").reset_index(drop=True)
            for c in ("Open", "High", "Low", "Close", "Volume"):
                out[c] = pd.to_numeric(out[c], errors="coerce")
            out = out.dropna(subset=["Close"])
            if out.empty:
                return QuoteBundle(symbol, pd.DataFrame(), error="收盘价无效")
            return QuoteBundle(symbol, out)
        except Exception as e:
            last_err = str(e)
            if attempt < 2:
                time.sleep(2 ** attempt)
    return QuoteBundle(symbol, pd.DataFrame(), error=last_err or "未知错误")


def _fetch_yfinance_history(symbol: str, lookback_days: int) -> QuoteBundle:
    try:
        import yfinance as yf
    except ImportError as e:
        return QuoteBundle(symbol, pd.DataFrame(), error=f"缺少 yfinance: {e}")
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=f"{max(lookback_days, 5)}d", auto_adjust=True)
        if hist is None or hist.empty:
            return QuoteBundle(symbol, pd.DataFrame(), error="无价格数据")
        return QuoteBundle(symbol, hist)
    except Exception as e:
        return QuoteBundle(symbol, pd.DataFrame(), error=str(e))


def fetch_history(symbol: str, lookback_days: int) -> QuoteBundle:
    """A 股 6 位代码用 akshare；否则回退 yfinance（如美股代码）。"""
    if _is_a_share_code(symbol):
        return _fetch_a_share_history(symbol, lookback_days)
    return _fetch_yfinance_history(symbol, lookback_days)
