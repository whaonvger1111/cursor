#!/usr/bin/env python3
"""
每日 A 股分析入口：适合由 cron 在交易日 09:30 之后触发。

用法:
  python3 -m trading_agent.run_daily_analysis
  python3 -m trading_agent.run_daily_analysis --top 10
  python3 -m trading_agent.run_daily_analysis --email   # 发邮件（需环境变量 SMTP）

环境变量（发 QQ 邮件）:
  A_SHARE_SMTP_USER=你的QQ邮箱
  A_SHARE_SMTP_PASSWORD=QQ邮箱授权码（非登录密码）

自选池: 默认读取本包目录下 watchlist.txt（每行一个代码）；有内容则只分析自选，不拉全市场。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from trading_agent.a_share_agent import (
    analyze_symbol_history,
    fetch_a_share_spot,
    fetch_individual_brief_em,
    fetch_stock_name,
    filter_liquid_main_board,
    score_universe,
    session_context_now,
)
from trading_agent.mail import send_text_email
from trading_agent.watchlist import load_watchlist


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


def _default_watchlist_path() -> Path:
    return Path(__file__).resolve().parent / "watchlist.txt"


def build_report(args: argparse.Namespace) -> tuple[str, int]:
    """
    生成完整报告文本；返回 (text, exit_code)。
    exit_code 非 0 表示应通知运维（如邮件发送失败）。
    """
    lines: list[str] = []

    def out(s: str = "") -> None:
        lines.append(s)

    out("=" * 60)
    out("中国 A 股市场 — 每日简报（公开数据 / 规则化模型，不构成投资建议）")
    out(session_context_now())
    out("=" * 60)

    watch_path = Path(args.watchlist).expanduser().resolve()
    wl_codes = load_watchlist(watch_path) if args.use_watchlist else []

    if args.symbols.strip():
        codes = [c.strip().zfill(6) for c in args.symbols.split(",") if c.strip()]
        if not codes:
            out("错误：未解析到有效代码。")
            return "\n".join(lines), 1
        picks = pd.DataFrame({"代码": codes, "名称": [""] * len(codes)})
        out(f"\n模式：命令行指定代码 — {', '.join(codes)}\n")
    elif wl_codes:
        names: list[str] = []
        prices: list[str] = []
        for c in wl_codes:
            brief = fetch_individual_brief_em(c)
            names.append(brief.get("名称", ""))
            prices.append(brief.get("最新价", ""))
        picks = pd.DataFrame({"代码": wl_codes, "名称": names, "最新价": prices})
        out(f"\n模式：自选池文件 — {watch_path}")
        out(f"共 {len(wl_codes)} 只，不拉取全市场行情。")
        out(f"{'代码':<8}{'名称':<10}{'参考价':>12}")
        out("-" * 32)
        for _, row in picks.iterrows():
            out(
                f"{str(row['代码']).zfill(6):<8}"
                f"{str(row['名称'])[:8]:<10}{str(row.get('最新价', '')):>12}"
            )
        out("")
    else:
        out("\n正在拉取全市场行情（可能需要 1–3 分钟）…")
        raw = fetch_a_share_spot()
        uni = filter_liquid_main_board(raw)
        scored = score_universe(uni)
        top_n = min(max(args.top, 1), 30)
        picks = scored.head(top_n)
        out(
            f"\n根据量比、换手、当日涨跌与 60 日动量等综合打分，"
            f"列出前 {len(picks)} 只供跟踪：\n"
        )
        out(f"{'代码':<8}{'名称':<10}{'最新价':>10}{'涨跌幅%':>10}{'量比':>8}{'60日%':>10}")
        out("-" * 52)
        for _, row in picks.iterrows():
            code = str(row["代码"]).zfill(6)
            nm = str(row["名称"])[:8]
            px = row.get("最新价", "")
            pct = row.get("涨跌幅", "")
            lb = row.get("量比", "")
            m60 = row.get("60日涨跌幅", "")
            out(f"{code:<8}{nm:<10}{str(px):>10}{str(pct):>10}{str(lb):>8}{str(m60):>10}")
        out("")

    rows: list[pd.Series] = []
    for _, row in picks.iterrows():
        rows.append(row)

    out("=" * 60)
    out("技术结构简评与买卖时段参考（日线 MA5/MA20 + RSI14）")
    out("=" * 60)

    for row in rows:
        code = str(row["代码"]).zfill(6)
        name = str(row["名称"]).strip()
        if not name:
            name = fetch_stock_name(code)
        out("")
        out(f"【{code} {name}】")
        try:
            an = analyze_symbol_history(code, name=name)
        except Exception as e:
            out(f"  分析失败: {e}")
            continue
        m = an.metrics
        if m:
            out(
                f"  收盘 {m.get('收盘', float('nan')):.2f}  "
                f"MA5 {m.get('MA5', float('nan')):.2f}  "
                f"MA20 {m.get('MA20', float('nan')):.2f}  "
                f"RSI14 {m.get('RSI14', float('nan')):.1f}"
            )
        out(f"  信号: {an.signal}")
        out(f"  买入时间参考: {an.buy_hint}")
        out(f"  卖出时间参考: {an.sell_hint}")

    out("")
    out("-" * 60)
    out(
        "风险提示：本输出由程序根据公开行情自动生成，存在延迟与误差，"
        "绝不构成任何投资建议。投资有风险，决策请自负。"
    )
    out("-" * 60)

    return "\n".join(lines), 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="中国 A 股每日筛选与技术提示（非投资建议）")
    p.add_argument("--top", type=int, default=12, help="全市场模式下推荐数量（默认 12）")
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="逗号分隔股票代码（优先级最高，跳过自选与全市场）",
    )
    p.add_argument(
        "--watchlist",
        type=str,
        default="",
        help="自选池文件路径；默认使用包内 watchlist.txt",
    )
    p.add_argument(
        "--no-watchlist",
        action="store_true",
        help="忽略自选池文件，直接使用全市场筛选",
    )
    p.add_argument(
        "--skip-calendar",
        action="store_true",
        help="不检查是否为交易日（调试用）",
    )
    p.add_argument(
        "--email",
        type=str,
        nargs="?",
        const="36269216@qq.com",
        default=None,
        metavar="ADDR",
        help="发送报告到邮箱；默认 36269216@qq.com；需配置 A_SHARE_SMTP_USER 与 A_SHARE_SMTP_PASSWORD",
    )
    p.add_argument(
        "--no-email",
        action="store_true",
        help="只打印到终端，不发送邮件",
    )
    args = p.parse_args(argv)

    args.use_watchlist = not args.no_watchlist
    if not args.watchlist:
        args.watchlist = str(_default_watchlist_path())

    if not args.skip_calendar and not _is_cn_trading_day():
        msg = "今日非 A 股交易日，跳过分析。"
        print(msg)
        if args.email and not args.no_email:
            try:
                send_text_email(
                    subject="[A股日报] 非交易日，已跳过",
                    body=msg + "\n\n" + session_context_now(),
                    to_addrs=[args.email.strip()],
                )
            except Exception as e:
                print(f"邮件发送失败: {e}", file=sys.stderr)
                return 1
        return 0

    report, code = build_report(args)
    print(report)

    if args.no_email or args.email is None:
        return code

    to_addr = args.email.strip()
    try:
        d = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")
        send_text_email(
            subject=f"[A股日报] {d}",
            body=report,
            to_addrs=[to_addr],
        )
        print(f"\n已发送至 {to_addr}", file=sys.stderr)
    except ValueError as e:
        print(f"\n未发送邮件: {e}", file=sys.stderr)
        print(
            "请设置环境变量: A_SHARE_SMTP_USER（发件 QQ 邮箱）、"
            "A_SHARE_SMTP_PASSWORD（QQ 邮箱授权码）。",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"\n邮件发送失败: {e}", file=sys.stderr)
        return 1

    return code


if __name__ == "__main__":
    sys.exit(main())
