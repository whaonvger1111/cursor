#!/usr/bin/env python3
"""
中国 A 股：基于公开行情数据的筛选与简易技术分析。

重要说明（必读）：
- 本脚本仅为教育与研究用途，输出不构成投资建议；证券投资有风险，决策须自负。
- 数据来源为第三方接口，可能存在延迟、缺失或变更；买入/卖出时点为规则化启发式，非保证盈利。

A 股交易时间（北京时间）：周一至周五 9:30–11:30、13:00–15:00（法定节假日除外）。
建议在交易日盘中或收盘后运行以获取较新行情；若需每日 9:30 自动运行，可用 cron 在 9:35 左右执行
（留出行情更新时间），时区设为 Asia/Shanghai。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

try:
    import akshare as ak
except ImportError as e:  # pragma: no cover
    print("请先安装依赖: pip install akshare pandas", file=sys.stderr)
    raise SystemExit(1) from e


DISCLAIMER = (
    "【免责声明】本输出基于公开数据与简单技术指标，不构成任何投资建议；"
    "请勿将本结果作为唯一决策依据。"
)


def _retry_call(fn, retries: int = 4, base_sleep: float = 1.5):
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — 网络/API 不稳定
            last = e
            time.sleep(base_sleep * (2**attempt))
    if last:
        raise last
    raise RuntimeError("retry failed")


def fetch_spot_a_em() -> pd.DataFrame:
    """东方财富 A 股实时行情（全市场）。"""

    def _():
        return ak.stock_zh_a_spot_em()

    return _retry_call(_)


def fetch_daily_hist(symbol: str, days: int = 120) -> pd.DataFrame:
    """前复权日线，symbol 为 6 位代码如 600519。"""

    end = datetime.now()
    start = end - timedelta(days=days + 30)
    start_s = start.strftime("%Y%m%d")

    def _():
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_s,
            adjust="qfq",
        )

    df = _retry_call(_)
    if df is None or df.empty:
        return pd.DataFrame()
    # 统一列名
    rename = {
        "日期": "date",
        "收盘": "close",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "换手率": "turnover_rate",
    }
    for k, v in rename.items():
        if k in df.columns:
            df = df.rename(columns={k: v})
    if "close" not in df.columns:
        return pd.DataFrame()
    df = df.sort_values("date").reset_index(drop=True)
    return df


def filter_tradable_spot(df: pd.DataFrame) -> pd.DataFrame:
    """剔除明显异常、ST、退市等（启发式）。"""
    if df.empty:
        return df
    out = df.copy()
    name_col = "名称" if "名称" in out.columns else None
    ref = (
        pd.to_numeric(out["最新价"], errors="coerce")
        if "最新价" in out.columns
        else pd.Series(float("nan"), index=out.index)
    )
    if "昨收" in out.columns:
        ref = ref.fillna(pd.to_numeric(out["昨收"], errors="coerce"))
    out["参考价"] = ref
    # 部分数据源在非交易时段「最新价」全空，用昨收仍可筛除无效行
    out = out[out["参考价"].notna() & (out["参考价"] > 0)]
    if name_col:
        s = out[name_col].astype(str)
        mask_st = ~(s.str.contains("ST", case=False, regex=False) | s.str.contains("退", regex=False))
        out = out[mask_st]
    return out


def cross_section_score(df: pd.DataFrame) -> pd.DataFrame:
    """横截面打分：当日涨跌、流动性/动量代理、换手。

    当「量比」或「最新价」在数据源中缺失时，用「60日涨跌幅」等列替代，避免得分全为常数。
    """
    x = df.copy()
    for c in ["涨跌幅", "量比", "换手率", "60日涨跌幅", "年初至今涨跌幅"]:
        if c not in x.columns:
            x[c] = float("nan")
        x[c] = pd.to_numeric(x[c], errors="coerce")

    def norm(s: pd.Series) -> pd.Series:
        lo, hi = s.quantile(0.05), s.quantile(0.95)
        if hi <= lo:
            return pd.Series(0.5, index=s.index)
        return ((s.clip(lo, hi) - lo) / (hi - lo)).fillna(0.5)

    x["_m"] = norm(x["涨跌幅"])
    vol_ratio_ok = x["量比"].notna().sum() > max(50, int(0.05 * len(x)))
    if vol_ratio_ok:
        x["_v"] = norm(x["量比"].fillna(x["量比"].median()))
    else:
        # 量比缺失时用中期动量近似「相对强弱」（仍非预测收益）
        mom = x["60日涨跌幅"].fillna(x["年初至今涨跌幅"])
        x["_v"] = norm(mom)
    x["_t"] = norm(x["换手率"].fillna(0))
    x["score_cross"] = 0.40 * x["_m"] + 0.35 * x["_v"] + 0.25 * x["_t"]
    return x


@dataclass
class TechSignal:
    code: str
    name: str
    ma5: float | None
    ma20: float | None
    rsi14: float | None
    buy_hint: str
    sell_hint: str


def compute_rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    v = rsi.iloc[-1]
    if pd.isna(v):
        return None
    return float(v)


def technical_signals_for_symbol(code: str, name: str) -> TechSignal | None:
    hist = fetch_daily_hist(code, days=120)
    if hist.empty or len(hist) < 25:
        return TechSignal(
            code, name, None, None, None,
            "历史数据不足，无法判断趋势。",
            "历史数据不足。",
        )
    c = pd.to_numeric(hist["close"], errors="coerce")
    ma5 = float(c.tail(5).mean())
    ma20 = float(c.tail(20).mean())
    rsi = compute_rsi(c, 14)
    last = float(c.iloc[-1])

    buy_parts: list[str] = []
    sell_parts: list[str] = []

    if ma5 > ma20:
        buy_parts.append("短期均线位于中期均线上方，趋势偏多。")
    else:
        sell_parts.append("短期均线位于中期均线下方，趋势偏空或震荡。")

    if last > ma5:
        buy_parts.append("收盘价站上5日均线，短线相对强势。")
    elif last < ma5:
        sell_parts.append("收盘价跌破5日均线，短线转弱信号。")

    if rsi is not None:
        if rsi < 35:
            buy_parts.append(f"RSI(14)≈{rsi:.1f}，处于超卖区域附近，注意反弹与假突破风险。")
        elif rsi > 70:
            sell_parts.append(f"RSI(14)≈{rsi:.1f}，处于超买区域附近，注意获利了结与追高风险。")
        else:
            buy_parts.append(f"RSI(14)≈{rsi:.1f}，未处于极端区域。")

    # 盘中时点建议（规则化文字）
    buy_time = (
        "若看多：可考虑在交易日 9:30–10:00 观察开盘方向与量比，"
        "或 14:30 后结合当日均线位置再决定是否分批；避免盲目追涨停。"
    )
    sell_time = (
        "若止盈/止损：可设置跌破5日均线或前一日低点作为离场参考；"
        "急涨后可关注 13:00–14:30 是否放量滞涨。"
    )

    buy_hint = " ".join(buy_parts) + " " + buy_time if buy_parts else buy_time
    sell_hint = " ".join(sell_parts) + " " + sell_time if sell_parts else sell_time

    return TechSignal(
        code=code,
        name=name,
        ma5=ma5,
        ma20=ma20,
        rsi14=rsi,
        buy_hint=buy_hint,
        sell_hint=sell_hint,
    )


def run_screen(top_n: int = 15) -> dict[str, Any]:
    spot = fetch_spot_a_em()
    spot = filter_tradable_spot(spot)
    spot = cross_section_score(spot)
    spot = spot.sort_values("score_cross", ascending=False).head(top_n)

    code_col = "代码" if "代码" in spot.columns else spot.columns[1]
    name_col = "名称" if "名称" in spot.columns else spot.columns[2]

    picks: list[dict[str, Any]] = []
    for _, row in spot.iterrows():
        code = str(row[code_col]).zfill(6)
        name = str(row[name_col])
        ts = technical_signals_for_symbol(code, name)
        if ts is None:
            continue
        item = {
            "code": code,
            "name": name,
            "latest_snapshot": row.to_dict(),
            "technical": asdict(ts),
        }
        picks.append(item)
        time.sleep(0.35)  # 略限流，降低接口压力

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "timezone_note": "本机时间；分析 A 股请使用北京时间理解交易时段。",
        "disclaimer": DISCLAIMER,
        "top_n": top_n,
        "picks": picks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="A 股筛选与简易技术分析")
    parser.add_argument("--top", type=int, default=12, help="推荐关注股票数量（默认 12）")
    parser.add_argument(
        "--json",
        action="store_true",
        help="仅输出 JSON，便于定时任务落盘",
    )
    args = parser.parse_args()

    result = run_screen(top_n=args.top)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    print(DISCLAIMER)
    print(f"生成时间: {result['generated_at']}")
    print()
    for i, p in enumerate(result["picks"], 1):
        t = p["technical"]
        print(f"【{i}】 {t['code']} {t['name']}")
        print(f"    MA5={t['ma5']}, MA20={t['ma20']}, RSI(14)={t['rsi14']}")
        print(f"    买入参考: {t['buy_hint']}")
        print(f"    卖出/风控: {t['sell_hint']}")
        print()


if __name__ == "__main__":
    main()
