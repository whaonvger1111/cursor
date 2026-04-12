#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股日线级技术面筛选（非投资建议）。

数据来源：公开行情（akshare）。分析基于「前一交易日及更早」的日线收盘价；
盘中 9:30 起可对照当日分时与盘口自行决策。不构成任何买入/卖出保证。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError as e:  # pragma: no cover
    print("请先安装依赖: pip install -r requirements.txt", file=sys.stderr)
    raise e


CN_TZ = ZoneInfo("Asia/Shanghai")

# 默认观察列表：可按需修改或通过 --symbols 传入
DEFAULT_SYMBOLS = (
    "000001",  # 平安银行
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "601318",  # 中国平安
    "600036",  # 招商银行
)


@dataclass
class SymbolSignal:
    symbol: str
    name: str
    last_trade_date: str
    close: float
    ma5: float
    ma20: float
    rsi14: float | None
    trend: str
    action_hint: str
    buy_time_hint: str
    sell_time_hint: str
    notes: str


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _fetch_daily(symbol: str, lookback_days: int = 120) -> pd.DataFrame:
    """拉取前复权日线。"""
    end = datetime.now(CN_TZ).date()
    start = pd.Timestamp(end) - pd.Timedelta(days=lookback_days * 2)
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=pd.Timestamp(end).strftime("%Y%m%d"),
        adjust="qfq",
    )
    if df is None or df.empty:
        raise ValueError(f"无行情数据: {symbol}")
    # 列名兼容
    col_map = {c: str(c).strip() for c in df.columns}
    df = df.rename(columns=col_map)
    date_col = "日期" if "日期" in df.columns else df.columns[0]
    close_col = "收盘" if "收盘" in df.columns else None
    if close_col is None:
        for cand in ("收盘", "close", "Close"):
            if cand in df.columns:
                close_col = cand
                break
    if close_col is None:
        raise ValueError(f"无法识别收盘价列: {list(df.columns)}")
    out = df[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"])
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna().sort_values("date").tail(lookback_days)
    return out.reset_index(drop=True)


def _stock_name(symbol: str) -> str:
    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        if info is not None and not info.empty and "value" in info.columns:
            row = info[info["item"] == "股票简称"]
            if not row.empty:
                return str(row["value"].iloc[0])
    except Exception:
        pass
    return symbol


def analyze_symbol(symbol: str, lookback_days: int) -> SymbolSignal:
    hist = _fetch_daily(symbol, lookback_days=lookback_days)
    close = hist["close"]
    ma5 = close.rolling(5, min_periods=5).mean()
    ma20 = close.rolling(20, min_periods=20).mean()
    rsi = _rsi(close, 14)

    last_date = hist["date"].iloc[-1].strftime("%Y-%m-%d")
    c = float(close.iloc[-1])
    m5 = float(ma5.iloc[-1])
    m20 = float(ma20.iloc[-1])
    r = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None

    # 趋势与简单规则（教育用途）
    if m5 > m20 * 1.002:
        trend = "短期均线位于长期均线上方（偏多）"
    elif m5 < m20 * 0.998:
        trend = "短期均线位于长期均线下方（偏空）"
    else:
        trend = "短期与长期均线纠缠（震荡）"

    action_hint = "观望/仅观察"
    notes_parts: list[str] = []

    if r is not None:
        if r >= 70:
            notes_parts.append(f"RSI≈{r:.1f} 进入常见超买区，注意追高风险。")
        elif r <= 30:
            notes_parts.append(f"RSI≈{r:.1f} 进入常见超卖区，注意反弹与基本面风险。")

    if m5 > m20 and (r is None or r < 68):
        action_hint = "技术面偏强：可关注回踩均线或突破后的跟随（非建议）"
    elif m5 < m20 and (r is None or r > 35):
        action_hint = "技术面偏弱：宜谨慎，等待均线走平或放量扭转（非建议）"
    else:
        action_hint = "震荡：可等待方向明朗（非建议）"

    name = _stock_name(symbol)

    buy_time_hint = (
        "A股连续竞价时段 09:30–11:30、13:00–15:00；集合竞价 09:15–09:25 决定开盘价。"
        "日线信号通常用于「收盘后」制定次日预案，而非保证开盘即买。"
    )
    sell_time_hint = (
        "若持筹需减仓：常见做法是在冲高无力、跌破关键均线或止损位时分批处理；"
        "尾盘 14:30 后流动性变化亦常被用于择时，但仍需结合个股与风险承受力。"
    )

    notes = "；".join(notes_parts) if notes_parts else "无额外提示。"

    return SymbolSignal(
        symbol=symbol,
        name=name,
        last_trade_date=last_date,
        close=c,
        ma5=m5,
        ma20=m20,
        rsi14=r,
        trend=trend,
        action_hint=action_hint,
        buy_time_hint=buy_time_hint,
        sell_time_hint=sell_time_hint,
        notes=notes,
    )


def _should_run_now(force: bool) -> tuple[bool, str]:
    if force:
        return True, "已使用 --force，跳过交易时段检查。"
    now = datetime.now(CN_TZ)
    # 工作日周一到周五
    if now.weekday() >= 5:
        return False, "当前为周末，A股休市；可用 --force 仍生成报告。"
    t = now.time()
    open_morning = datetime.strptime("09:30", "%H:%M").time()
    # 允许 9:25 之后视为「开盘前后」可运行
    early = datetime.strptime("09:25", "%H:%M").time()
    close_afternoon = datetime.strptime("15:00", "%H:%M").time()
    if early <= t <= close_afternoon:
        return True, "当前处于 A 股常规交易时段（含 9:30 开盘后）。"
    return False, (
        f"当前北京时间 {now.strftime('%H:%M')} 不在常规交易窗口 "
        f"（建议 09:30–15:00 运行，或使用 --force）。"
    )


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="A 股日线技术面简报（非投资建议）")
    p.add_argument(
        "--symbols",
        type=str,
        default=",".join(DEFAULT_SYMBOLS),
        help="逗号分隔 6 位代码，如 000001,600519",
    )
    p.add_argument("--lookback", type=int, default=120, help="拉取日线大致天数")
    p.add_argument(
        "--force",
        action="store_true",
        help="非交易时段也运行（便于测试与盘后生成）",
    )
    p.add_argument("--json-out", type=str, default="", help="可选：写入 JSON 文件路径")
    args = p.parse_args(list(argv) if argv is not None else None)

    ok_time, time_msg = _should_run_now(args.force)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    header = (
        "【免责声明】本脚本仅根据公开历史价格做简单技术指标展示，不构成投资建议，"
        "不预测收益，不对任何损失负责。入市有风险，决策请自负。\n"
        f"【运行信息】{time_msg} 北京时间：{datetime.now(CN_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
    )
    print(header)

    if not ok_time and not args.force:
        print("提示：默认仅在交易日 09:25–15:00（北京时间）输出完整分析；请加 --force 绕过。")
        return 0

    results: list[dict[str, Any]] = []
    for sym in symbols:
        try:
            sig = analyze_symbol(sym, lookback_days=args.lookback)
            results.append(asdict(sig))
            print(f"--- {sig.name} ({sig.symbol}) 截至 {sig.last_trade_date} ---")
            rsi_s = f"{sig.rsi14:.2f}" if sig.rsi14 is not None else "N/A"
            print(
                f"收盘: {sig.close:.3f}  MA5: {sig.ma5:.3f}  MA20: {sig.ma20:.3f}  RSI14: {rsi_s}"
            )
            print(f"趋势: {sig.trend}")
            print(f"摘要: {sig.action_hint}")
            print(f"买入时间参考: {sig.buy_time_hint}")
            print(f"卖出时间参考: {sig.sell_time_hint}")
            print(f"备注: {sig.notes}\n")
        except Exception as ex:  # pragma: no cover - 网络/字段变化
            print(f"[错误] {sym}: {ex}\n", file=sys.stderr)

    if args.json_out:
        path = args.json_out
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"已写入: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
