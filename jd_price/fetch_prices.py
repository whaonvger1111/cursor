#!/usr/bin/env python3
"""Fetch JD.com product prices by SKU (batch supported).

Uses the semi-public price endpoint (p.3.cn) when no API credentials are set.
With JD Union credentials, uses the official routerjson API instead.

Run from a residential/office network; datacenter IPs are often blocked.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

PRICE_API = "https://p.3.cn/prices/mgets"
SKU_IN_URL = re.compile(r"(?:item\.jd\.com|/product)/(\d+)", re.I)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


def parse_sku(value: str) -> str | None:
    """Extract numeric SKU from raw id or JD product URL."""
    value = value.strip()
    if value.isdigit():
        return value
    match = SKU_IN_URL.search(value)
    return match.group(1) if match else None


def load_skus(path: Path) -> list[str]:
    skus: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sku = parse_sku(line)
        if sku:
            skus.append(sku)
        else:
            print(f"警告: 无法解析 SKU，已跳过: {line}", file=sys.stderr)
    return skus


def chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def fetch_prices_public(
    sku_ids: list[str],
    *,
    session: requests.Session | None = None,
    delay_sec: float = 0.5,
) -> list[dict[str, Any]]:
    """Query p.3.cn price API (max ~100 SKUs per request in practice)."""
    session = session or requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    rows: list[dict[str, Any]] = []

    for batch in chunk(sku_ids, 50):
        params = {
            "skuIds": ",".join(f"J_{sku}" for sku in batch),
            "type": "1",
        }
        referer_sku = batch[0]
        headers = {"Referer": f"https://item.jd.com/{referer_sku}.html"}
        resp = session.get(PRICE_API, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError(f"Unexpected response: {data!r}")

        for item in data:
            raw_id = str(item.get("id", ""))
            sku = raw_id.replace("J_", "") if raw_id.startswith("J_") else raw_id
            rows.append(
                {
                    "sku": sku,
                    "price": item.get("p"),
                    "market_price": item.get("m"),
                    "original_price": item.get("op"),
                    "source": "p.3.cn",
                    "raw": item,
                }
            )
        if delay_sec > 0:
            time.sleep(delay_sec)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["sku", "price", "market_price", "original_price", "title", "source"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="批量获取京东商品价格（SKU 或商品链接）"
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="SKU 或 item.jd.com 链接，可多个",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="从文本文件读取 SKU/链接（每行一个）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="导出 CSV 路径",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="导出 JSON 路径",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="批次之间的请求间隔（秒），默认 0.8",
    )
    parser.add_argument(
        "--union",
        action="store_true",
        help="使用京东联盟官方 API（需配置环境变量，见 config.example.env）",
    )
    args = parser.parse_args(argv)

    sku_list: list[str] = []
    for arg in args.inputs:
        sku = parse_sku(arg)
        if sku:
            sku_list.append(sku)
        else:
            print(f"警告: 无法解析: {arg}", file=sys.stderr)
    if args.file:
        sku_list.extend(load_skus(args.file))

    # dedupe, preserve order
    seen: set[str] = set()
    skus: list[str] = []
    for s in sku_list:
        if s not in seen:
            seen.add(s)
            skus.append(s)

    if not skus:
        parser.error("请提供至少一个 SKU 或链接，或使用 -f 指定文件")

    try:
        if args.union:
            try:
                from jd_price.jd_union_api import fetch_prices_union
            except ImportError:
                from jd_union_api import fetch_prices_union

            rows = fetch_prices_union(skus, delay_sec=args.delay)
        else:
            rows = fetch_prices_public(skus, delay_sec=args.delay)
    except requests.RequestException as exc:
        print(
            "请求失败。常见原因：当前 IP 被京东限制（云服务器/机房 IP 易被拒）、"
            "网络不通或请求过快。请在本地网络重试，或加大 --delay，"
            "或使用 --union 配置官方 API。",
            file=sys.stderr,
        )
        print(f"详情: {exc}", file=sys.stderr)
        return 1

    for row in rows:
        print(
            f"SKU {row['sku']}: 现价 {row.get('price')} "
            f"市场价 {row.get('market_price')} [{row.get('source')}]"
        )

    if args.json:
        args.json.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"已写入 JSON: {args.json}")

    if args.output:
        write_csv(args.output, rows)
        print(f"已写入 CSV: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
