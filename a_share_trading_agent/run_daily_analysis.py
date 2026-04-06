#!/usr/bin/env python3
"""
每日 A 股简报（基于公开行情 + 简单技术指标）。

用法:
  python3 -m a_share_trading_agent.run_daily_analysis
  python3 -m a_share_trading_agent.run_daily_analysis --top 200 --pick 15

说明:
  - 不构成投资建议；实盘请自担风险并遵守法规。
  - 「买入/卖出时间点」在 A 股制度下以交易时段说明 + 日线信号为主，
    无法保证精确到分钟的最优时点。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from a_share_trading_agent.data_sources import (
    baostock_session,
    eastmoney_code_to_baostock,
    fetch_eastmoney_spot_page,
    query_baostock_daily,
)
from a_share_trading_agent.signals import cn_trading_session_hints, summarize_signal


def _is_st_name(name: str) -> bool:
    n = name.upper()
    return "ST" in n or "*ST" in name


def main() -> None:
    parser = argparse.ArgumentParser(description="A 股日线级辅助分析")
    parser.add_argument(
        "--top",
        type=int,
        default=150,
        help="从实时行情中按成交额取前 N 只再筛选（默认 150）",
    )
    parser.add_argument(
        "--pick",
        type=int,
        default=12,
        help="最终输出推荐观察数量（默认 12）",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=2,
        help="拉取实时列表页数（每页 100，默认 2 页）",
    )
    args = parser.parse_args()

    end = datetime.now().date()
    start = end - timedelta(days=400)

    rows: list = []
    for p in range(1, args.pages + 1):
        rows.extend(fetch_eastmoney_spot_page(page=p, page_size=100, sort_field="f6"))

    # 按成交额排序并去重
    seen: set[str] = set()
    uniq: list = []
    for r in sorted(rows, key=lambda x: (x.amt or 0), reverse=True):
        if r.code in seen:
            continue
        seen.add(r.code)
        uniq.append(r)
        if len(uniq) >= args.top:
            break

    candidates = [r for r in uniq if not _is_st_name(r.name)]

    results: list[tuple] = []
    with baostock_session():
        for spot in candidates:
            bs_code = eastmoney_code_to_baostock(spot.code, spot.market)
            try:
                hist = query_baostock_daily(
                    bs_code,
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                )
            except Exception:
                continue
            sig = summarize_signal(hist)
            if sig.action == "关注买入":
                rank_key = (2, sig.score, spot.amt or 0)
            elif sig.action == "持有观望":
                rank_key = (1, sig.score, spot.amt or 0)
            else:
                rank_key = (0, sig.score, spot.amt or 0)
            results.append((rank_key, spot, sig))

    results.sort(key=lambda x: x[0], reverse=True)
    picked = results[: args.pick]

    print("=" * 60)
    print(f"A 股辅助观察简报  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    print("【重要】本输出为规则化技术分析演示，非投资建议；入市有风险。")
    print()
    print("【交易时段】" + cn_trading_session_hints())
    print()
    if not picked:
        print("未能生成候选（可能网络或数据源异常）。请稍后重试。")
        return

    print(f"【候选说明】从成交额靠前的股票中，用日线 RSI(14)+MA5/MA20 做简单打分。")
    print()
    for i, (_, spot, sig) in enumerate(picked, 1):
        pct = spot.pct_chg
        pct_s = f"{pct:+.2f}%" if pct is not None else "-"
        print(f"{i}. {spot.name} ({spot.code})  现价:{spot.last}  涨跌:{pct_s}")
        print(
            f"   信号: {sig.action}  |  score={sig.score:.2f}  "
            f"RSI14={sig.rsi14:.1f}  MA5={sig.ma5:.2f}  MA20={sig.ma20:.2f}"
        )
        print(f"   {sig.note}")
        print(
            "   时间参考: 日线级信号以收盘或次日集合竞价/开盘为观察窗口；"
            "短线若需减仓，可在盘中冲高或跌破 MA5 时分批评估。"
        )
        print()

    print("-" * 60)
    print(
        "【关于「每天九点半」】可在交易日本机 crontab 设置 "
        "`30 9 * * 1-5 cd /path && python3 -m a_share_trading_agent.run_daily_analysis` "
        "（时区需为 Asia/Shanghai）。"
    )


if __name__ == "__main__":
    main()
