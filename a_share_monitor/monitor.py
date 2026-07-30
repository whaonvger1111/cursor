#!/usr/bin/env python3
"""Monitor A-share trading signals from a watchlist or full market boards."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import baostock as bs

from a_share_monitor.data import fetch_history, fetch_history_logged_in, fetch_quotes, normalize_code
from a_share_monitor.indicators import add_indicators
from a_share_monitor.markets import MARKET_CHOICES, StockInfo, board_label, load_universe
from a_share_monitor.rank import format_ranked, rank_signals
from a_share_monitor.session import baostock_session
from a_share_monitor.signals import Signal, detect_signals

DEFAULT_WATCHLIST = Path(__file__).resolve().parent / "watchlist.txt"


def load_watchlist(path: Path) -> list[str]:
    codes: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        codes.append(normalize_code(line))
    if not codes:
        raise ValueError(f"Watchlist is empty: {path}")
    return codes


def scan_codes(codes: list[str], history_days: int = 180, workers: int = 8) -> list[Signal]:
    quotes = fetch_quotes(codes)
    all_signals: list[Signal] = []

    with baostock_session():
        total = len(codes)
        for idx, code in enumerate(codes, start=1):
            name = quotes.get(code).name if code in quotes else code
            try:
                df = fetch_history_logged_in(code, days=history_days)
                enriched = add_indicators(df)
                all_signals.extend(detect_signals(code, name, enriched))
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                if "用户未登录" in msg:
                    relog = bs.login()
                    if relog.error_code == "0":
                        try:
                            df = fetch_history_logged_in(code, days=history_days)
                            enriched = add_indicators(df)
                            all_signals.extend(detect_signals(code, name, enriched))
                            continue
                        except Exception as retry_exc:  # noqa: BLE001
                            print(f"[WARN] {code}: {retry_exc}", file=sys.stderr)
                            continue
                print(f"[WARN] {code}: {exc}", file=sys.stderr)
            if idx % 50 == 0 or idx == total:
                print(f"Progress: {idx}/{total}", file=sys.stderr)

    return all_signals


def scan_market(
    market: str,
    history_days: int = 180,
    workers: int = 8,
    limit: int | None = None,
) -> tuple[list[StockInfo], list[Signal]]:
    universe = load_universe(market)
    if limit is not None:
        universe = universe[:limit]
    codes = [stock.code for stock in universe]
    print(
        f"Scanning {MARKET_CHOICES[market]}: {len(codes)} stocks "
        f"(workers={workers})",
        file=sys.stderr,
    )
    signals = scan_codes(codes, history_days=history_days, workers=workers)
    return universe, signals


def format_signal(signal: Signal) -> str:
    return (
        f"[{signal.direction:4}] {signal.code} {signal.name:8} "
        f"{signal.signal_type:12} {signal.strength:6} "
        f"price={signal.price:>8.2f} | {signal.detail}"
    )


def print_report(codes: list[str], signals: list[Signal], top: int = 20) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== A-share Signal Report @ {now} ===")
    print(f"Universe: {len(codes)} symbols\n")

    ranked = rank_signals(signals)
    buy_candidates = [r for r in ranked if r.net_score > 0][:top]
    sell_candidates = sorted(
        [r for r in ranked if r.net_score < 0],
        key=lambda r: r.net_score,
    )[:top]

    print(f"Top {len(buy_candidates)} BUY candidates (by signal score):")
    if not buy_candidates:
        print("  (none)")
    for idx, row in enumerate(buy_candidates, start=1):
        print(format_ranked(row, idx))

    print(f"\nTop {len(sell_candidates)} SELL/avoid candidates:")
    if not sell_candidates:
        print("  (none)")
    for idx, row in enumerate(sell_candidates, start=1):
        print(format_ranked(row, idx))

    print("\nAll triggered signals:")
    if not signals:
        print("  (no signals triggered)")
        return
    for signal in signals:
        print(" ", format_signal(signal))


def print_market_report(
    universe: list[StockInfo],
    signals: list[Signal],
    top: int = 20,
) -> None:
    boards = {stock.code: stock.board for stock in universe}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    board_counts: dict[str, int] = {}
    for stock in universe:
        board_counts[stock.board] = board_counts.get(stock.board, 0) + 1

    print(f"\n=== A-share Market Scan @ {now} ===")
    print(f"Universe size: {len(universe)}")
    for board, count in sorted(board_counts.items()):
        print(f"  - {board_label(board)}: {count}")

    ranked = rank_signals(signals, boards=boards)
    buy_candidates = [r for r in ranked if r.net_score > 0][:top]

    print(f"\nTop {len(buy_candidates)} BUY candidates:")
    if not buy_candidates:
        print("  (none)")
    for idx, row in enumerate(buy_candidates, start=1):
        print(format_ranked(row, idx))

    by_board: dict[str, list] = {}
    for row in buy_candidates:
        by_board.setdefault(row.board, []).append(row)

    print("\nBUY candidates by board:")
    for board in ("star", "chinext", "main"):
        rows = by_board.get(board, [])
        if not rows:
            continue
        print(f"  [{board_label(board)}]")
        for row in rows[:5]:
            print(f"    {row.code} {row.name} net={row.net_score:+d} price={row.price:.2f}")


def save_signals(path: Path, signals: list[Signal]) -> None:
    payload = [
        {
            "code": s.code,
            "name": s.name,
            "signal_type": s.signal_type,
            "direction": s.direction,
            "strength": s.strength,
            "price": s.price,
            "detail": s.detail,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        for s in signals
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def watch_loop(
    codes: list[str],
    interval_sec: int,
    history_days: int,
    output: Path | None,
) -> None:
    seen: set[tuple[str, str, str]] = set()
    print(f"Watching {len(codes)} symbols every {interval_sec}s. Press Ctrl+C to stop.")

    while True:
        signals = scan_codes(codes, history_days=history_days)
        fresh = [
            s for s in signals if (s.code, s.signal_type, s.detail) not in seen
        ]
        for signal in fresh:
            print(format_signal(signal))
            seen.add((signal.code, signal.signal_type, signal.detail))

        if output is not None:
            save_signals(output, signals)

        time.sleep(interval_sec)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor A-share trading signals")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--watchlist",
            type=Path,
            default=DEFAULT_WATCHLIST,
            help="Path to watchlist file (one code per line)",
        )
        p.add_argument(
            "--codes",
            nargs="*",
            help="Override watchlist with explicit codes, e.g. 600519 000001",
        )
        p.add_argument(
            "--history-days",
            type=int,
            default=180,
            help="Number of daily bars used for indicators",
        )
        p.add_argument(
            "--output",
            type=Path,
            help="Optional JSON file to save latest scan results",
        )
        p.add_argument(
            "--workers",
            type=int,
            default=8,
            help="Parallel workers for market scans",
        )
        p.add_argument(
            "--top",
            type=int,
            default=20,
            help="How many ranked candidates to print",
        )

    scan = sub.add_parser("scan", help="Run a one-time signal scan")
    add_common_args(scan)
    scan.add_argument(
        "--market",
        choices=list(MARKET_CHOICES),
        help="Scan a full market board instead of watchlist",
    )
    scan.add_argument(
        "--limit",
        type=int,
        help="Limit number of stocks when scanning a market (for testing)",
    )
    scan.set_defaults(func="scan")

    watch = sub.add_parser("watch", help="Continuously monitor signals")
    add_common_args(watch)
    watch.add_argument("--interval", type=int, default=300, help="Polling interval in seconds")
    watch.set_defaults(func="watch")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan" and args.market:
        universe, signals = scan_market(
            args.market,
            history_days=args.history_days,
            workers=args.workers,
            limit=args.limit,
        )
        print_market_report(universe, signals, top=args.top)
        if args.output:
            save_signals(args.output, signals)
            print(f"\nSaved signals to {args.output}")
        return 0

    if args.codes:
        codes = [normalize_code(code) for code in args.codes]
    else:
        codes = load_watchlist(args.watchlist)

    if args.command == "scan":
        signals = scan_codes(codes, history_days=args.history_days, workers=args.workers)
        print_report(codes, signals, top=args.top)
        if args.output:
            save_signals(args.output, signals)
            print(f"\nSaved signals to {args.output}")
        return 0

    if args.command == "watch":
        watch_loop(
            codes,
            interval_sec=args.interval,
            history_days=args.history_days,
            output=args.output,
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
