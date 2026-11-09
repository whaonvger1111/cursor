"""三线打分与短名单：价值分板 / 技术独立 / 全A超跌。"""

from __future__ import annotations

from collections import Counter
from typing import Any

try:
    from .config import (
        BANK_CAP,
        CLEARED,
        HELD,
        OIL_SHIP_CODES,
        OPTICAL_MODULE_CODES,
        OPTICAL_NAME_KEYS,
        OVERSOLD_PB_MAX,
        OVERSOLD_PB_MIN,
        OVERSOLD_PE_MAX,
        OVERSOLD_PE_MIN,
        VALUE_GEM_PB_MAX,
        VALUE_GEM_PE_MAX,
        VALUE_MAIN_PB_MAX,
        VALUE_STAR_PB_MAX,
        VALUE_STAR_PE_MAX,
    )
    from .metrics import (
        a_hits_of,
        apply_limit_flags,
        gap_up_pct,
        is_bank,
        is_gap_up_over,
        is_power_stock,
        is_st,
        median,
        metrics_from_bars,
    )
except ImportError:
    from config import (
        BANK_CAP,
        CLEARED,
        HELD,
        OIL_SHIP_CODES,
        OPTICAL_MODULE_CODES,
        OPTICAL_NAME_KEYS,
        OVERSOLD_PB_MAX,
        OVERSOLD_PB_MIN,
        OVERSOLD_PE_MAX,
        OVERSOLD_PE_MIN,
        VALUE_GEM_PB_MAX,
        VALUE_GEM_PE_MAX,
        VALUE_MAIN_PB_MAX,
        VALUE_STAR_PB_MAX,
        VALUE_STAR_PE_MAX,
    )
    from metrics import (
        a_hits_of,
        apply_limit_flags,
        gap_up_pct,
        is_bank,
        is_gap_up_over,
        is_power_stock,
        is_st,
        median,
        metrics_from_bars,
    )


def _sleeve_sets(extra: dict) -> tuple[set[str], set[str], set[str], set[str]]:
    oil = set(extra.get("oil_codes") or []) | set(extra.get("ship_codes") or []) | OIL_SHIP_CODES
    oil = {c for c in oil if len(c) == 6 and c[0] in "036"}
    # 光模块只走代码+简称兜底。BK1136 常混入连接器/PCB/CIS，不能整组当忌追袖。
    bk_opt = set(extra.get("opt_codes") or [])
    opt = set(OPTICAL_MODULE_CODES)
    if 0 < len(bk_opt) <= 40:
        opt |= bk_opt
    ai = set(extra.get("ai_codes") or [])
    power = set(extra.get("power_codes") or [])
    return oil, opt, ai, power


def _zt_sets(extra: dict) -> tuple[set[str], set[str], int]:
    zt_codes: set[str] = set()
    zt_lianban: set[str] = set()
    max_height = 0
    today_pool = extra.get("zt", {}).get("20261109") or []
    for d, pool in (extra.get("zt") or {}).items():
        for x in pool:
            c = str(x.get("c") or "")
            if not c:
                continue
            zt_codes.add(c)
            try:
                lbc = int(x.get("lbc") or 0)
            except Exception:
                lbc = 0
            if lbc >= 2:
                zt_lianban.add(c)
            max_height = max(max_height, lbc)
    for x in today_pool:
        try:
            max_height = max(max_height, int(x.get("lbc") or 0))
        except Exception:
            pass
    return zt_codes, zt_lianban, max_height


