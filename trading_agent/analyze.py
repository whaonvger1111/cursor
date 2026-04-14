from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd

from trading_agent.config import big_move_pct
from trading_agent.fetch_quotes import fetch_history


@dataclass
class SymbolAnalysis:
    symbol: str
    last_close: float | None
    prev_close: float | None
    day_change_pct: float | None
    ma5: float | None
    ma20: float | None
    vs_ma5: str
    vs_ma20: str
    note: str
    recommendation: str
    buy_timing_cn: str
    sell_timing_cn: str
    error: str | None = None


def _last_two_closes(hist: pd.DataFrame) -> tuple[float | None, float | None]:
    if hist.empty or "Close" not in hist.columns:
        return None, None
    closes = hist["Close"].dropna()
    if len(closes) < 1:
        return None, None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    return last, prev


def _ma(hist: pd.DataFrame, window: int) -> float | None:
    if hist.empty or "Close" not in hist.columns:
        return None
    s = hist["Close"].dropna()
    if len(s) < window:
        return None
    return float(s.iloc[-window:].mean())


def _position_vs_ma(price: float | None, ma: float | None) -> str:
    if price is None or ma is None or ma == 0:
        return "n/a"
    if price > ma:
        return "above"
    if price < ma:
        return "below"
    return "at"


def _signals(
    last: float | None,
    prev: float | None,
    ma5: float | None,
    ma20: float | None,
    day_pct: float | None,
    move_threshold: float,
) -> Tuple[str, str, str, List[str]]:
    """返回 (偏多/中性/偏空, 买入时机说明, 卖出时机说明, 备注列表)。"""
    notes: List[str] = []

    if day_pct is not None and abs(day_pct) >= move_threshold:
        notes.append(
            f"单日波动达到阈值（{move_threshold:.1f}%）：{day_pct:+.2f}%，注意流动性与情绪"
        )

    if last is None or ma5 is None or ma20 is None:
        return (
            "数据不足",
            "待数据完整后再判断；A 股连续竞价时段为 9:30–11:30、13:00–15:00。",
            "同上。",
            notes,
        )

    bull_stack = last > ma5 > ma20
    bear_stack = last < ma5 < ma20
    above_ma20 = last > ma20

    if bull_stack and (day_pct is None or day_pct >= 0):
        rec = "偏多"
        buy = (
            "开盘后若回踩 MA5 附近缩量企稳，可结合板块与大盘分时再考虑分批；"
            "避免盲目追高远离均线的拉升。"
        )
        sell = (
            "若收盘有效跌破 MA5 或单日放量长上影，可视为短线止盈/减仓信号；"
            "趋势未破前可部分仓位滚动。"
        )
        notes.append("收盘站上 MA5 且 MA5>MA20，短线偏强")
    elif bear_stack:
        rec = "偏空"
        buy = (
            "宜观望或等待重新站上 MA20 并伴随量能配合；"
            "若仅博反弹，可关注急跌后分时企稳，严格止损。"
        )
        sell = (
            "反抽至 MA5/MA10 承压、量能不济时，可作为减仓或止损观察点；"
            "跌破前低且放量宜谨慎。"
        )
        notes.append("收盘位于 MA5 下方且 MA5<MA20，短线偏弱")
    elif above_ma20:
        rec = "中性偏强"
        buy = (
            "震荡中可留意回踩 MA20 附近的承接；"
            "与大盘同步走强时再考虑加仓，避免单一标的逆势重仓。"
        )
        sell = (
            "跌破 MA20 并两日未收回，可减仓观察；"
            "盈利单可参考 MA5 止盈。"
        )
        notes.append("仍在 MA20 之上，中期结构未坏")
    else:
        rec = "中性偏弱"
        buy = (
            "等待重新站上 MA20 或形成明确底部形态再考虑；"
            "短线仅适合小仓位试错。"
        )
        sell = (
            "反弹至 MA5 受阻可减仓；"
            "若持续运行在 MA20 下，宜控制总仓位。"
        )
        notes.append("收盘在 MA20 之下，注意趋势压力")

    return rec, buy, sell, notes


def analyze_symbol(symbol: str, lookback_days: int, move_threshold: float) -> SymbolAnalysis:
    bundle = fetch_history(symbol, lookback_days)
    if bundle.error:
        return SymbolAnalysis(
            symbol=symbol,
            last_close=None,
            prev_close=None,
            day_change_pct=None,
            ma5=None,
            ma20=None,
            vs_ma5="n/a",
            vs_ma20="n/a",
            note="",
            recommendation="—",
            buy_timing_cn="—",
            sell_timing_cn="—",
            error=bundle.error,
        )

    hist = bundle.history
    last, prev = _last_two_closes(hist)
    day_pct: float | None = None
    if last is not None and prev is not None and prev != 0:
        day_pct = (last / prev - 1.0) * 100.0

    ma5 = _ma(hist, 5)
    ma20 = _ma(hist, 20)

    rec, buy_cn, sell_cn, sig_notes = _signals(last, prev, ma5, ma20, day_pct, move_threshold)
    extra = "; ".join(sig_notes) if sig_notes else "规则扫描无额外标记"

    return SymbolAnalysis(
        symbol=symbol,
        last_close=last,
        prev_close=prev,
        day_change_pct=day_pct,
        ma5=ma5,
        ma20=ma20,
        vs_ma5=_position_vs_ma(last, ma5),
        vs_ma20=_position_vs_ma(last, ma20),
        note=extra,
        recommendation=rec,
        buy_timing_cn=buy_cn,
        sell_timing_cn=sell_cn,
        error=None,
    )


def run_analysis(symbols: List[str], lookback_days: int) -> str:
    thr = big_move_pct()
    lines: List[str] = []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("中国 A 股相关标的 — 日线规则化摘要（数据来源：公开行情，非投资建议）")
    lines.append(f"生成时间（UTC）：{now_utc}")
    lines.append(f"标的列表：{', '.join(symbols)}")
    lines.append("")

    for sym in symbols:
        a = analyze_symbol(sym, lookback_days, thr)
        lines.append(f"=== {a.symbol} ===")
        if a.error:
            lines.append(f"  错误：{a.error}")
            lines.append("")
            continue
        lc = f"{a.last_close:.4f}" if a.last_close is not None else "n/a"
        pc = f"{a.prev_close:.4f}" if a.prev_close is not None else "n/a"
        dpc = f"{a.day_change_pct:+.2f}%" if a.day_change_pct is not None else "n/a"
        m5 = f"{a.ma5:.4f}" if a.ma5 is not None else "n/a"
        m20 = f"{a.ma20:.4f}" if a.ma20 is not None else "n/a"
        lines.append(f"  最新收盘：{lc}  前收：{pc}  涨跌幅：{dpc}")
        lines.append(f"  MA5：{m5}（{a.vs_ma5}）  MA20：{m20}（{a.vs_ma20}）")
        lines.append(f"  规则倾向：{a.recommendation}")
        lines.append(f"  买入时机（规则化表述）：{a.buy_timing_cn}")
        lines.append(f"  卖出时机（规则化表述）：{a.sell_timing_cn}")
        lines.append(f"  备注：{a.note}")
        lines.append("")

    lines.append(
        "免责声明：以上为基于历史收盘价的简单均线与波动规则，不构成任何证券买卖建议；"
        "实盘请结合公告、资金面、板块与自身风险承受能力，并遵守当地法规。"
    )
    return "\n".join(lines)
