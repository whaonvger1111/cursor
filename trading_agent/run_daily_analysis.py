#!/usr/bin/env python3
"""Entry point for scheduled daily stock analysis."""

from trading_agent.analyze import run_analysis
from trading_agent.config import get_symbols, lookback_days


def main() -> None:
    symbols = get_symbols()
    text = run_analysis(symbols, lookback_days())
    print(text)


if __name__ == "__main__":
    main()
