#!/usr/bin/env python3
"""Monitor A-share trading signals from a watchlist."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from a_share_monitor.data import fetch_history, fetch_quotes, normalize_code
from a_share_monitor.indicators import add_indicators
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


def scan_watchlist(codes: list[str], history_days: int = 180) -> list[Signal]:
    quotes = fetch_quotes(codes)
    all_signals: list[Signal] = []

    for code in codes:
        name = quotes.get(code).name if code in quotes else code
        try:
            df = fetch_history(code, days=history_days)
            enriched = add_indicators(df)
            all_signals.extend(detect_signals(code, name, enriched))
        except Exception as exc:  # noqa: BLE001 - surface per-symbol failures in scan output
            print(f"[WARN] {code}: {exc}", file=sys.stderr)

    return all_signals


def format_signal(signal: Signal) -> str:
    return (
        f"[{signal.direction:4}] {signal.code} {signal.name:8} "
        f"{signal.signal_type:12} {signal.strength:6} "
        f"price={signal.price:>8.2f} | {signal.detail}"
    )


def print_report(codes: list[str], signals: list[Signal]) -> None:
    quotes = fetch_quotes(codes)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== A-share Signal Report @ {now} ===")
    print(f"Watchlist: {len(codes)} symbols\n")

    print("Latest quotes:")
    for code in codes:
        quote = quotes.get(code)
        if quote is None:
            print(f"  {code}: quote unavailable")
            continue
        print(
            f"  {quote.code} {quote.name:8} "
            f"price={quote.price:>8.2f} chg={quote.change_pct:>6.2f}% "
            f"vol={quote.volume:,}"
        )

    print("\nSignals:")
    if not signals:
        print("  (no signals triggered)")
        return

    for signal in signals:
        print(" ", format_signal(signal))


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
        signals = scan_watchlist(codes, history_days=history_days)
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

    scan = sub.add_parser("scan", help="Run a one-time signal scan")
    add_common_args(scan)
    scan.set_defaults(func="scan")

    watch = sub.add_parser("watch", help="Continuously monitor signals")
    add_common_args(watch)
    watch.add_argument("--interval", type=int, default=300, help="Polling interval in seconds")
    watch.set_defaults(func="watch")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.codes:
        codes = [normalize_code(code) for code in args.codes]
    else:
        codes = load_watchlist(args.watchlist)

    if args.command == "scan":
        signals = scan_watchlist(codes, history_days=args.history_days)
        print_report(codes, signals)
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
