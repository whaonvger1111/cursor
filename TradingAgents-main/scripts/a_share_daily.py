#!/usr/bin/env python3
"""
每日 A 股分析（基于 TradingAgents 多智能体流程）。

用法:
  python3 scripts/a_share_daily.py
  python3 scripts/a_share_daily.py --tickers 600519.SS 000001.SZ --date 2026-04-06
  python3 scripts/a_share_daily.py --wait-until-open   # 等到北京时间 9:30 再跑（交易日）

环境变量（与 TradingAgents 一致）:
  OPENAI_API_KEY / GOOGLE_API_KEY / ANTHROPIC_API_KEY 等
  A_SHARE_TICKERS  逗号分隔，默认脚本内常量

说明:
  - yfinance 对 A 股使用后缀: 上海 .SS，深圳 .SZ
  - 本脚本为研究辅助，不构成投资建议
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# 确保可从仓库根目录导入
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 默认关注标的（可改环境变量 A_SHARE_TICKERS）
DEFAULT_A_SHARE_TICKERS = [
    "600519.SS",  # 贵州茅台
    "000858.SZ",  # 五粮液
    "601318.SS",  # 中国平安
]


def _parse_tickers(raw: str | None) -> List[str]:
    if raw and raw.strip():
        return [t.strip() for t in raw.split(",") if t.strip()]
    return list(DEFAULT_A_SHARE_TICKERS)


def _is_likely_cn_trading_day(d: date) -> bool:
    """若已安装 exchange_calendars，则用上交所日历；否则仅排除周末。"""
    if d.weekday() >= 5:
        return False
    try:
        import exchange_calendars as ec  # type: ignore
        import pandas as pd

        cal = ec.get_calendar("XSHG")
        return bool(cal.is_open_on(pd.Timestamp(d)))
    except Exception:
        return True


def _next_open_930_shanghai(now: datetime) -> datetime:
    """下一个北京时间交易日 9:30（严格晚于 now）。"""
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("Asia/Shanghai")
    except ImportError:
        import pytz

        tz = pytz.timezone("Asia/Shanghai")

    local = now.astimezone(tz)
    for day_offset in range(14):
        d = (local + timedelta(days=day_offset)).date()
        if not _is_likely_cn_trading_day(d):
            continue
        t = datetime(d.year, d.month, d.day, 9, 30, tzinfo=tz)
        if t > local:
            return t
    raise RuntimeError("无法计算下一个 A 股开盘 9:30 时间")


def _wait_until_open() -> None:
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("Asia/Shanghai")
    except ImportError:
        import pytz

        tz = pytz.timezone("Asia/Shanghai")

    while True:
        now = datetime.now(tz)
        target = _next_open_930_shanghai(now)
        if now >= target:
            return
        sleep_s = min(60.0, max(1.0, (target - now).total_seconds()))
        time.sleep(sleep_s)


def _build_config(results_subdir: str) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["project_dir"] = str(_REPO_ROOT)
    cfg["results_dir"] = str(_REPO_ROOT / "results" / results_subdir)
    cfg["output_language"] = "Simplified Chinese"
    cfg["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    os.makedirs(cfg["results_dir"], exist_ok=True)
    return cfg


def run_analysis(
    tickers: List[str],
    trade_date: str,
    *,
    debug: bool,
) -> List[Tuple[str, str, str, dict]]:
    """返回 [(ticker, trade_date, decision_rating, full_state_snippet), ...]"""
    cfg = _build_config(f"a_share_daily_{trade_date}")
    ta = TradingAgentsGraph(debug=debug, config=cfg)
    out: List[Tuple[str, str, str, dict]] = []

    for sym in tickers:
        final_state, rating = ta.propagate(sym, trade_date)
        snippet = {
            "company_of_interest": final_state.get("company_of_interest"),
            "trade_date": final_state.get("trade_date"),
            "extracted_rating": rating,
            "final_trade_decision": (final_state.get("final_trade_decision") or "")[:8000],
        }
        out.append((sym, trade_date, str(rating).strip(), snippet))
    return out


def main() -> int:
    load_dotenv(_REPO_ROOT / ".env")

    p = argparse.ArgumentParser(description="A 股每日 TradingAgents 分析")
    p.add_argument(
        "--tickers",
        type=str,
        default=os.getenv("A_SHARE_TICKERS"),
        help="逗号分隔，如 600519.SS,000001.SZ；默认见脚本或环境变量",
    )
    p.add_argument(
        "--date",
        type=str,
        default=None,
        help="分析日 YYYY-MM-DD，默认今天（上海时区）",
    )
    p.add_argument(
        "--wait-until-open",
        action="store_true",
        help="阻塞到北京时间交易日 9:30 再开始（适合 cron 早触发）",
    )
    p.add_argument(
        "--skip-non-trading-day",
        action="store_true",
        help="若非交易日则直接退出 0（需 exchange_calendars 才能识别节假日，否则仅周末）",
    )
    p.add_argument("--debug", action="store_true", help="打印智能体中间输出")
    args = p.parse_args()

    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("Asia/Shanghai")
    except ImportError:
        import pytz

        tz = pytz.timezone("Asia/Shanghai")

    if args.wait_until_open:
        _wait_until_open()

    tickers = _parse_tickers(args.tickers)
    if args.date:
        trade_date = args.date
        d = date.fromisoformat(trade_date)
    else:
        d = datetime.now(tz).date()
        trade_date = d.isoformat()

    if args.skip_non_trading_day and not _is_likely_cn_trading_day(d):
        print(f"跳过非交易日: {trade_date}")
        return 0

    rows = run_analysis(tickers, trade_date, debug=args.debug)

    summary_path = _REPO_ROOT / "results" / f"a_share_daily_{trade_date}"
    summary_path.mkdir(parents=True, exist_ok=True)
    report_file = summary_path / "summary.json"

    payload = {
        "trade_date": trade_date,
        "tickers": tickers,
        "results": [
            {"ticker": t, "rating": r, "snippet": s} for t, td, r, s in rows
        ],
    }
    report_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\n已写入: {report_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
