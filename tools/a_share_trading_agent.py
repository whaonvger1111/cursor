#!/usr/bin/env python3
"""
A 股日度辅助分析（基于公开行情与简单规则，非投资建议）。

适用场景：交易日开盘后（建议 9:30 之后）运行，结合热度榜与个股快照做排序与买卖时段提示。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

TZ_SH = ZoneInfo("Asia/Shanghai")


def _parse_xq_kv(df: Any) -> dict[str, Any]:
    """将 akshare stock_individual_spot_xq 返回的 item/value 表转为字典。"""
    out: dict[str, Any] = {}
    for _, row in df.iterrows():
        k = str(row["item"]).strip()
        v = row["value"]
        out[k] = v
    return out


def normalize_xq_symbol(code: str) -> str:
    """
    将东方财富/热度榜代码转为雪球接口常用前缀：SH600519 / SZ300058。
    """
    c = str(code).strip().upper()
    if c.startswith(("SH", "SZ", "BJ")):
        return c
    if c.startswith("6"):
        return "SH" + c
    if c.startswith(("0", "3")):
        return "SZ" + c
    if c.startswith("8", "4"):
        return "BJ" + c
    # 已是纯数字时按常见规则
    if c.isdigit():
        if c.startswith("6"):
            return "SH" + c
        return "SZ" + c
    return c


def fetch_hot_list(top_n: int) -> list[dict[str, Any]]:
    import akshare as ak

    df = ak.stock_hot_rank_em()
    rows: list[dict[str, Any]] = []
    for _, r in df.head(top_n).iterrows():
        raw = str(r.get("代码", "")).strip()
        name = str(r.get("股票名称", r.get("名称", ""))).strip()
        rows.append({"raw_code": raw, "name": name, "rank": int(r.get("当前排名", 0) or 0)})
    return rows


def fetch_spot_xq(symbol: str) -> dict[str, Any]:
    import akshare as ak

    df = ak.stock_individual_spot_xq(symbol=symbol)
    return _parse_xq_kv(df)


def _to_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        if isinstance(x, str) and not x.strip():
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


@dataclass
class StockView:
    symbol: str
    name: str
    price: float | None
    pct_chg: float | None
    turnover_rate: float | None
    amount: float | None
    pe_ttm: float | None
    quote_time: str | None
    score: float
    note: str


def _score(
    pct: float | None,
    turnover: float | None,
    amount: float | None,
) -> tuple[float, str]:
    """
    简单启发式分数：适度上涨 + 有成交活跃度；惩罚接近涨停的追涨。
    """
    notes: list[str] = []
    s = 0.0
    if pct is None:
        notes.append("涨幅缺失")
        return 0.0, "; ".join(notes)

    # 涨幅：偏好 1%～8%，过高视为追高风险
    if pct < -2:
        notes.append("当日偏弱")
    if -2 <= pct < 1:
        s += pct * 0.8
    elif 1 <= pct <= 8:
        s += 2.0 + (pct - 1) * 0.35
    elif 8 < pct <= 10.5:
        s += 4.0 - (pct - 8) * 1.2
        notes.append("接近涨停/波动大")
    else:
        s += 1.0
        notes.append("极端涨跌幅")

    if turnover is not None:
        s += min(turnover, 15.0) * 0.15
    if amount is not None and amount > 0:
        s += min(3.0, (amount / 1e9) ** 0.5)

    return s, "; ".join(notes) if notes else "规则打分"


def build_views(entries: list[dict[str, Any]]) -> list[StockView]:
    views: list[StockView] = []
    for e in entries:
        raw = e["raw_code"]
        sym = normalize_xq_symbol(raw)
        name = e.get("name") or ""
        try:
            spot = fetch_spot_xq(sym)
        except Exception as ex:  # noqa: BLE001 — 网络/API 不稳定
            views.append(
                StockView(
                    symbol=sym,
                    name=name,
                    price=None,
                    pct_chg=None,
                    turnover_rate=None,
                    amount=None,
                    pe_ttm=None,
                    quote_time=None,
                    score=-1e9,
                    note=f"行情获取失败: {ex}",
                )
            )
            continue

        price = _to_float(spot.get("现价"))
        pct = _to_float(spot.get("涨幅"))
        turnover = _to_float(spot.get("周转率"))
        amount = _to_float(spot.get("成交额"))
        pe = _to_float(spot.get("市盈率(TTM)"))
        qt = spot.get("时间")
        qt_s = str(qt) if qt is not None else None

        sc, note = _score(pct, turnover, amount)
        views.append(
            StockView(
                symbol=sym,
                name=str(spot.get("名称") or name),
                price=price,
                pct_chg=pct,
                turnover_rate=turnover,
                amount=amount,
                pe_ttm=pe,
                quote_time=qt_s,
                score=sc,
                note=note,
            )
        )
    return views


def print_report(views: list[StockView], top_k: int, as_json: bool) -> None:
    now = datetime.now(TZ_SH)
    header = {
        "generated_at_cst": now.isoformat(),
        "disclaimer": (
            "本输出仅为基于公开行情与启发式规则的自动化整理，不构成投资建议。"
            "证券市场有风险，决策需自行承担。"
        ),
        "session_cst": "沪深A股连续竞价通常为 09:30–11:30、13:00–15:00（周一至周五，节假日除外）。",
    }
    ranked = sorted(views, key=lambda v: v.score, reverse=True)
    picks = [v for v in ranked if v.score > -1e8][:top_k]

    timing = {
        "观察与买入参考时段": [
            "开盘后 9:30–9:45：观察竞价后方向与量能，避免盲目追高开缺口。",
            "上午 10:00–11:20：趋势若与大盘/板块一致，可考虑分批；严格设置止损位。",
            "午后 13:00–14:30：延续趋势时可持有观察；若量价背离宜减仓。",
        ],
        "卖出或减仓参考时段": [
            "冲高无量或涨幅过大时：可分笔止盈，不必苛求卖在最高点。",
            "14:50–15:00：若当日目标已达或风险暴露偏高，可择机收尾；次日再评估。",
        ],
        "说明": "具体买卖点需结合你本人的策略、仓位与风险承受能力；本脚本不提供精确时点预测。",
    }

    if as_json:
        payload = {
            **header,
            "timing_hints_cst": timing,
            "candidates": [asdict(v) for v in picks],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("=" * 60)
    print("A 股日度辅助分析（非投资建议）")
    print(f"生成时间（北京时间）: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(header["disclaimer"])
    print("-" * 60)
    print("交易时段提示:", header["session_cst"])
    print()
    for title, lines in timing.items():
        if title == "说明":
            print(f"{title}: {lines}")
            continue
        print(f"【{title}】")
        for line in lines:
            print(f"  - {line}")
        print()
    print("-" * 60)
    print(f"推荐关注（按启发式分数排序，前 {top_k} 名）:")
    for i, v in enumerate(picks, 1):
        print(
            f"{i}. {v.symbol} {v.name} | 现价:{v.price} | 涨幅:{v.pct_chg}% | "
            f"换手:{v.turnover_rate}% | 成交额:{v.amount} | PE(TTM):{v.pe_ttm} | 行情时间:{v.quote_time}"
        )
        print(f"   分数:{v.score:.2f} | 备注:{v.note}")
    print("=" * 60)


def main() -> int:
    p = argparse.ArgumentParser(description="A 股热度 + 快照辅助分析")
    p.add_argument("--hot-top", type=int, default=25, help="东方财富热度榜取前 N 只再拉详情")
    p.add_argument("--top-k", type=int, default=8, help="输出推荐数量")
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="逗号分隔自选，如 SH600519,SZ300750（若填写则跳过热度榜）",
    )
    p.add_argument("--json", action="store_true", help="输出 JSON 便于自动化")
    args = p.parse_args()

    if args.symbols.strip():
        syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
        entries = [{"raw_code": s, "name": "", "rank": 0} for s in syms]
    else:
        entries = fetch_hot_list(args.hot_top)

    views = build_views(entries)
    print_report(views, args.top_k, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
