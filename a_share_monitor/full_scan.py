#!/usr/bin/env python3
"""Scan main + chinext + star boards, merge, rank, and export JSON."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from a_share_monitor.data import fetch_quotes
from a_share_monitor.markets import MARKET_CHOICES, board_label, load_universe
from a_share_monitor.monitor import scan_codes
from a_share_monitor.rank import RankedStock, rank_signals


def ranked_to_dict(row: RankedStock) -> dict:
    return {
        "code": row.code,
        "name": row.name,
        "board": row.board,
        "board_label": board_label(row.board),
        "price": row.price,
        "buy_score": row.buy_score,
        "sell_score": row.sell_score,
        "net_score": row.net_score,
        "buy_signals": row.buy_signals,
        "sell_signals": row.sell_signals,
    }


def run_full_scan(
    boards: list[str],
    history_days: int,
    top_buy: int,
    top_sell: int,
) -> dict:
    all_universe = []
    all_signals = []
    board_counts: dict[str, int] = {}

    for board in boards:
        universe = load_universe(board)
        board_counts[board] = len(universe)
        all_universe.extend(universe)
        codes = [stock.code for stock in universe]
        print(f"=== Scanning {MARKET_CHOICES[board]} ({len(codes)} stocks) ===")
        all_signals.extend(scan_codes(codes, history_days=history_days))

    boards_map = {stock.code: stock.board for stock in all_universe}
    ranked = rank_signals(all_signals, boards=boards_map)
    buy_candidates = [r for r in ranked if r.net_score > 0]
    sell_candidates = sorted(
        [r for r in ranked if r.net_score < 0],
        key=lambda r: r.net_score,
    )

    quote_codes = [r.code for r in ranked[: max(top_buy, top_sell)]]
    quotes = fetch_quotes(quote_codes) if quote_codes else {}
    quote_times = sorted({q.updated_at for q in quotes.values() if q.updated_at})

    return {
        "scan_timestamp": datetime.now().isoformat(timespec="seconds"),
        "boards_scanned": boards,
        "board_counts": board_counts,
        "universe_size": len(all_universe),
        "signals_triggered": len(all_signals),
        "quote_timestamps": quote_times,
        "top_buy": [ranked_to_dict(r) for r in buy_candidates[:top_buy]],
        "top_sell": [ranked_to_dict(r) for r in sell_candidates[:top_sell]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Full A-share board scan with merged ranking")
    parser.add_argument(
        "--boards",
        nargs="+",
        default=["main", "chinext", "star"],
        choices=["main", "chinext", "star", "all"],
        help="Boards to scan (default: main chinext star)",
    )
    parser.add_argument("--history-days", type=int, default=180)
    parser.add_argument("--top-buy", type=int, default=50)
    parser.add_argument("--top-sell", type=int, default=50)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/opt/cursor/artifacts/full_market_scan.json"),
    )
    args = parser.parse_args()

    boards = ["main", "chinext", "star"] if "all" in args.boards else args.boards
    args.output.parent.mkdir(parents=True, exist_ok=True)

    payload = run_full_scan(boards, args.history_days, args.top_buy, args.top_sell)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved merged scan to {args.output}")
    print(f"Universe: {payload['universe_size']} | BUY hits: {len(payload['top_buy'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
