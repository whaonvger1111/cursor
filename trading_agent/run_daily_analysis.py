#!/usr/bin/env python3
"""定时任务入口：A 股相关标的日线规则化分析（见 trading_agent.analyze）。"""

from trading_agent.analyze import run_analysis
from trading_agent.config import get_symbols, lookback_days


def main() -> None:
    symbols = get_symbols()
    text = run_analysis(symbols, lookback_days())
    print(text)


if __name__ == "__main__":
    main()
