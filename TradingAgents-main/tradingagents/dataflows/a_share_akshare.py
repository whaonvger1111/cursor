"""
China A-share market data via AkShare (Eastmoney / Sina aggregators).

Used when `data_vendors` is set to `akshare` or when `auto` routing selects A-shares.
AkShare depends on third-party sites; failures may occur during market hours or maintenance.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Annotated, Optional

import pandas as pd

from .a_share_symbols import is_a_share_symbol, parse_yahoo_style_symbol, to_em_symbol

_AK_MAX_RETRIES = 3
_AK_BASE_DELAY = 1.5


def _with_retry(func, *args, **kwargs):
    last_err: Optional[Exception] = None
    for attempt in range(_AK_MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < _AK_MAX_RETRIES - 1:
                time.sleep(_AK_BASE_DELAY * (2**attempt))
    raise last_err  # type: ignore[misc]


def _import_akshare():
    try:
        import akshare as ak  # noqa: WPS433
    except ImportError as e:
        raise RuntimeError(
            "AkShare is not installed. Install with: pip install akshare"
        ) from e
    return ak


def _code_6(symbol: str) -> str:
    code, _ = parse_yahoo_style_symbol(symbol)
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"Expected 6-digit A-share code, got: {symbol!r}")
    return code


def download_akshare_ohlcv(symbol: str, start_str: str, end_str: str) -> pd.DataFrame:
    """
    Fetch daily OHLCV for an A-share into a DataFrame compatible with stockstats.

    start_str / end_str: YYYY-MM-DD.
    """
    if not is_a_share_symbol(symbol):
        raise ValueError(f"Expected A-share symbol, got {symbol!r}")
    ak = _import_akshare()
    code = _code_6(symbol)
    start = start_str.replace("-", "")
    end = end_str.replace("-", "")
    df = _with_retry(
        ak.stock_zh_a_hist,
        symbol=code,
        period="daily",
        start_date=start,
        end_date=end,
        adjust="qfq",
    )
    if df is None or df.empty:
        return pd.DataFrame()
    out = pd.DataFrame(
        {
            "Date": pd.to_datetime(df["日期"]),
            "Open": df["开盘"],
            "High": df["最高"],
            "Low": df["最低"],
            "Close": df["收盘"],
            "Adj Close": df["收盘"],
            "Volume": df["成交量"],
        }
    )
    for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["Close"])
    out["Date"] = out["Date"].dt.tz_localize(None)
    return out


def get_stock_data(
    symbol: Annotated[str, "A-share symbol, e.g. 600519.SS or 000001.SZ"],
    start_date: Annotated[str, "Start date yyyy-mm-dd"],
    end_date: Annotated[str, "End date yyyy-mm-dd"],
) -> str:
    """Daily OHLCV for A-shares (forward-adjusted by default for comparability)."""
    if not is_a_share_symbol(symbol):
        raise ValueError(f"akshare get_stock_data expects an A-share symbol, got {symbol!r}")
    out = download_akshare_ohlcv(symbol, start_date, end_date)
    if out.empty:
        return (
            f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        )
    csv_string = out.to_csv(index=False)
    header = f"# Stock data for {symbol} from {start_date} to {end_date} (AkShare, qfq)\n"
    header += f"# Total records: {len(out)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + csv_string


def get_indicators(
    symbol: Annotated[str, "A-share symbol"],
    indicator: Annotated[str, "stockstats indicator name"],
    curr_date: Annotated[str, "YYYY-mm-dd"],
    look_back_days: Annotated[int, "calendar days lookback"],
) -> str:
    """Delegates to the same indicator logic as yfinance by using unified load_ohlcv."""
    from .y_finance import get_stock_stats_indicators_window

    return get_stock_stats_indicators_window(symbol, indicator, curr_date, look_back_days)


def get_fundamentals(
    ticker: Annotated[str, "A-share symbol"],
    curr_date: Annotated[str, "unused, AkShare returns latest snapshot"] = None,
) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(f"akshare fundamentals expect an A-share symbol, got {ticker!r}")
    ak = _import_akshare()
    code = _code_6(ticker)
    df = _with_retry(ak.stock_individual_info_em, symbol=code)
    if df is None or df.empty:
        return f"No fundamentals data found for symbol '{ticker}'"
    lines = [f"# A-share snapshot (AkShare / Eastmoney) for {ticker}\n"]
    for _, row in df.iterrows():
        lines.append(f"{row['item']}: {row['value']}")
    lines.append(
        f"\n# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return "\n".join(lines)


def _filter_report_df(df: pd.DataFrame, curr_date: Optional[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if not curr_date or "REPORT_DATE" not in df.columns:
        return df
    cutoff = pd.Timestamp(curr_date)
    d = df.copy()
    d["REPORT_DATE"] = pd.to_datetime(d["REPORT_DATE"], errors="coerce")
    d = d[d["REPORT_DATE"] <= cutoff].sort_values("REPORT_DATE", ascending=False)
    return d.head(24)


def get_balance_sheet(
    ticker: Annotated[str, "A-share symbol"],
    freq: Annotated[str, "ignored for AkShare EM; reports are as published"] = "quarterly",
    curr_date: Annotated[str, "drop reports after this date"] = None,
) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(f"akshare balance sheet expects an A-share symbol, got {ticker!r}")
    ak = _import_akshare()
    em = to_em_symbol(ticker)
    df = _with_retry(ak.stock_balance_sheet_by_report_em, symbol=em)
    df = _filter_report_df(df, curr_date)
    if df is None or df.empty:
        return f"No balance sheet data found for symbol '{ticker}'"
    header = f"# Balance Sheet (AkShare EM) for {ticker}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + df.to_csv()


def get_cashflow(
    ticker: Annotated[str, "A-share symbol"],
    freq: Annotated[str, "ignored"] = "quarterly",
    curr_date: Annotated[str, "drop reports after this date"] = None,
) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(f"akshare cashflow expects an A-share symbol, got {ticker!r}")
    ak = _import_akshare()
    em = to_em_symbol(ticker)
    df = _with_retry(ak.stock_cash_flow_sheet_by_report_em, symbol=em)
    df = _filter_report_df(df, curr_date)
    if df is None or df.empty:
        return f"No cash flow data found for symbol '{ticker}'"
    header = f"# Cash Flow Statement (AkShare EM) for {ticker}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + df.to_csv()


def get_income_statement(
    ticker: Annotated[str, "A-share symbol"],
    freq: Annotated[str, "ignored"] = "quarterly",
    curr_date: Annotated[str, "drop reports after this date"] = None,
) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(
            f"akshare income statement expects an A-share symbol, got {ticker!r}"
        )
    ak = _import_akshare()
    em = to_em_symbol(ticker)
    df = _with_retry(ak.stock_profit_sheet_by_report_em, symbol=em)
    df = _filter_report_df(df, curr_date)
    if df is None or df.empty:
        return f"No income statement data found for symbol '{ticker}'"
    header = f"# Income Statement (AkShare EM profit sheet) for {ticker}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + df.to_csv()


def get_news(
    ticker: str,
    start_date: str,
    end_date: str,
) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(f"akshare news expect an A-share symbol, got {ticker!r}")
    ak = _import_akshare()
    code = _code_6(ticker)
    df = _with_retry(ak.stock_news_em, symbol=code)
    if df is None or df.empty:
        return f"No news found for {ticker}"
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    parts = []
    for _, row in df.iterrows():
        t = row.get("发布时间")
        if pd.notna(t):
            try:
                pub = pd.to_datetime(str(t))
                if pub.tzinfo is not None:
                    pub = pub.tz_localize(None)
                if pub.to_pydatetime() < start_dt or pub.to_pydatetime() > end_dt:
                    continue
            except Exception:
                pass
        title = row.get("新闻标题", "")
        body = row.get("新闻内容", "")
        src = row.get("文章来源", "")
        link = row.get("新闻链接", "")
        parts.append(f"### {title} (source: {src})\n{body}\nLink: {link}\n")
    if not parts:
        return f"No news found for {ticker} between {start_date} and {end_date}"
    return (
        f"## {ticker} News (AkShare), from {start_date} to {end_date}:\n\n"
        + "\n".join(parts)
    )


def get_global_news(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 10,
) -> str:
    """Macro-oriented CCTV news for the requested calendar day (Chinese context)."""
    ak = _import_akshare()

    lines: list[str] = []
    curr = datetime.strptime(curr_date, "%Y-%m-%d").date()
    for i in range(max(1, look_back_days)):
        day = (curr - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = _with_retry(ak.news_cctv, date=day)
        except Exception:
            df = None
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            title = row.get("title", "")
            content = row.get("content", "")
            lines.append(f"### {title}\n{content}\n")
            if len(lines) >= limit:
                break
        if len(lines) >= limit:
            break
    if not lines:
        return f"No CCTV macro news returned near {curr_date} (AkShare)."
    return "## China macro news (AkShare CCTV):\n\n" + "\n".join(lines[:limit])


def get_insider_transactions(ticker: str) -> str:
    if not is_a_share_symbol(ticker):
        raise ValueError(
            f"akshare insider/holder changes expect an A-share symbol, got {ticker!r}"
        )
    ak = _import_akshare()
    code = _code_6(ticker)
    df = _with_retry(ak.stock_shareholder_change_ths, symbol=code)
    if df is None or df.empty:
        return f"No shareholder change records found for symbol '{ticker}'"
    header = f"# Major shareholder changes (AkShare / 同花顺) for {ticker}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + df.to_csv(index=False)
