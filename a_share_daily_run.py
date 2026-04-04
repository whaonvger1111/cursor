#!/usr/bin/env python3
"""
A 股日线批处理：调用 TradingAgents 多智能体图，对股票池逐一分析并写入报告。

用法（需已配置 LLM API 密钥，见 TradingAgents-main/.env.example）：
  cd /workspace && pip install -e ./TradingAgents-main
  python a_share_daily_run.py

建议在用户本机 crontab 用北京时间 9:30 触发（示例）：
  30 9 * * 1-5 TZ=Asia/Shanghai cd /workspace && /usr/bin/python3 a_share_daily_run.py >> /workspace/a_share_cron.log 2>&1

说明：
- 分析日 trade_date 取「上一交易日」的日期，与日线收盘价可得性一致；非投资建议。
- 数据依赖 yfinance；A 股需带交易所后缀 .SS / .SZ / .BJ。
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# 以源码树运行：将 TradingAgents 包加入路径
_REPO_ROOT = Path(__file__).resolve().parent
_TA_ROOT = _REPO_ROOT / "TradingAgents-main"
if str(_TA_ROOT) not in sys.path:
    sys.path.insert(0, str(_TA_ROOT))

from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


CN_TZ = ZoneInfo("Asia/Shanghai")
UNIVERSE_FILE = _REPO_ROOT / "a_share_universe.txt"
REPORT_DIR = _REPO_ROOT / "a_share_reports"


def _load_universe(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"股票池文件不存在: {path}")
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s.upper())
    if not out:
        raise ValueError(f"股票池为空: {path}")
    return out


def _previous_trading_day(ref: datetime) -> date:
    """上一自然日向前回退，跳过周末（不处理内地长假，与 yfinance 日线一致即可）。"""
    d = ref.date() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _build_config() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["project_dir"] = str(_TA_ROOT / "tradingagents")
    cfg["results_dir"] = os.getenv(
        "TRADINGAGENTS_RESULTS_DIR", str(_REPO_ROOT / "tradingagents_results")
    )
    cfg["data_cache_dir"] = os.path.join(cfg["project_dir"], "dataflows", "data_cache")
    cfg["output_language"] = "Chinese"
    cfg["max_debate_rounds"] = int(os.getenv("A_SHARE_DEBATE_ROUNDS", "1"))
    cfg["max_risk_discuss_rounds"] = int(os.getenv("A_SHARE_RISK_ROUNDS", "1"))
    cfg["deep_think_llm"] = os.getenv("A_SHARE_DEEP_LLM", cfg.get("deep_think_llm", "gpt-5.4"))
    cfg["quick_think_llm"] = os.getenv("A_SHARE_QUICK_LLM", cfg.get("quick_think_llm", "gpt-5.4-mini"))
    cfg["llm_provider"] = os.getenv("LLM_PROVIDER", cfg.get("llm_provider", "openai"))
    if os.getenv("OPENAI_BASE_URL"):
        cfg["backend_url"] = os.environ["OPENAI_BASE_URL"]
    cfg["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    return cfg


def main() -> None:
    load_dotenv(_TA_ROOT / ".env")
    load_dotenv(_REPO_ROOT / ".env")

    now_cn = datetime.now(CN_TZ)
    trade_date = _previous_trading_day(now_cn)
    tickers = _load_universe(UNIVERSE_FILE)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"a_share_report_{trade_date.isoformat()}.md"

    cfg = _build_config()
    graph = TradingAgentsGraph(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config=cfg,
    )

    header: list[str] = [
        "# A 股多智能体分析（TradingAgents）",
        "",
        f"- 运行时间（北京时间）: {now_cn.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- 使用的日线交易日 trade_date: **{trade_date}**（上一完整交易日，日线口径）",
        f"- 标的数量: {len(tickers)}",
        "",
        "> 框架仅供研究；输出不构成投资建议。",
        "",
    ]

    sections: list[str] = []
    summary_rows: list[dict] = []

    for symbol in tickers:
        block = [f"## {symbol}", ""]
        try:
            state, rating = graph.propagate(symbol, trade_date.isoformat())
            block.append(f"**信号摘要**: `{rating}`")
            block.append("")
            final = state.get("final_trade_decision") or ""
            block.append("### 决策原文")
            block.append("")
            block.append(final.strip() or "（空）")
            block.append("")
            summary_rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date.isoformat(),
                    "rating": str(rating).strip(),
                }
            )
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            block.append(f"**运行失败**: {err}")
            block.append("")
            summary_rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date.isoformat(),
                    "error": err,
                }
            )
        sections.extend(block)

    table_lines = [
        "## 汇总",
        "",
        "| 代码 | 交易日 | 信号 / 状态 |",
        "| --- | --- | --- |",
    ]
    for r in summary_rows:
        cell = r.get("rating") or r.get("error") or ""
        table_lines.append(
            f"| {r.get('symbol', '')} | {r.get('trade_date', '')} | {cell} |"
        )
    table_lines.append("")

    report_path.write_text(
        "\n".join(header + table_lines + sections), encoding="utf-8"
    )
    (_REPO_ROOT / "a_share_last_run.json").write_text(
        json.dumps(
            {
                "run_at_cn": now_cn.isoformat(),
                "trade_date": trade_date.isoformat(),
                "report": str(report_path),
                "rows": summary_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"报告已写入: {report_path}")


if __name__ == "__main__":
    main()
