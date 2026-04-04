#!/usr/bin/env python3
"""
A 股日线批处理：调用 TradingAgents 多智能体图，对股票池逐一分析并写入报告。

用法（需已配置 LLM API 密钥，见 TradingAgents-main/.env.example）：
  cd /workspace && pip install -e ./TradingAgents-main
  pip install -r requirements_a_share.txt   # 交易日历（含长假），强烈推荐
  python a_share_daily_run.py

建议在用户本机 crontab 用北京时间 9:30 触发（示例）：
  30 9 * * 1-5 TZ=Asia/Shanghai cd /workspace && /usr/bin/python3 a_share_daily_run.py >> /workspace/a_share_cron.log 2>&1

交易日 trade_date 规则（北京时间）：
- 若已安装 exchange_calendars：按上交所 XSHG 日历识别周末与内地休市；正常交易日 15:00 收盘前
  使用「上一完整交易日」的日线（与未收盘的当日 K 线一致）；15:00 及之后使用「当日」。
- 未安装日历时回退为仅跳过周末（长假仍可能偏差），报告与 JSON 中会标注。

默认启用分析师：market, news, fundamentals（不含 social，减少对 A 股噪声）。
环境变量 A_SHARE_ANALYSTS 可覆盖，例如：market,social,news,fundamentals

非投资建议；数据依赖 yfinance；A 股代码需带 .SS / .SZ / .BJ。
"""

from __future__ import annotations

import json
import os
import sys
import warnings
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

# A 股现货常规收盘时间（北京时间）；与 exchange_calendars 分钟级一致即可用于日线口径
_A_SHARE_REGULAR_CLOSE = datetime(2000, 1, 1, 15, 0, tzinfo=CN_TZ).time()


def _try_get_xshg_calendar():
    try:
        import exchange_calendars as xc

        return xc.get_calendar("XSHG")
    except ImportError:
        return None


def _resolve_trade_date(now_cn: datetime) -> tuple[date, str]:
    """返回 (trade_date, 说明备注)。trade_date 为传给 TradingAgents 的 YYYY-MM-DD。"""
    ref = now_cn.date()
    cal = _try_get_xshg_calendar()

    if cal is None:
        warnings.warn(
            "未安装 exchange_calendars，trade_date 仅跳过周末，长假可能不准确。"
            "请执行: pip install -r requirements_a_share.txt",
            stacklevel=2,
        )
        d = ref - timedelta(days=1)
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        return d, "fallback_weekend_only"

    import pandas as pd

    ref_ts = pd.Timestamp(ref)
    if not cal.is_session(ref_ts):
        sess = cal.date_to_session(ref_ts, direction="previous")
        return sess.date(), "calendar_non_session_use_previous_completed"

    # ref 是交易日：收盘前用上一交易日（当日 K 线未走完）；收盘后用当日
    close_today = datetime.combine(ref, _A_SHARE_REGULAR_CLOSE, tzinfo=CN_TZ)
    if now_cn < close_today:
        prev = cal.previous_session(ref_ts)
        return prev.date(), "calendar_before_close_use_previous_session"
    return ref, "calendar_after_close_use_today_session"


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


def _parse_analyst_list() -> list[str]:
    raw = os.getenv(
        "A_SHARE_ANALYSTS",
        "market,news,fundamentals",
    )
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    allowed = {"market", "social", "news", "fundamentals"}
    for p in parts:
        if p not in allowed:
            raise ValueError(
                f"A_SHARE_ANALYSTS 含未知分析师: {p}，允许: {sorted(allowed)}"
            )
    if not parts:
        raise ValueError("A_SHARE_ANALYSTS 不能为空")
    return parts


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
    trade_date, trade_date_reason = _resolve_trade_date(now_cn)
    tickers = _load_universe(UNIVERSE_FILE)
    analysts = _parse_analyst_list()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"a_share_report_{trade_date.isoformat()}.md"

    cfg = _build_config()
    graph = TradingAgentsGraph(
        selected_analysts=analysts,
        debug=False,
        config=cfg,
    )

    reason_zh = {
        "fallback_weekend_only": "未装交易日历：仅跳过周末（长假可能不准）",
        "calendar_non_session_use_previous_completed": "非交易日：取上一完整交易日",
        "calendar_before_close_use_previous_session": "交易日下午收盘前：取上一完整交易日（当日 K 未收盘）",
        "calendar_after_close_use_today_session": "交易日下午收盘后：取当日交易日",
    }.get(trade_date_reason, trade_date_reason)

    header: list[str] = [
        "# A 股多智能体分析（TradingAgents）",
        "",
        f"- 运行时间（北京时间）: {now_cn.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- 使用的日线交易日 trade_date: **{trade_date}** — {reason_zh}",
        f"- 启用分析师: {', '.join(analysts)}（默认不含 social，可用 A_SHARE_ANALYSTS 修改）",
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
                "trade_date_reason": trade_date_reason,
                "analysts": analysts,
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
