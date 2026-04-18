#!/usr/bin/env python3
"""
中国 A 股日线级「交易辅助」分析脚本。

设计用途：在交易日盘中/盘后拉取公开行情，给出候选标的与基于均线/RSI 的
观察性买卖时机提示。不构成投资建议。

典型用法（北京时间每个交易日 9:30 之后由计划任务执行）::

    python3 -m trading_agent.a_share_daily_analysis --top 10

数据源：AkShare（东方财富等公开接口），可能因网络或接口变更失败。
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError as e:  # pragma: no cover
    print("请先安装依赖: pip install akshare pandas numpy", file=sys.stderr)
    raise e


DISCLAIMER = """
【重要声明】本输出由公开行情数据经简单规则引擎生成，仅供学习研究，不构成
证券投资建议。买卖决策请咨询持牌机构或自行承担风险。
"""


@dataclass
class TimingResult:
    code: str
    name: str
    action_hint: str
    detail: str


def _to_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce")


def _fetch_spot() -> pd.DataFrame:
    """全市场 A 股实时快照（耗时约 2～3 分钟）。"""
    df = ak.stock_zh_a_spot_em()
    return df


def _clean_universe(df: pd.DataFrame) -> pd.DataFrame:
    """剔除 ST、退市等高风险名称过滤。"""
    if "名称" not in df.columns:
        return df
    name = df["名称"].astype(str)
    mask = ~(name.str.contains("ST", case=False, na=False) | name.str.contains("退", na=False))
    return df.loc[mask].copy()


def _score_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """基于流动性 + 动量 + 量能的简易综合分（横截面标准化）。"""
    need = ["成交额", "量比", "换手率", "60日涨跌幅", "年初至今涨跌幅"]
    for c in need:
        if c not in df.columns:
            raise ValueError(f"行情表缺少列: {c}")

    work = df.copy()
    work["_amt"] = _to_float(work["成交额"])
    work["_lb"] = _to_float(work["量比"])
    work["_tr"] = _to_float(work["换手率"])
    work["_60"] = _to_float(work["60日涨跌幅"])
    work["_ytd"] = _to_float(work["年初至今涨跌幅"])

    work = work.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["_amt", "_lb", "_tr", "_60", "_ytd"]
    )
    # 流动性：成交额处于全市场前段（例如前 30%）
    amt_thr = work["_amt"].quantile(0.70)
    work = work[work["_amt"] >= amt_thr]

    def _z(col: str) -> pd.Series:
        x = work[col]
        mu, sigma = x.mean(), x.std()
        if sigma == 0 or np.isnan(sigma):
            return x * 0.0
        return (x - mu) / sigma

    # 动量偏多：60 日、YTD 为正贡献；量能适中偏多（过高可能是短线过热）
    z60 = _z("_60")
    zytd = _z("_ytd")
    zlb = _z("_lb")
    ztr = _z("_tr")
    # 量比、换手：取适中，惩罚极端 z（绝对值 > 2 时降权）
    def _clip_penalty(z: pd.Series) -> pd.Series:
        a = z.abs()
        return z.where(a <= 2.0, z * 0.5)

    zlb2 = _clip_penalty(zlb)
    ztr2 = _clip_penalty(ztr)

    work["_score"] = 0.35 * z60 + 0.25 * zytd + 0.22 * zlb2 + 0.18 * ztr2
    return work.sort_values("_score", ascending=False)


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _load_daily(symbol: str, lookback_days: int = 200, max_retries: int = 3) -> pd.DataFrame:
    end = datetime.now().date()
    start = end - timedelta(days=lookback_days * 2)
    last_err: Exception | None = None
    df: pd.DataFrame | None = None
    for attempt in range(1, max_retries + 1):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            break
        except Exception as e:  # pragma: no cover
            last_err = e
            if attempt == max_retries:
                raise RuntimeError(f"历史 K 线拉取失败: {symbol}") from last_err
            time.sleep(min(4 * attempt, 20))

    if df is None or df.empty:
        raise RuntimeError(f"无历史数据: {symbol}")
    df["收盘"] = _to_float(df["收盘"])
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").tail(lookback_days)
    return df


def analyze_timing(symbol: str, name: str = "") -> TimingResult:
    """基于日线 MA5/MA20 与 RSI 的观察性提示。"""
    hist = _load_daily(symbol)
    close = hist["收盘"]
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    rsi = _rsi(close, 14)

    last = hist.iloc[-1]
    c = float(last["收盘"])
    m5 = float(ma5.iloc[-1])
    m20 = float(ma20.iloc[-1])
    r = float(rsi.iloc[-1])

    parts: list[str] = []
    parts.append(f"收盘 {c:.2f} | MA5 {m5:.2f} | MA20 {m20:.2f} | RSI(14) {r:.1f}")

    # 规则：偏趋势 + 超买超卖
    if m5 > m20 and c >= m20:
        trend = "短期均线位于中期均线上方，趋势偏强。"
        hint = "持有/关注"
    elif m5 < m20 and c < m20:
        trend = "短期均线位于中期均线下方，趋势偏弱。"
        hint = "观望/减仓观察"
    else:
        trend = "长短期均线交织，可能处于震荡或变盘阶段。"
        hint = "观望/等待方向确认"

    parts.append(trend)

    if r < 35:
        parts.append("RSI 偏低：若基本面与趋势未破坏，可关注分批买入窗口（需自行设定止损）。")
        hint = hint + " | RSI 超卖区"
    elif r > 70:
        parts.append("RSI 偏高：短线过热，可关注止盈或减仓节奏。")
        hint = hint + " | RSI 超买区"

    # 下一交易日「时点」：仅为流程性提示（非精确到分钟的建议）
    parts.append(
        "下一交易日：集合竞价后观察开盘量能与 MA5/MA20 相对位置；"
        "若计划买入，常见做法是等待回踩 MA5 附近缩量企稳再分批；"
        "若计划卖出，常见做法是冲高量能背离或跌破 MA5 时考虑减仓。"
    )

    return TimingResult(code=symbol, name=name, action_hint=hint, detail="\n".join(parts))


def run_analysis(top: int, max_retries: int = 3) -> int:
    print(f"=== A 股日线分析 @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    print(DISCLAIMER.strip() + "\n")

    spot = None
    for attempt in range(1, max_retries + 1):
        try:
            spot = _fetch_spot()
            break
        except Exception as e:  # pragma: no cover
            print(f"拉取快照失败 ({attempt}/{max_retries}): {e}")
            time.sleep(min(4 * attempt, 30))

    if spot is None:
        print("无法获取全市场行情，请检查网络或稍后重试。")
        return 1

    uni = _clean_universe(spot)
    try:
        ranked = _score_candidates(uni)
    except Exception as e:
        print(f"评分失败: {e}")
        return 1

    cols_show = [c for c in ["代码", "名称", "最新价", "涨跌幅", "成交额", "量比", "60日涨跌幅"] if c in ranked.columns]
    top_df = ranked.head(top)
    print(f"候选标的（按综合得分排序，共展示 {len(top_df)} 只）:\n")
    print(top_df[cols_show + ["_score"]].to_string(index=False))
    print("\n--- 分时/日线级「时点」提示（基于最近日线） ---\n")

    for _, row in top_df.iterrows():
        code = str(row["代码"])
        name = str(row.get("名称", ""))
        try:
            tr = analyze_timing(code, name)
            print(f"【{tr.code} {tr.name}】 {tr.action_hint}")
            print(tr.detail)
            print()
        except Exception as e:
            print(f"【{code} {name}】 分析失败: {e}\n")

    print("说明：A 股连续竞价通常 09:30 开始；本脚本使用日线与快照，无法替代 Level-2 或tick 级决策。")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="中国 A 股日线辅助分析（非投资建议）")
    p.add_argument("--top", type=int, default=10, help="输出前 N 只候选股并做深度分析")
    p.add_argument("--retries", type=int, default=3, help="网络失败重试次数")
    args = p.parse_args(argv)
    return run_analysis(top=args.top, max_retries=args.retries)


if __name__ == "__main__":
    raise SystemExit(main())
