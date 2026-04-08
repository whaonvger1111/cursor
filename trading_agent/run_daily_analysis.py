#!/usr/bin/env python3
"""
每日 A 股分析入口：适合由 cron 在交易日 09:30 之后触发。

用法:
  python3 -m trading_agent.run_daily_analysis
  python3 -m trading_agent.run_daily_analysis --top 10

环境: 需已安装 akshare、pandas、numpy。
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from trading_agent.a_share_agent import (
    analyze_symbol_history,
    fetch_a_share_spot,
    filter_liquid_main_board,
    score_universe,
    session_context_now,
)


def _is_cn_trading_day() -> bool:
    try:
        import akshare as ak
        from datetime import datetime
        from zoneinfo import ZoneInfo

        today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        cal = ak.tool_trade_date_hist_sina()
        if cal is None or cal.empty:
            return True
        dates = set(cal["trade_date"].astype(str).tolist())
        return today in dates
    except Exception:
        return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="中国 A 股每日筛选与技术提示（非投资建议）")
    p.add_argument("--top", type=int, default=12, help="推荐关注股票数量（默认 12）")
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="逗号分隔股票代码，仅分析这些（跳过全市场拉取，用于测试）",
    )
    p.add_argument(
        "--skip-calendar",
        action="store_true",
        help="不检查是否为交易日（调试用）",
    )
    args = p.parse_args(argv)

    if not args.skip_calendar and not _is_cn_trading_day():
        print("今日非 A 股交易日，跳过分析。")
        return 0

    print("=" * 60)
    print("中国 A 股市场 — 每日简报（公开数据 / 规则化模型，不构成投资建议）")
    print(session_context_now())
    print("=" * 60)

    if args.symbols.strip():
        codes = [c.strip().zfill(6) for c in args.symbols.split(",") if c.strip()]
        if not codes:
            print("未解析到有效代码。")
            return 1
        picks = pd.DataFrame({"代码": codes, "名称": [""] * len(codes)})
        print(f"\n仅分析指定代码: {', '.join(codes)}（不拉取全市场行情）\n")
    else:
        print("\n正在拉取全市场行情（可能需要 1–3 分钟）…")
        raw = fetch_a_share_spot()
        uni = filter_liquid_main_board(raw)
        scored = score_universe(uni)
        top_n = min(max(args.top, 1), 30)
        picks = scored.head(top_n)

    rows: list[pd.Series] = []
    if args.symbols.strip():
        for _, row in picks.iterrows():
            rows.append(row)
    else:
        print(
            f"\n根据量比、换手、当日涨跌与 60 日动量等综合打分，"
            f"列出前 {len(picks)} 只供跟踪：\n"
        )
        print(f"{'代码':<8}{'名称':<10}{'最新价':>10}{'涨跌幅%':>10}{'量比':>8}{'60日%':>10}")
        print("-" * 52)
        for _, row in picks.iterrows():
            code = str(row["代码"]).zfill(6)
            nm = str(row["名称"])[:8]
            px = row.get("最新价", "")
            pct = row.get("涨跌幅", "")
            lb = row.get("量比", "")
            m60 = row.get("60日涨跌幅", "")
            print(f"{code:<8}{nm:<10}{str(px):>10}{str(pct):>10}{str(lb):>8}{str(m60):>10}")
            rows.append(row)

    print("\n" + "=" * 60)
    print("技术结构简评与买卖时段参考（日线 MA5/MA20 + RSI14）")
    print("=" * 60)

    for row in rows:
        code = str(row["代码"]).zfill(6)
        name = str(row["名称"])
        print(f"\n【{code} {name}】")
        try:
            an = analyze_symbol_history(code, name=name)
        except Exception as e:
            print(f"  分析失败: {e}")
            continue
        m = an.metrics
        if m:
            print(
                f"  收盘 {m.get('收盘', '—'):.2f}  "
                f"MA5 {m.get('MA5', float('nan')):.2f}  "
                f"MA20 {m.get('MA20', float('nan')):.2f}  "
                f"RSI14 {m.get('RSI14', float('nan')):.1f}"
            )
        print(f"  信号: {an.signal}")
        print(f"  买入时间参考: {an.buy_hint}")
        print(f"  卖出时间参考: {an.sell_hint}")

    print("\n" + "-" * 60)
    print(
        "风险提示：本输出由程序根据公开行情自动生成，存在延迟与误差，"
        "绝不构成任何投资建议。投资有风险，决策请自负。"
    )
    print("-" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
