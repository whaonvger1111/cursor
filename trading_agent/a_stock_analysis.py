#!/usr/bin/env python3
"""
China A-share daily analysis (runs on end-of-day or latest available bar).

Designed to be invoked after the market opens (e.g. 09:35 Asia/Shanghai) when
yesterday's close is final; intraday quotes are not used here.

Disclaimer: Outputs are heuristic technical signals for research/education only.
They are NOT investment advice. Trading involves substantial risk.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None  # type: ignore


# Default watchlist: large-cap / liquid names for screening (not exhaustive).
DEFAULT_SYMBOLS: list[tuple[str, str]] = [
    ("600519", "贵州茅台"),
    ("601318", "中国平安"),
    ("600036", "招商银行"),
    ("601012", "隆基绿能"),
    ("300750", "宁德时代"),
    ("000858", "五粮液"),
    ("601888", "中国中免"),
    ("600900", "长江电力"),
    ("601166", "兴业银行"),
    ("000333", "美的集团"),
    ("002594", "比亚迪"),
    ("600276", "恒瑞医药"),
    ("600030", "中信证券"),
    ("601328", "交通银行"),
    ("000001", "平安银行"),
]


@dataclass
class SignalResult:
    code: str
    name: str
    score: float
    last_close: float
    ma5: float
    ma20: float
    rsi14: float
    vol_ratio: float
    buy_hint: str
    sell_hint: str
    notes: str


def _ensure_akshare() -> None:
    if ak is None:
        print(
            "缺少依赖 akshare：请执行 pip install akshare",
            file=sys.stderr,
        )
        sys.exit(2)


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def fetch_daily(symbol: str, days: int = 120) -> pd.DataFrame:
    """Fetch adjusted daily OHLCV for one A-share (6-digit code)."""
    _ensure_akshare()
    end = datetime.now().date()
    start = end - timedelta(days=max(days, 60))
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="qfq",
    )
    if df is None or df.empty:
        return pd.DataFrame()
    # Normalize column names (akshare versions differ slightly).
    col_map = {c: str(c).strip() for c in df.columns}
    df = df.rename(columns=col_map)
    # Expected columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, ...
    date_col = "日期" if "日期" in df.columns else df.columns[0]
    close_col = "收盘" if "收盘" in df.columns else None
    vol_col = "成交量" if "成交量" in df.columns else None
    if close_col is None or vol_col is None:
        return pd.DataFrame()
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[date_col]),
            "close": pd.to_numeric(df[close_col], errors="coerce"),
            "volume": pd.to_numeric(df[vol_col], errors="coerce"),
        }
    )
    out = out.dropna().sort_values("date").reset_index(drop=True)
    return out


def analyze_one(code: str, name: str) -> Optional[SignalResult]:
    df = fetch_daily(code)
    if len(df) < 25:
        return None

    close = df["close"]
    vol = df["volume"]
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    rsi14 = _rsi(close, 14)
    vol_ma5 = vol.rolling(5).mean()
    vol_ratio = (vol.iloc[-1] / vol_ma5.iloc[-1]) if vol_ma5.iloc[-1] else 1.0

    c = close.iloc[-1]
    m5 = ma5.iloc[-1]
    m20 = ma20.iloc[-1]
    r = rsi14.iloc[-1]

    # Simple score: trend + momentum + volume participation (clamped).
    trend_score = 0.0
    if c > m5 > m20:
        trend_score = 2.0
    elif c > m20:
        trend_score = 1.0
    elif c < m5 < m20:
        trend_score = -2.0
    elif c < m20:
        trend_score = -1.0

    rsi_score = 0.0
    if r < 35:
        rsi_score = 1.0  # oversold bounce potential
    elif r > 70:
        rsi_score = -1.0  # overbought risk

    vol_bonus = 0.5 if vol_ratio > 1.2 else (-0.3 if vol_ratio < 0.7 else 0.0)
    score = float(np.clip(trend_score + rsi_score + vol_bonus, -4, 4))

    buy_parts: list[str] = []
    sell_parts: list[str] = []
    if c > m20 and close.iloc[-2] <= ma20.iloc[-2]:
        buy_parts.append("收盘上穿20日均线，可留意趋势转强后的回踩确认")
    if r < 40 and c >= m5:
        buy_parts.append("RSI偏低且价格未有效破位，可结合板块与基本面关注左侧机会")
    if vol_ratio > 1.15 and c > m5:
        buy_parts.append("放量站上短期均线，可作为短线关注信号（需设止损）")

    if c < m5 and m5 < m20:
        sell_parts.append("价格处在5日/20日均线下方，趋势偏弱，减仓或观望")
    if r > 75:
        sell_parts.append("RSI偏高，短线过热，考虑分批止盈或收紧止损")
    if close.iloc[-2] >= ma5.iloc[-2] and c < m5:
        sell_parts.append("收盘跌破5日均线，短线或转弱")

    buy_hint = "；".join(buy_parts) if buy_parts else "暂无明确买入信号，以观望或定投计划为主"
    sell_hint = "；".join(sell_parts) if sell_parts else "暂无强烈卖出信号，仍以趋势与风控为主"

    notes = (
        f"最新收盘 {c:.2f}，MA5={m5:.2f}，MA20={m20:.2f}，"
        f"RSI14={r:.1f}，量比(量/5日均量)={vol_ratio:.2f}"
    )

    return SignalResult(
        code=code,
        name=name,
        score=score,
        last_close=c,
        ma5=m5,
        ma20=m20,
        rsi14=r,
        vol_ratio=vol_ratio,
        buy_hint=buy_hint,
        sell_hint=sell_hint,
        notes=notes,
    )


def run_report(symbols: list[tuple[str, str]], top_n: int = 8) -> int:
    results: list[SignalResult] = []
    for code, name in symbols:
        try:
            r = analyze_one(code, name)
            if r is not None:
                results.append(r)
        except Exception as exc:  # noqa: BLE001 — surface data/API issues
            print(f"[跳过] {code} {name}: {exc}", file=sys.stderr)

    if not results:
        print("未能获取有效行情，请检查网络或稍后再试。")
        return 1

    results.sort(key=lambda x: x.score, reverse=True)
    picks = results[:top_n]

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    print("=" * 60)
    print("中国A股 — 日线技术梳理（非投资建议）")
    print(f"生成时间（本地时区）: {now.isoformat(timespec='seconds')}")
    print("说明：基于昨日及历史收盘数据；实盘需结合基本面、资金面与风险偏好。")
    print("=" * 60)

    print("\n【相对评分较高的关注名单】（排序按综合得分，仅作筛选参考）\n")
    for i, r in enumerate(picks, 1):
        print(f"{i}. {r.code} {r.name} | 得分 {r.score:+.2f}")
        print(f"   {r.notes}")
        print(f"   买入观察: {r.buy_hint}")
        print(f"   卖出/风控: {r.sell_hint}")
        print()

    print("【时间与执行提示】")
    print("- 日线策略：多在收盘后复盘；次日集合竞价与开盘后观察是否延续信号。")
    print("- 若 cron 固定在北京时间 09:35 触发：此时可看隔夜外盘与早盘竞价，仍以前一日收盘信号为主轴。")
    print("- 买入时点（思路）：确认趋势（如站稳关键均线）+ 回踩缩量 + 板块未转弱。")
    print("- 卖出时点（思路）：跌破预设止损位、或趋势破坏（如有效跌破 MA20）、或 RSI 极端过热后放量滞涨。")
    print()
    print("风险提示：历史表现不预示未来；请勿将超过承受能力的资金投入股市。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="A-share daily technical screen (akshare).")
    parser.add_argument(
        "--top",
        type=int,
        default=8,
        help="推荐展示前 N 只（按得分）",
    )
    args = parser.parse_args()
    return run_report(DEFAULT_SYMBOLS, top_n=args.top)


if __name__ == "__main__":
    raise SystemExit(main())