def score_row(u: dict, extra: dict) -> dict:
    bars = u.get("bars") or []
    m = metrics_from_bars(bars)
    apply_limit_flags(m, bars, u["board"])
    hits = a_hits_of(m)
    oil, opt, ai, power_codes = _sleeve_sets(extra)
    zt_codes, zt_lianban, zt_height = _zt_sets(extra)

    if u.get("close") in (None, 0) and m.get("k_close"):
        u["close"] = m["k_close"]
    if u.get("open") in (None, 0) and m.get("k_open"):
        u["open"] = m["k_open"]
    if u.get("prev_close") in (None, 0) and m.get("k_prev_close"):
        u["prev_close"] = m["k_prev_close"]

    open_px = u.get("open") or m.get("k_open")
    prev = u.get("prev_close") or m.get("k_prev_close")
    gap = gap_up_pct(open_px, prev)

    name, ind, code = u["name"], u.get("industry"), u["code"]
    c_reasons: list[str] = []
    if is_st(name):
        c_reasons.append("ST")
    live_px = u.get("close") or m.get("k_close")
    if live_px in (None, 0):
        c_reasons.append("停牌或无价")
    if is_power_stock(name, ind) or code in power_codes:
        c_reasons.append("电力")
    if code in oil:
        c_reasons.append("忌追袖·油运")
    if code in opt or any(k in (name or "") for k in OPTICAL_NAME_KEYS):
        c_reasons.append("忌追袖·光模块")
    if code in zt_lianban:
        c_reasons.append("连板")
    if m.get("limit_up_5d") or m.get("near_board_5d"):
        c_reasons.append("近板")
    if code in zt_codes and (u.get("pct") or 0) >= 5:
        c_reasons.append("涨停池残续")
    # AI 设备链残续硬追：概念内且近板/大涨
    if code in ai and (m.get("near_board_5d") or m.get("limit_up_5d") or (u.get("pct") or 0) >= 5):
        c_reasons.append("忌追袖·AI设备链残续")

    avg_amt = m.get("avg_amount_5d")
    avg_to = m.get("avg_turnover_5d")
    zombie = False
    if avg_amt is not None and avg_amt < 3_000_000 and (avg_to is None or avg_to < 0.40):
        zombie = True
    if (avg_to is not None and avg_to < 0.12) and (avg_amt is None or avg_amt < 12_000_000):
        zombie = True
    if zombie:
        c_reasons.append("无量僵尸")
    if is_gap_up_over(open_px, prev):
        c_reasons.append("高开>1%")

    pe, pb = u.get("pe"), u.get("pb")
    b_notes = []
    if pe is not None and pe > 0:
        b_notes.append(f"PE={pe:.1f}")
    else:
        b_notes.append("PE非正或缺失")
    if pb is not None:
        b_notes.append(f"PB={pb:.2f}")
        if 0 < pb < 1:
            b_notes.append("破净")
        elif pb >= 8:
            b_notes.append("畸高PB")
    else:
        b_notes.append("PB缺失")
    if pe is not None and pe > 80:
        b_notes.append("畸高PE")
    b_notes.append("脉冲阴跌" if m.get("pulse") else "非脉冲")
    if not is_st(name):
        b_notes.append("非ST")

    value_penalty = 0
    if pe is None or pe <= 0:
        value_penalty += 25
    elif pe > 80:
        value_penalty += 40
    elif pe > 40:
        value_penalty += 15
    if pb is None:
        value_penalty += 10
    elif pb >= 8:
        value_penalty += 30
    elif pb >= 4:
        value_penalty += 12
    if m.get("pulse"):
        value_penalty += 20

    oversold = 0.0
    if m.get("ret_20d") is not None:
        oversold += max(0.0, -m["ret_20d"]) * 40
    if m.get("ret_5d") is not None:
        oversold += max(0.0, -m["ret_5d"]) * 25
    if m.get("dev_ma20") is not None:
        oversold += max(0.0, -m["dev_ma20"]) * 40
    if m.get("pctile_60d") is not None:
        oversold += max(0.0, 0.40 - m["pctile_60d"]) * 30

    value_bonus = 0.0
    if pe is not None and 0 < pe <= 12:
        value_bonus += 18
    elif pe is not None and 0 < pe <= 20:
        value_bonus += 10
    elif pe is not None and 0 < pe <= 30:
        value_bonus += 4
    if pb is not None and 0 < pb < 1:
        value_bonus += 16
    elif pb is not None and 1 <= pb < 1.5:
        value_bonus += 10
    elif pb is not None and 1.5 <= pb < 2.5:
        value_bonus += 5

    n_hits = len(hits)
    rank_score = n_hits * 100 + oversold + value_bonus - value_penalty
    if code in HELD:
        rank_score -= 200
    if code in CLEARED:
        rank_score -= 80

    return {
        **u,
        "metrics": m,
        "a_hits": hits,
        "c_reasons": c_reasons,
        "b_notes": b_notes,
        "rank_score": rank_score,
        "gap_pct": gap,
        "is_bank": is_bank(ind, name),
        "is_held": code in HELD,
        "is_cleared": code in CLEARED,
        "oil_sleeve": code in oil,
        "opt_sleeve": code in opt,
        "ai_sleeve": code in ai,
        "zt_height_today": zt_height,
        "bars": None,
        "n_bars": m.get("n_bars"),
    }


