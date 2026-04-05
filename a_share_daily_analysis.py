#!/usr/bin/env python3
"""
每日中国 A 股（yfinance 后缀 .SS / .SZ）批量分析，基于 TauricResearch/TradingAgents。

用法:
  cd /workspace
  export OPENAI_API_KEY=...   # 或其他已配置的 LLM 提供商密钥，见 TradingAgents-main/.env.example
  python3 a_share_daily_analysis.py

可选环境变量:
  TRADINGAGENTS_LLM_PROVIDER   默认 openai；可选 google, anthropic, ollama 等
  TRADINGAGENTS_DEEP_MODEL     默认 gpt-5.4-mini（可按你的账户可用模型修改）
  TRADINGAGENTS_QUICK_MODEL    默认同上
  TRADINGAGENTS_BACKEND_URL    兼容接口的 base URL（如自建网关）
  A_SHARE_TICKERS              逗号分隔代码，如 600519.SS,000858.SZ（覆盖默认列表）
  ANALYSIS_DATE                覆盖分析日 YYYY-MM-DD（默认可交易日记为上一交易日近似）

北京时间每个交易日 09:30 后运行（数据与框架均非实时行情，属研究用途）:
  crontab -e 并设置 CRON_TZ=Asia/Shanghai，例如:
  30 9 * * 1-5 cd /workspace && /usr/bin/python3 a_share_daily_analysis.py >> /tmp/a_share_ta.log 2>&1

免责声明: 输出为研究演示，不构成投资建议。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# 确保可导入工作区内的 TradingAgents（未 pip install 时）
_WORKSPACE = Path(__file__).resolve().parent
_TA_ROOT = _WORKSPACE / "TradingAgents-main"
if _TA_ROOT.is_dir() and str(_TA_ROOT) not in sys.path:
    sys.path.insert(0, str(_TA_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_TA_ROOT / ".env")
load_dotenv(_WORKSPACE / ".env")

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402

# 默认关注标的（沪市 .SS，深市 .SZ）；可通过环境变量 A_SHARE_TICKERS 覆盖
DEFAULT_A_SHARE: list[tuple[str, str]] = [
    ("600519.SS", "贵州茅台"),
    ("000858.SZ", "五粮液"),
    ("601318.SS", "中国平安"),
    ("600036.SS", "招商银行"),
    ("300750.SZ", "宁德时代"),
]


def _parse_tickers_env() -> list[tuple[str, str]] | None:
    raw = os.environ.get("A_SHARE_TICKERS", "").strip()
    if not raw:
        return None
    out: list[tuple[str, str]] = []
    for part in raw.split(","):
        p = part.strip().upper()
        if not p:
            continue
        if "." not in p:
            raise SystemExit(
                f"标的需带交易所后缀: {p!r}（沪市 .SS，深市 .SZ）"
            )
        out.append((p, p))
    return out


def _load_tickers_json(path: Path) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        pairs: list[tuple[str, str]] = []
        for item in data:
            if isinstance(item, str):
                pairs.append((item.strip().upper(), item.strip().upper()))
            elif isinstance(item, dict) and "symbol" in item:
                sym = str(item["symbol"]).strip().upper()
                name = str(item.get("name", sym))
                pairs.append((sym, name))
        return pairs
    raise SystemExit(f"不支持的 JSON 格式: {path}")


def _default_trade_date() -> str:
    """返回用于 propagate 的日期字符串（尽量避开周末）。"""
    d = date.today()
    # 周一则回退到上周五
    if d.weekday() == 0:
        d = d - timedelta(days=3)
    elif d.weekday() == 6:
        d = d - timedelta(days=2)
    elif d.weekday() == 5:
        d = d - timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def _build_config() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["output_language"] = "Chinese"
    cfg["max_debate_rounds"] = min(int(cfg.get("max_debate_rounds", 1)), 1)
    cfg["max_risk_discuss_rounds"] = min(int(cfg.get("max_risk_discuss_rounds", 1)), 1)
    cfg["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    cfg["llm_provider"] = os.environ.get("TRADINGAGENTS_LLM_PROVIDER", cfg["llm_provider"])
    cfg["deep_think_llm"] = os.environ.get("TRADINGAGENTS_DEEP_MODEL", "gpt-5.4-mini")
    cfg["quick_think_llm"] = os.environ.get("TRADINGAGENTS_QUICK_MODEL", cfg["deep_think_llm"])
    if os.environ.get("TRADINGAGENTS_BACKEND_URL"):
        cfg["backend_url"] = os.environ["TRADINGAGENTS_BACKEND_URL"]
    cfg["results_dir"] = os.environ.get(
        "TRADINGAGENTS_RESULTS_DIR",
        str(_WORKSPACE / "a_share_analysis_results"),
    )
    return cfg


def run() -> int:
    parser = argparse.ArgumentParser(description="A 股 TradingAgents 每日批量分析")
    parser.add_argument(
        "--date",
        dest="trade_date",
        help="分析日 YYYY-MM-DD（默认：当前可交易日近似）",
    )
    parser.add_argument(
        "--tickers-file",
        type=Path,
        help="JSON 标的列表，见脚本内说明",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印配置与标的，不调用 LLM",
    )
    args = parser.parse_args()

    trade_date = args.trade_date or os.environ.get("ANALYSIS_DATE") or _default_trade_date()

    if args.tickers_file:
        tickers = _load_tickers_json(args.tickers_file)
    else:
        env_tickers = _parse_tickers_env()
        tickers = env_tickers if env_tickers else DEFAULT_A_SHARE

    cfg = _build_config()

    print("=== A 股 TradingAgents 批量分析 ===", flush=True)
    print(f"分析日: {trade_date}", flush=True)
    print(f"LLM: {cfg['llm_provider']} / {cfg['deep_think_llm']}", flush=True)
    print(f"结果目录: {cfg['results_dir']}", flush=True)
    print("标的:", flush=True)
    for sym, name in tickers:
        print(f"  {sym}  {name}", flush=True)
    print(flush=True)

    if args.dry_run:
        return 0

    graph = TradingAgentsGraph(debug=False, config=cfg)

    summary: list[dict] = []
    for symbol, display_name in tickers:
        print(f"--- 分析 {symbol} ({display_name}) ---", flush=True)
        try:
            _state, decision = graph.propagate(symbol, trade_date)
        except Exception as e:
            print(f"[错误] {symbol}: {e}", flush=True)
            summary.append(
                {
                    "symbol": symbol,
                    "name": display_name,
                    "error": str(e),
                }
            )
            continue
        rec = {
            "symbol": symbol,
            "name": display_name,
            "trade_date": trade_date,
            "signal": decision,
        }
        summary.append(rec)
        print(f"信号摘要: {decision}", flush=True)
        print(flush=True)

    out_path = Path(cfg["results_dir"]) / f"summary_{trade_date}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已写入汇总: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
