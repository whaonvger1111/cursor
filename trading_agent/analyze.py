from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

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
    score: int
    tier_cn: str
    buy_timing_cn: str
    sell_timing_cn: str
    note: str
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
        return "上方"
    if price < ma:
        return "下方"
    return "持平"


def _score_and_timing(
    last: float | None,
    prev: float | None,
    ma5: float | None,
    ma20: float | None,
    day_pct: float | None,
    move_threshold: float,
) -> tuple[int, str, str, str, List[str]]:
    """简单规则打分与买卖时点说明（教育性，非投资建议）。"""
    notes: List[str] = []
    score = 50

    if day_pct is not None:
        if abs(day_pct) >= move_threshold:
            notes.append(
                f"相对阈值 {move_threshold:.1f}% 波动偏大：{day_pct:+.2f}%"
            )
        if day_pct >= move_threshold:
            score += 5
        if day_pct <= -move_threshold:
            score -= 12

    if last is not None and ma20 is not None:
        if last > ma20:
            score += 15
        else:
            score -= 10

    if last is not None and ma5 is not None:
        if last > ma5:
            score += 12
        else:
            score -= 8

    if ma5 is not None and ma20 is not None and ma5 > ma20:
        score += 10
    elif ma5 is not None and ma20 is not None and ma5 < ma20:
        score -= 8

    score = max(0, min(100, score))

    if score >= 72:
        tier = "优先关注（规则化）"
    elif score >= 55:
        tier = "观察（规则化）"
    else:
        tier = "谨慎（规则化）"

    # 买入/卖出「时点」：用可执行的观察条件描述，非下单指令
    buy_timing = "数据不足，无法给出规则化观察点。"
    sell_timing = "数据不足，无法给出规则化观察点。"

    if last is not None and ma5 is not None and ma20 is not None:
        if last > ma5 and last > ma20:
            buy_timing = (
                "若出现缩量回踩至 MA5 附近且未跌破 MA20，可作为「关注低吸窗口」观察"
                "（需结合量能与大盘，非买入指令）。"
            )
            sell_timing = (
                "若收盘跌破 MA5 且次日反抽不过 MA5、量能萎缩，可作为「考虑减仓窗口」观察。"
            )
        elif last < ma5 and last > ma20:
            buy_timing = (
                "震荡中：若放量重新站上 MA5 并收阳，可作为「突破确认窗口」观察。"
            )
            sell_timing = (
                "若向下跌破 MA20 且反弹无力，可作为「止损/减仓纪律窗口」观察。"
            )
        else:
            buy_timing = (
                "弱势：仅当重新站上 MA5 与 MA20 后再谈参与；否则以观望为主。"
            )
            sell_timing = (
                "持仓者：反抽至 MA5 附近受阻、量能不济时，可作为「减仓观察窗口」。"
            )

    return score, tier, buy_timing, sell_timing, notes


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
            score=0,
            tier_cn="—",
            buy_timing_cn="—",
            sell_timing_cn="—",
            note="",
            error=bundle.error,
        )

    hist = bundle.history
    last, prev = _last_two_closes(hist)
    day_pct: float | None = None
    if last is not None and prev is not None and prev != 0:
        day_pct = (last / prev - 1.0) * 100.0

    ma5 = _ma(hist, 5)
    ma20 = _ma(hist, 20)

    score, tier, buy_t, sell_t, extra_notes = _score_and_timing(
        last, prev, ma5, ma20, day_pct, move_threshold
    )

    base_notes: List[str] = list(extra_notes)
    if last is not None and ma5 is not None and ma20 is not None:
        if last > ma5 and last > ma20:
            base_notes.append("收盘同时站上 MA5 与 MA20（短线偏强）")
        elif last < ma5 and last < ma20:
            base_notes.append("收盘同时落在 MA5 与 MA20 之下（短线偏弱）")

    summary = "; ".join(base_notes) if base_notes else "无显著规则化标记"

    return SymbolAnalysis(
        symbol=symbol,
        last_close=last,
        prev_close=prev,
        day_change_pct=day_pct,
        ma5=ma5,
        ma20=ma20,
        vs_ma5=_position_vs_ma(last, ma5),
        vs_ma20=_position_vs_ma(last, ma20),
        score=score,
        tier_cn=tier,
        buy_timing_cn=buy_t,
        sell_timing_cn=sell_t,
        note=summary,
        error=None,
    )


def run_analysis(symbols: List[str], lookback_days: int) -> str:
    thr = big_move_pct()
    lines: List[str] = []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("中国 A 股 — 每日规则化分析（基于公开日线）")
    lines.append(f"生成时间（UTC）：{now_utc}")
    lines.append(
        "说明：A 股连续竞价 09:30 起；本脚本使用已收盘日线，适合盘前/盘后复盘，"
        "不等同于实时逐笔信号。"
    )
    lines.append(f"标的列表：{', '.join(symbols)}")
    lines.append("")

    results: List[SymbolAnalysis] = []
    for sym in symbols:
        results.append(analyze_symbol(sym, lookback_days, thr))

    for a in results:
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
        lines.append(f"  最新收盘：{lc}  前收：{pc}  日涨跌幅：{dpc}")
        lines.append(
            f"  MA5：{m5}（收盘在均线{a.vs_ma5}）  "
            f"MA20：{m20}（收盘在均线{a.vs_ma20}）"
        )
        lines.append(f"  规则化评分：{a.score}/100 — {a.tier_cn}")
        lines.append(f"  摘要：{a.note}")
        lines.append(f"  买入相关观察窗口：{a.buy_timing_cn}")
        lines.append(f"  卖出/减仓相关观察窗口：{a.sell_timing_cn}")
        lines.append("")

    ok = [a for a in results if not a.error]
    if ok:
        ranked = sorted(ok, key=lambda x: x.score, reverse=True)
        lines.append("=== 规则化排序（仅供复盘，非投资建议）===")
        for i, a in enumerate(ranked[: min(5, len(ranked))], start=1):
            lines.append(f"  {i}. {a.symbol}  评分 {a.score} — {a.tier_cn}")
        lines.append("")

    lines.append(
        "免责声明：以上为基于公开行情与简单技术指标的规则化整理，不构成任何"
        "证券投资建议或买卖时点承诺；入市有风险，决策请自负。"
    )
    return "\n".join(lines)
