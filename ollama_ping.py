#!/usr/bin/env python3
"""
轻量自检：验证本机 Ollama 是否可用，以及 TradingAgents 的 OpenAI 兼容客户端能否对话。
不运行 LangGraph、不拉行情，适合 cron / 启动脚本快速探测。

用法:
  python3 ollama_ping.py
  OLLAMA_MODEL=llama3.2:3b python3 ollama_ping.py
  OLLAMA_HOST=http://192.168.1.10:11434 python3 ollama_ping.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parent
_TA = _REPO / "TradingAgents-main"
if _TA.is_dir() and str(_TA) not in sys.path:
    sys.path.insert(0, str(_TA))


def _http_get(url: str, timeout: float = 5.0) -> tuple[int, bytes]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return getattr(resp, "status", 200), resp.read()


def check_ollama_tags(host: str) -> bool:
    base = host.rstrip("/")
    try:
        code, body = _http_get(f"{base}/api/tags")
        if code != 200:
            return False
        data = json.loads(body.decode("utf-8", errors="replace"))
        models = data.get("models") or []
        print(f"[ok] Ollama 可达: {base}，已安装模型数: {len(models)}")
        for m in models[:8]:
            name = m.get("name", "?")
            print(f"     - {name}")
        if len(models) > 8:
            print(f"     ... 另有 {len(models) - 8} 个")
        return True
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as e:
        print(f"[fail] 无法连接 Ollama ({base}): {e}")
        return False


def check_tradingagents_llm(model: str) -> bool:
    os.environ.setdefault("LLM_PROVIDER", "ollama")
    try:
        from tradingagents.llm_clients.factory import create_llm_client

        llm = create_llm_client("ollama", model).get_llm()
        r = llm.invoke([("human", "只回复两个字：连通")])
        text = (r.content or "").strip()
        print(f"[ok] TradingAgents LLM 调用成功，模型={model}")
        print(f"     回复摘录: {text[:200]}")
        return True
    except Exception as e:
        print(f"[fail] TradingAgents LLM 调用失败: {type(e).__name__}: {e}")
        return False


def main() -> int:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
    model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b").strip()

    print("=== Ollama 连通性自检 ===\n")
    if not check_ollama_tags(host):
        print("\n提示: 请先在本机执行 `ollama serve` 或安装并启动 Ollama 服务。")
        return 1

    print()
    if not check_tradingagents_llm(model):
        return 2

    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
