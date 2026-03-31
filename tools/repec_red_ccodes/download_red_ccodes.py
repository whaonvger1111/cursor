#!/usr/bin/env python3
"""
Download replication files from URLs in index_macro.jsonl (or index_all.jsonl).

Usage:
  python3 download_red_ccodes.py --index ../../data/red_ccodes/index_macro.jsonl --max 5
  python3 download_red_ccodes.py --index ../../data/red_ccodes/index_macro.jsonl --id 23-118

Default output: workspace/data/red_ccodes/downloads/
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "repec-red-download/1.0 (research; local)"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--index",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data/red_ccodes/index_macro.jsonl",
    )
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--max", type=int, default=0, help="Max number of items (0=all)")
    ap.add_argument("--delay", type=float, default=0.5, help="Seconds between downloads")
    ap.add_argument("--id", type=str, default="", help="Only this RED code id, e.g. 23-118")
    args = ap.parse_args()

    out_root = args.out or Path(__file__).resolve().parents[2] / "data/red_ccodes/downloads"
    out_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    with args.index.open(encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    if args.id:
        rows = [r for r in rows if r.get("id") == args.id]
    if args.max:
        rows = rows[: args.max]

    log = out_root / "download_log.txt"
    n_ok = 0
    with log.open("w", encoding="utf-8") as lg:
        for r in rows:
            cid = r.get("id", "unknown")
            urls = r.get("file_urls") or []
            if not urls:
                lg.write(f"{cid}: no file_urls\n")
                continue
            sub = out_root / cid
            sub.mkdir(parents=True, exist_ok=True)
            for u in urls:
                name = u.rsplit("/", 1)[-1].split("?")[0] or "file.bin"
                dest = sub / name
                try:
                    time.sleep(args.delay)
                    fetch(u, dest)
                    lg.write(f"{cid}: OK {u} -> {dest}\n")
                    n_ok += 1
                except Exception as e:
                    lg.write(f"{cid}: FAIL {u} ({e})\n")
    print(f"Done. Files attempted under {out_root}. See {log} ({n_ok} successful file fetches).")


if __name__ == "__main__":
    main()
