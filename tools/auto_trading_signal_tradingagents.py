#!/usr/bin/env python3
"""
将本脚本放在 TradingAgents 项目根目录（与 main.py、tradingagents/ 同级），或在本机任意位置运行并设置环境变量：
  set TRADINGAGENTS_ROOT=C:\\Users\\Administrator\\Desktop\\TradingAgents-main

周期性调用 TradingAgents 多智能体图，输出交易决策提示（框架为研究/模拟用途，不构成投资建议）。
需已安装依赖（pip install -e .）并配置 API 密钥，例如：set OPENAI_API_KEY=...

A 股（沪深）说明：
  默认数据来自 yfinance，代码需用 Yahoo 后缀：沪市 6 开头加 .SS，深市 0/3 开头加 .SZ。
  例：贵州茅台 600519.SS，平安银行 000001.SZ。最终 JSON 里 decision 字段经框架提炼为
  BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL，其中 BUY/SELL 即买入/卖出类提示。
  港股示例：0700.HK。  若某标的 yfinance 无数据，需自行换数据源或改 TradingAgents 数据层。

定时运行（Windows 每个交易日 09:00）：见 tools/windows/README_scheduling.md
  Cursor Automations（云端定时）：见仓库根目录 AUTOMATIONS.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# 解析 TradingAgents 根目录
_env_root = os.environ.get("TRADINGAGENTS_ROOT", "").strip()
if _env_root:
    _TA_ROOT = Path(_env_root).resolve()
else:
    _TA_ROOT = Path(__file__).resolve().parent

if not (_TA_ROOT / "tradingagents").is_dir():
    print(
        "错误: 找不到 tradingagents 包。请将脚本复制到 TradingAgents 项目根目录，或设置环境变量 "
        "TRADINGAGENTS_ROOT 指向该项目路径（例如 Desktop\\\\TradingAgents-main）。",
        file=sys.stderr,
    )
    sys.exit(1)

if str(_TA_ROOT) not in sys.path:
    sys.path.insert(0, str(_TA_ROOT))

from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

load_dotenv(_TA_ROOT / ".env")


def _today_str() -> str:
    """交易日日期：默认本机日历日；设置 TRADING_SIGNAL_TIMEZONE=Asia/Shanghai 时用该时区的「今天」。"""
    tz_name = os.getenv("TRADING_SIGNAL_TIMEZONE", "").strip()
    if tz_name:
        try:
            return datetime.now(ZoneInfo(tz_name)).date().isoformat()
        except (ValueError, OSError):
            pass
    return date.today().isoformat()


def _build_config(args: argparse.Namespace) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["deep_think_llm"] = args.deep_model
    cfg["quick_think_llm"] = args.quick_model
    cfg["max_debate_rounds"] = args.debate_rounds
    cfg["llm_provider"] = args.llm_provider
    if args.output_language:
        cfg["output_language"] = args.output_language
    cfg["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    return cfg


def _run_once(
    ta: TradingAgentsGraph, ticker: str, trade_date: str, out_dir: Path
) -> dict:
    _, decision = ta.propagate(ticker, trade_date)
    record = {
        "ticker": ticker,
        "trade_date": trade_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = trade_date.replace(":", "-")
    path = out_dir / f"signal_{ticker}_{safe}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {ticker} @ {trade_date} -> {decision}")
    print(f"     已保存: {path}")
    return record


def main() -> None:
    p = argparse.ArgumentParser(description="TradingAgents 自动交易提示（定时/单次）")
    p.add_argument(
        "--tickers",
        default=os.getenv("TRADING_SIGNAL_TICKERS", "NVDA"),
        help="逗号分隔代码；A 股用 Yahoo 格式，如 600519.SS,000001.SZ",
    )
    p.add_argument(
        "--trade-date",
        default=None,
        help="分析日期 YYYY-MM-DD，默认今天",
    )
    p.add_argument(
        "--interval-hours",
        type=float,
        default=0.0,
        help="与 --loop 联用：每 N 小时重复；0 表示循环时默认 24 小时",
    )
    p.add_argument("--loop", action="store_true", help="持续循环（需设置间隔）")
    p.add_argument("--once", action="store_true", help="只运行一轮（默认行为）")
    p.add_argument(
        "--output-dir",
        default=os.getenv("TRADING_SIGNAL_OUTPUT_DIR", "./trading_signal_logs"),
        help="JSON 输出目录（相对于当前工作目录）",
    )
    p.add_argument("--debug", action="store_true")
    p.add_argument("--llm-provider", default="openai")
    p.add_argument("--deep-model", default="gpt-5.4-mini")
    p.add_argument("--quick-model", default="gpt-5.4-mini")
    p.add_argument("--debate-rounds", type=int, default=1)
    p.add_argument("--output-language", default="Chinese")
    args = p.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        print("错误: 未指定有效 ticker", file=sys.stderr)
        sys.exit(1)

    trade_date = args.trade_date or _today_str()
    out_dir = Path(args.output_dir).resolve()

    if args.llm_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print(
            "错误: 使用 openai 时需设置环境变量 OPENAI_API_KEY（或在 TradingAgents 根目录的 .env 中配置）。",
            file=sys.stderr,
        )
        sys.exit(1)

    config = _build_config(args)
    ta = TradingAgentsGraph(debug=args.debug, config=config)

    def cycle() -> None:
        for t in tickers:
            _run_once(ta, t, trade_date, out_dir)

    if args.once or not args.loop:
        cycle()
        return

    interval = args.interval_hours if args.interval_hours > 0 else 24.0
    print(f"循环模式: 每 {interval} 小时执行一次，Ctrl+C 结束。")
    while True:
        cycle()
        time.sleep(interval * 3600.0)


if __name__ == "__main__":
    main()
