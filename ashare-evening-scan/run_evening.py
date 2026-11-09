#!/usr/bin/env python3
"""晚筛细扫入口：价值分板 + 技术独立 + 全A超跌。扫描≠买卖灯。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# hyphenated directory is not an importable package; load sibling modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CACHE_DIR, OUT_DIR, PRICE_ASOF, now_cn  # noqa: E402
from fetch import (  # noqa: E402
    collect,
    fetch_sina_quotes,
    fetch_tencent_quotes,
    fill_sleeves,
    session,
    universe_from_cache,
)
from report import (  # noqa: E402
    a_trigger_text,
    build_digest,
    build_oversold_md,
    build_tech_md,
    build_value_md,
    oversold_reason,
    slim_row,
    tech_reason,
    value_reason,
    vs_morning_oversold,
    vs_morning_value,
)
from screens import (  # noqa: E402
    board_valuation_medians,
    pick_oversold,
    pick_tech,
    pick_value_by_board,
    score_row,
)
from store import dump_json, load_json  # noqa: E402


def score_all(universe: list[dict], extra: dict) -> list[dict]:
    print("[5] scoring ...", flush=True)
    scored = [score_row(u, extra) for u in universe]
    print(f"[5] scored={len(scored)}", flush=True)
    return scored


def write_outputs(
    scored: list[dict],
    extra: dict,
    fetch_meta: dict,
    sina: dict,
    tencent: dict,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    medians = board_valuation_medians(scored)
    value_picked, value_funnel = pick_value_by_board(scored, medians)
    value_codes = {x["code"] for arr in value_picked.values() for x in arr}
    tech_picked, tech_funnel = pick_tech(scored, value_codes)
    oversold_picked, oversold_funnel = pick_oversold(scored)

    print("[6] value", {b: [x["code"] for x in arr] for b, arr in value_picked.items()}, flush=True)
    print("[6] tech", [x["code"] for x in tech_picked], flush=True)
    print("[6] oversold", [x["code"] for x in oversold_picked], flush=True)

    value_md = build_value_md(value_picked, value_funnel, medians, extra, sina, tencent, fetch_meta, scored)
    tech_md = build_tech_md(tech_picked, tech_funnel, sina, tencent, fetch_meta, value_codes)
    oversold_md = build_oversold_md(oversold_picked, oversold_funnel, extra, sina, tencent, fetch_meta, scored)
    digest_md = build_digest(
        value_picked,
        tech_picked,
        oversold_picked,
        value_funnel,
        tech_funnel,
        oversold_funnel,
        medians,
        sina,
        tencent,
        scored,
        fetch_meta,
    )

    (OUT_DIR / "late-screen-value-byboard.md").write_text(value_md, encoding="utf-8")
    (OUT_DIR / "late-screen-tech.md").write_text(tech_md, encoding="utf-8")
    (OUT_DIR / "late-screen-oversold.md").write_text(oversold_md, encoding="utf-8")
    (OUT_DIR / "late-screen-digest-for-invest.md").write_text(digest_md, encoding="utf-8")

    dump_json(
        OUT_DIR / "late-screen-value-byboard.json",
        {
            "price_asof": PRICE_ASOF,
            "fetched_at": now_cn(),
            "disclaimer": "扫描≠买卖灯｜教育模拟",
            "funnel": value_funnel,
            "medians": medians,
            "vs_morning": vs_morning_value(value_picked),
            "shortlist": {
                b: [slim_row(x, sina, tencent, value_reason(x, medians)) for x in arr]
                for b, arr in value_picked.items()
            },
        },
    )
    dump_json(
        OUT_DIR / "late-screen-tech.json",
        {
            "price_asof": PRICE_ASOF,
            "fetched_at": now_cn(),
            "disclaimer": "扫描≠买卖灯｜教育模拟",
            "funnel": tech_funnel,
            "shortlist": [slim_row(x, sina, tencent, tech_reason(x)) for x in tech_picked],
        },
    )
    dump_json(
        OUT_DIR / "late-screen-oversold.json",
        {
            "price_asof": PRICE_ASOF,
            "fetched_at": now_cn(),
            "disclaimer": "扫描≠买卖灯｜建议并乙｜教育模拟",
            "funnel": oversold_funnel,
            "vs_morning_1106": vs_morning_oversold(scored, oversold_picked),
            "shortlist": [
                slim_row(x, sina, tencent, a_trigger_text(x) + "｜" + oversold_reason(x)) for x in oversold_picked
            ],
        },
    )
    print(f"[8] wrote {OUT_DIR}", flush=True)


def zt_height(extra: dict) -> int:
    h = 0
    for pool in (extra.get("zt") or {}).values():
        for x in pool:
            try:
                h = max(h, int(x.get("lbc") or 0))
            except Exception:
                pass
    return h


def main() -> int:
    parser = argparse.ArgumentParser(description="A-share evening late screen (scan≠order)")
    parser.add_argument("--stage", default="all", choices=["all", "collect", "report"])
    args = parser.parse_args()

    scored_path = CACHE_DIR / "scored.json"
    s = session()

    if args.stage in ("all", "collect"):
        bundle = collect(s)
        extra = bundle["extra"]
        scored = score_all(bundle["universe"], extra)
        slim = []
        for x in scored:
            y = dict(x)
            y.pop("bars", None)
            slim.append(y)
        dump_json(
            scored_path,
            {
                "extra": extra,
                "empty_kline": bundle["empty_kline"],
                "skipped_names": bundle.get("skipped_names") or extra.get("skipped_names") or [],
                "scored": slim,
            },
        )
        if args.stage == "collect":
            return 0

    print("[5b] fill sleeves + rescore from kline cache ...", flush=True)
    universe, extra, empty = universe_from_cache()
    extra = fill_sleeves(session(), extra)
    dump_json(CACHE_DIR / "extra.json", extra)
    extra["clist_total"] = extra.get("clist_total")
    scored = score_all(universe, extra)
    slim = []
    for x in scored:
        y = dict(x)
        y.pop("bars", None)
        slim.append(y)
    dump_json(
        scored_path,
        {
            "extra": extra,
            "empty_kline": empty,
            "skipped_names": extra.get("skipped_names") or [],
            "scored": slim,
        },
    )
    blob = {"extra": extra, "empty_kline": empty, "scored": slim}
    scored = blob["scored"]
    extra = blob["extra"]
    empty_names = [(x["code"], x["name"]) for x in scored if not x.get("n_bars")]
    fetch_meta = {
        "clist_total": extra.get("clist_total") or 5563,
        "empty_kline": blob.get("empty_kline"),
        "empty_names": empty_names,
        "skipped_non_hs_a": extra.get("skipped_non_hs_a"),
        "skipped_names": extra.get("skipped_names") or [],
        "zt_height": zt_height(extra),
        "oil_bk": extra.get("oil_bk"),
        "opt_bk": extra.get("opt_bk"),
        "ai_bk": extra.get("ai_bk"),
    }

    codes = set()
    # pick first to know whom to quote
    medians = board_valuation_medians(scored)
    value_picked, _ = pick_value_by_board(scored, medians)
    value_codes = {x["code"] for arr in value_picked.values() for x in arr}
    tech_picked, _ = pick_tech(scored, value_codes)
    oversold_picked, _ = pick_oversold(scored)
    for x in [*tech_picked, *oversold_picked]:
        codes.add(x["code"])
    for arr in value_picked.values():
        for x in arr:
            codes.add(x["code"])
    for c in HELD_CODES():
        codes.add(c)
    for c, _n in __import__("config", fromlist=["MORNING_OVERSOLD"]).MORNING_OVERSOLD:
        codes.add(c)

    print(f"[7] sina+tencent cross quotes n={len(codes)} ...", flush=True)
    sina = fetch_sina_quotes(session(), sorted(codes))
    tencent = fetch_tencent_quotes(session(), sorted(codes))
    fetch_meta["sina_ok"] = len(sina)
    fetch_meta["tencent_ok"] = len(tencent)
    write_outputs(scored, extra, fetch_meta, sina, tencent)
    return 0


def HELD_CODES() -> list[str]:
    from config import HELD

    return list(HELD)


if __name__ == "__main__":
    raise SystemExit(main())
