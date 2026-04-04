#!/usr/bin/env python3
"""
全 A 股批处理（Ollama / 可改 LLM）：对超大股票池逐只调用 TradingAgents。

现实约束：
- 5000+ 标的 × 多智能体 = 极长时间；默认仅启用 **market** 分析师以控制成本。
- 必须显式确认并建议设置上限；支持断点续跑。

用法示例：
  export LLM_PROVIDER=ollama
  export OLLAMA_MODEL=llama3.2:3b
  export A_SHARE_FULL_CONFIRM=1
  export A_SHARE_FULL_MAX=100          # 本批最多分析多少只（0=不限制，需配合确认）
  export A_SHARE_FULL_OFFSET=0         # 跳过前 N 只（与 MAX 配合做分片）
  python3 a_share_full_market_run.py

  # 刷新代码列表缓存（AkShare 实时行情接口，较慢）
  export A_SHARE_FULL_REFRESH_CODES=1
  python3 a_share_full_market_run.py

  # 仅跑 a_share_universe.txt（联调 / 小样本）
  export A_SHARE_FULL_USE_UNIVERSE_FILE=1
  export A_SHARE_FULL_MAX=5
  python3 a_share_full_market_run.py

输出：
- a_share_full_market_results.jsonl  每行一只的 JSON 结果
- a_share_full_market_progress.json    已完成代码集合（断点续跑）

非投资建议。
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_REPO_ROOT = Path(__file__).resolve().parent
_TA_ROOT = _REPO_ROOT / "TradingAgents-main"
if str(_TA_ROOT) not in sys.path:
    sys.path.insert(0, str(_TA_ROOT))

from dotenv import load_dotenv

# 复用交易日与配置逻辑
import a_share_daily_run as asd

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

CN_TZ = ZoneInfo("Asia/Shanghai")
CODES_CACHE = _REPO_ROOT / "a_share_all_codes_cache.json"
PROGRESS_PATH = _REPO_ROOT / "a_share_full_market_progress.json"
RESULTS_PATH = _REPO_ROOT / "a_share_full_market_results.jsonl"


def _cn_numeric_code_to_yfinance(code: str) -> str:
    """6→沪 .SS；0/3→深 .SZ；4/8/9→北 .BJ（含 920 等）。"""
    x = str(code).strip().zfill(6)
    if x.startswith("6"):
        return f"{x}.SS"
    if x[0] in "03":
        return f"{x}.SZ"
    if x[0] in "489":
        return f"{x}.BJ"
    return f"{x}.SZ"


def _fetch_all_a_codes_from_akshare() -> list[str]:
    import akshare as ak

    print("正在从 AkShare 拉取全市场 A 股列表（stock_zh_a_spot_em，可能需数分钟）...", flush=True)
    df = ak.stock_zh_a_spot_em()
    if df is None or df.empty or "代码" not in df.columns:
        raise RuntimeError("无法获取 A 股列表")
    codes = df["代码"].astype(str).str.strip().unique().tolist()
    out = sorted(_cn_numeric_code_to_yfinance(c) for c in codes)
    return out


def _load_cached_codes() -> list[str] | None:
    if not CODES_CACHE.exists():
        return None
    try:
        data = json.loads(CODES_CACHE.read_text(encoding="utf-8"))
        codes = data.get("codes")
        if isinstance(codes, list) and codes:
            return codes
    except Exception:
        pass
    return None


def _save_codes_cache(codes: list[str]) -> None:
    CODES_CACHE.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(CN_TZ).isoformat(),
                "count": len(codes),
                "codes": codes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _get_universe() -> list[str]:
    if os.getenv("A_SHARE_FULL_USE_UNIVERSE_FILE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        p = _REPO_ROOT / "a_share_universe.txt"
        print(f"使用股票池文件（测试）: {p}", flush=True)
        return asd._load_universe(p)

    if os.getenv("A_SHARE_FULL_REFRESH_CODES", "").strip().lower() in ("1", "true", "yes"):
        codes = _fetch_all_a_codes_from_akshare()
        _save_codes_cache(codes)
        return codes
    cached = _load_cached_codes()
    if cached is not None:
        print(f"使用缓存代码表: {CODES_CACHE}（{len(cached)} 只）", flush=True)
        return cached
    codes = _fetch_all_a_codes_from_akshare()
    _save_codes_cache(codes)
    return codes


def _load_done() -> set[str]:
    if not PROGRESS_PATH.exists():
        return set()
    try:
        data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        return set(data.get("done", []))
    except Exception:
        return set()


def _save_done(done: set[str]) -> None:
    PROGRESS_PATH.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(CN_TZ).isoformat(),
                "count": len(done),
                "done": sorted(done),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _append_result_line(obj: dict) -> None:
    with open(RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _build_full_market_config() -> dict:
    cfg = asd._build_config()
    # 全市场：默认轻量，避免新闻/AkShare 拖垮单只耗时
    if os.getenv("A_SHARE_FULL_LIGHT", "1").strip().lower() in ("1", "true", "yes"):
        cfg["a_share_enriched_news"] = False
        cfg["a_share_use_akshare"] = False
    return cfg


def main() -> int:
    load_dotenv(_TA_ROOT / ".env")
    load_dotenv(_REPO_ROOT / ".env")

    max_n = int(os.getenv("A_SHARE_FULL_MAX", "20"))
    offset = int(os.getenv("A_SHARE_FULL_OFFSET", "0"))
    confirm = os.getenv("A_SHARE_FULL_CONFIRM", "").strip().lower() in ("1", "true", "yes")

    if max_n == 0 and not confirm:
        print(
            "错误: A_SHARE_FULL_MAX=0 表示不限制数量，必须设置 A_SHARE_FULL_CONFIRM=1 以确认。",
            file=sys.stderr,
        )
        return 2

    if max_n > 500 and not confirm:
        print(
            "错误: A_SHARE_FULL_MAX>500 时必须设置 A_SHARE_FULL_CONFIRM=1。",
            file=sys.stderr,
        )
        return 2

    all_codes = _get_universe()
    slice_codes = all_codes[offset:]
    if max_n > 0:
        slice_codes = slice_codes[:max_n]

    if not slice_codes:
        print("没有待处理标的（检查 OFFSET / MAX）。")
        return 0

    now_cn = datetime.now(CN_TZ)
    trade_date, trade_reason = asd._resolve_trade_date(now_cn)

    cfg = _build_full_market_config()
    analysts_env = os.getenv("A_SHARE_FULL_ANALYSTS", "market").strip()
    analysts = [x.strip().lower() for x in analysts_env.split(",") if x.strip()]
    if not analysts:
        analysts = ["market"]

    print(
        f"本批: {len(slice_codes)} 只 | trade_date={trade_date} ({trade_reason}) | "
        f"分析师={analysts} | LLM={cfg.get('llm_provider')} / {cfg.get('quick_think_llm')}",
        flush=True,
    )

    done = _load_done()
    cfg["project_dir"] = str(_TA_ROOT / "tradingagents")
    cfg["results_dir"] = os.getenv(
        "TRADINGAGENTS_RESULTS_DIR", str(_REPO_ROOT / "tradingagents_results")
    )
    cfg["data_cache_dir"] = os.path.join(cfg["project_dir"], "dataflows", "data_cache")

    graph = TradingAgentsGraph(selected_analysts=analysts, debug=False, config=cfg)

    processed = 0
    skipped = 0
    for sym in slice_codes:
        if sym in done:
            skipped += 1
            continue
        t0 = time.perf_counter()
        row: dict = {"symbol": sym, "trade_date": trade_date.isoformat(), "ok": False}
        try:
            state, rating = graph.propagate(sym, trade_date.isoformat())
            row["ok"] = True
            row["rating"] = str(rating).strip()
            row["final_excerpt"] = (state.get("final_trade_decision") or "")[:2000]
            done.add(sym)
            _save_done(done)
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            done.add(sym)
            _save_done(done)
        row["elapsed_sec"] = round(time.perf_counter() - t0, 2)
        _append_result_line(row)
        processed += 1
        print(f"[{processed}/{len(slice_codes)}] {sym} ok={row['ok']} {row.get('elapsed_sec')}s", flush=True)

    print(f"完成: 处理 {processed}，跳过已完成 {skipped}，进度文件 {PROGRESS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