def board_valuation_medians(scored: list[dict]) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for b in ("主板", "创业板", "科创板"):
        pes = [x["pe"] for x in scored if x["board"] == b and x.get("pe") and x["pe"] > 0]
        pbs = [x["pb"] for x in scored if x["board"] == b and x.get("pb") and x["pb"] > 0]
        out[b] = {"pe": median(pes), "pb": median(pbs), "n_pe": len(pes), "n_pb": len(pbs)}
    return out


def _kick_counter(rows: list[dict]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for x in rows:
        for r in x.get("c_reasons") or []:
            c[r] += 1
        if not x.get("n_bars"):
            c["K线空"] += 1
    return dict(c)


def pick_value_by_board(scored: list[dict], medians: dict) -> tuple[dict[str, list[dict]], dict]:
    """主板破净门；创业/科创相对低估放宽。各≤5。"""
    funnel: dict[str, Any] = {
        "universe": len(scored),
        "by_board": {},
        "kicked": _kick_counter(scored),
        "pass_gate": {},
        "pass_c_and_gap": {},
        "short_n": {},
    }
    picked: dict[str, list[dict]] = {"主板": [], "创业板": [], "科创板": []}

    def value_ok(x: dict) -> bool:
        pe, pb = x.get("pe"), x.get("pb")
        if pe is None or pe <= 0 or pb is None or pb <= 0:
            return False
        if x["board"] == "主板":
            return pb < VALUE_MAIN_PB_MAX and 1.5 <= pe <= 25
        med = medians.get(x["board"]) or {}
        med_pe = med.get("pe") or 30
        med_pb = med.get("pb") or 3
        if x["board"] == "创业板":
            return pe <= min(VALUE_GEM_PE_MAX, med_pe * 1.15) and pb <= min(VALUE_GEM_PB_MAX, max(med_pb * 1.25, 2.2))
        return pe <= min(VALUE_STAR_PE_MAX, med_pe * 1.20) and pb <= min(VALUE_STAR_PB_MAX, max(med_pb * 1.30, 2.8))

    def value_rank(x: dict) -> float:
        pe, pb = x.get("pe") or 99, x.get("pb") or 99
        med = medians.get(x["board"]) or {}
        med_pe = med.get("pe") or pe
        med_pb = med.get("pb") or pb
        rel_pe = pe / med_pe if med_pe else 1
        rel_pb = pb / med_pb if med_pb else 1
        mcap = x.get("mcap") or 0
        liq = min(12.0, (mcap / 1e10))  # 百亿档流动性加分，封顶
        cheap = (1.5 - min(rel_pe, 1.5)) * 40 + (1.5 - min(rel_pb, 1.5)) * 50
        if x["board"] == "主板" and pb < 1:
            cheap += (1 - pb) * 40
        return cheap + liq - (5 if x["metrics"].get("pulse") else 0)

    for b in ("主板", "创业板", "科创板"):
        board_rows = [x for x in scored if x["board"] == b]
        funnel["by_board"][b] = len(board_rows)
        gated = [x for x in board_rows if value_ok(x) and not x["is_held"] and not x["is_cleared"] and "退" not in (x.get("name") or "")]
        funnel["pass_gate"][b] = len(gated)
        clean = [x for x in gated if not x["c_reasons"]]
        funnel["pass_c_and_gap"][b] = len(clean)
        clean.sort(key=lambda z: -value_rank(z))
        taken: list[dict] = []
        banks = 0
        inds: dict[str, int] = {}
        for x in clean:
            if len(taken) >= 5:
                break
            if x["is_bank"]:
                if banks >= BANK_CAP:
                    continue
                # 银行只作对照，不占主板破净主推前席：放到末位候选，这里直接跳过强制席
                continue
            ind = x.get("industry") or "未知"
            if inds.get(ind, 0) >= 1:
                continue
            inds[ind] = inds.get(ind, 0) + 1
            taken.append(x)
        # 行业不够再放宽到同业 2
        if len(taken) < 5:
            for x in clean:
                if len(taken) >= 5:
                    break
                if x["code"] in {t["code"] for t in taken}:
                    continue
                if x["is_bank"]:
                    continue
                ind = x.get("industry") or "未知"
                if inds.get(ind, 0) >= 2:
                    continue
                inds[ind] = inds.get(ind, 0) + 1
                taken.append(x)
        picked[b] = taken[:5]
        funnel["short_n"][b] = len(taken)
        for x in taken:
            x["value_rank"] = round(value_rank(x), 2)
    return picked, funnel


def pick_tech(scored: list[dict], value_codes: set[str]) -> tuple[list[dict], dict]:
    """站上均线、非近板、高开≤1%；禁电力；勿复述价值票；已持不主推。"""
    funnel = {
        "universe": len(scored),
        "above_ma20": 0,
        "stack_ok": 0,
        "after_excludes": 0,
        "kicked_value_overlap": 0,
        "kicked_held": 0,
    }
    cands = []
    for x in scored:
        m = x["metrics"]
        if m.get("above_ma20"):
            funnel["above_ma20"] += 1
        if not m.get("above_ma20") or not m.get("ma5_gt_ma20"):
            continue
        # 未过度偏离均线（追高）
        if m.get("dev_ma20") is None or m["dev_ma20"] > 0.08:
            continue
        if m.get("dev_ma20") < 0:
            continue
        funnel["stack_ok"] += 1
        if x["code"] in value_codes:
            funnel["kicked_value_overlap"] += 1
            continue
        if x["is_held"] or x["is_cleared"]:
            funnel["kicked_held"] += 1
            continue
        if x["c_reasons"]:
            continue
        if x["is_bank"]:
            continue
        if (m.get("avg_amount_5d") or 0) < 20_000_000:
            continue
        r5 = m.get("ret_5d")
        if r5 is not None and (r5 > 0.10 or r5 < -0.04):
            continue
        funnel["after_excludes"] += 1
        cands.append(x)

    def tech_rank(x: dict) -> float:
        m = x["metrics"]
        stack = 20
        if m.get("above_ma60"):
            stack += 12
        tightness = max(0.0, 0.08 - abs(m.get("dev_ma20") or 0)) * 100
        liq = min(6.0, (x.get("mcap") or 0) / 8e10)
        return stack + tightness + liq

    cands.sort(key=lambda z: -tech_rank(z))
    picked: list[dict] = []
    inds: dict[str, int] = {}
    boards: dict[str, int] = {"主板": 0, "创业板": 0, "科创板": 0}
    board_cap = {"主板": 3, "创业板": 2, "科创板": 1}
    value_inds = {
        (x.get("industry") or "未知")
        for row in scored
        if row["code"] in value_codes
        for x in [row]
    }
    funnel["kicked_value_industry"] = 0
    for x in cands:
        if len(picked) >= 5:
            break
        ind = x.get("industry") or "未知"
        if ind in value_inds:
            funnel["kicked_value_industry"] += 1
            continue
        if inds.get(ind, 0) >= 1:
            continue
        if boards[x["board"]] >= board_cap[x["board"]]:
            continue
        inds[ind] = 1
        boards[x["board"]] += 1
        x["tech_rank"] = round(tech_rank(x), 2)
        picked.append(x)
    funnel["short_n"] = len(picked)
    funnel["kicked"] = _kick_counter(scored)
    return picked, funnel


def pick_oversold(scored: list[dict]) -> tuple[list[dict], dict]:
    funnel = {
        "universe": len(scored),
        "by_board": {},
        "kline_ok": 0,
        "pass_A": 0,
        "pass_A_by_board": {},
        "pass_A2plus": 0,
        "after_C": 0,
        "after_B_quality": 0,
        "kicked": _kick_counter(scored),
    }
    for b in ("主板", "创业板", "科创板"):
        funnel["by_board"][b] = sum(1 for x in scored if x["board"] == b)
        funnel["pass_A_by_board"][b] = 0

    candidates = []
    for x in scored:
        if x.get("n_bars"):
            funnel["kline_ok"] += 1
        if not x["a_hits"]:
            continue
        funnel["pass_A"] += 1
        funnel["pass_A_by_board"][x["board"]] += 1
        if len(x["a_hits"]) >= 2:
            funnel["pass_A2plus"] += 1
        if x["c_reasons"]:
            continue
        funnel["after_C"] += 1
        pe, pb = x.get("pe"), x.get("pb")
        if pe is None or pe < OVERSOLD_PE_MIN or pe > OVERSOLD_PE_MAX:
            continue
        if pb is None or pb < OVERSOLD_PB_MIN or pb >= OVERSOLD_PB_MAX:
            continue
        if "退" in (x.get("name") or ""):
            continue
        if x["metrics"].get("pulse") and len(x["a_hits"]) < 3:
            continue
        funnel["after_B_quality"] += 1
        candidates.append(x)

    candidates.sort(key=lambda z: (-len(z["a_hits"]), -z["rank_score"]))
    picked: list[dict] = []
    banks = 0
    board_cap = {"主板": 5, "创业板": 3, "科创板": 2}
    board_count = {"主板": 0, "创业板": 0, "科创板": 0}
    industry_count: dict[str, int] = {}

    def can_take(x: dict, *, min_hits: int, industry_cap: int) -> bool:
        if x["code"] in {p["code"] for p in picked}:
            return False
        if x["is_held"] or x["is_cleared"]:
            return False
        if len(x["a_hits"]) < min_hits:
            return False
        if x["is_bank"] and banks >= BANK_CAP:
            return False
        if x["is_bank"]:
            return False  # 对照不占强制席
        if board_count[x["board"]] >= board_cap[x["board"]]:
            return False
        ind = x.get("industry") or "未知"
        if industry_count.get(ind, 0) >= industry_cap:
            return False
        return True

    def take(x: dict) -> None:
        nonlocal banks
        picked.append(x)
        board_count[x["board"]] += 1
        ind = x.get("industry") or "未知"
        industry_count[ind] = industry_count.get(ind, 0) + 1
        if x["is_bank"]:
            banks += 1

    for min_hits, industry_cap in ((2, 1), (2, 2), (1, 2)):
        for x in candidates:
            if len(picked) >= 10:
                break
            if can_take(x, min_hits=min_hits, industry_cap=industry_cap):
                take(x)
        if len(picked) >= 5:
            break
    funnel["short_n"] = len(picked)
    return picked[:10], funnel


def align_of(x: dict) -> str:
    if x["board"] == "科创板":
        return "观察·不对齐本账户开仓"
    if x["board"] == "创业板":
        return "可对齐"
    if x["is_bank"]:
        return "仅对照·勿堆第二银行强制席"
    return "主板"
