"""三线 markdown / json 交付。"""

from __future__ import annotations

from typing import Any

try:
    from .config import (
        CLEARED,
        HELD,
        MORNING_OVERSOLD,
        MORNING_VALUE_SIDE,
        PRICE_ASOF,
        WINDOW_NEXT,
        now_cn,
    )
    from .metrics import fmt_num, fmt_pct
    from .screens import align_of
except ImportError:
    from config import (
        CLEARED,
        HELD,
        MORNING_OVERSOLD,
        MORNING_VALUE_SIDE,
        PRICE_ASOF,
        WINDOW_NEXT,
        now_cn,
    )
    from metrics import fmt_num, fmt_pct
    from screens import align_of


def quote_triple(x: dict, sina: dict, tencent: dict) -> dict:
    code = x["code"]
    sq, tq = sina.get(code) or {}, tencent.get(code) or {}
    close = tq.get("close") or sq.get("close") or x.get("close")
    prev = tq.get("prev_close") or sq.get("prev_close") or x.get("prev_close")
    pct = None
    if close and prev:
        pct = (close / prev - 1.0) * 100
    elif x.get("pct") is not None:
        pct = x["pct"]
    return {
        "close": close,
        "prev": prev,
        "pct": pct,
        "sina": sq.get("close"),
        "tencent": tq.get("close"),
        "eastmoney": x.get("close"),
        "open": tq.get("open") or sq.get("open") or x.get("open"),
        "date": sq.get("date") or tq.get("date") or PRICE_ASOF,
    }


def short_line(x: dict, sina: dict, tencent: dict, reason: str) -> str:
    q = quote_triple(x, sina, tencent)
    pct = f"{q['pct']:+.2f}%" if q["pct"] is not None else "涨跌缺失"
    close = fmt_num(q["close"])
    return f"`{x['code']} {x['name']}` 收盘{close} {pct}｜{reason}"


def a_trigger_text(x: dict) -> str:
    m = x["metrics"]
    bits = []
    if "①" in x["a_hits"]:
        bits.append(f"①跌幅20d={fmt_pct(m.get('ret_20d'))}/5d={fmt_pct(m.get('ret_5d'))}")
    if "②" in x["a_hits"]:
        bits.append(f"②vsMA20={fmt_pct(m.get('dev_ma20'))}")
    if "③" in x["a_hits"]:
        p = m.get("pctile_60d")
        bits.append("③60d分位=" + (f"{p * 100:.0f}%" if p is not None else "缺失"))
    return "; ".join(bits) if bits else "无"


def b_sentence(x: dict) -> str:
    pe, pb = x.get("pe"), x.get("pb")
    parts = []
    if pb is not None and 0 < pb < 1:
        parts.append(f"破净PB={pb:.2f}")
    elif pb is not None:
        parts.append(f"PB={pb:.2f}")
    else:
        parts.append("PB缺失")
    if pe is not None and pe > 0:
        tag = "低PE" if pe <= 15 else "PE"
        parts.append(f"{tag}={pe:.1f}")
    else:
        parts.append("PE非正或缺失")
    parts.append("脉冲阴跌" if x["metrics"].get("pulse") else "非脉冲阴跌")
    return "；".join(parts)


def oversold_reason(x: dict) -> str:
    m = x["metrics"]
    p = m.get("pctile_60d")
    ptxt = f"{p * 100:.0f}%" if p is not None else "缺失"
    return (
        f"满A{len(x['a_hits'])}；20d {fmt_pct(m.get('ret_20d'))} / vsMA20 {fmt_pct(m.get('dev_ma20'))} / "
        f"60d分位 {ptxt}；行业{x.get('industry') or '缺失'}；PE={fmt_num(x.get('pe'), 1)}/PB={fmt_num(x.get('pb'))}"
    )


def value_reason(x: dict, medians: dict) -> str:
    pe, pb = x.get("pe"), x.get("pb")
    med = medians.get(x["board"]) or {}
    if x["board"] == "主板":
        gate = f"破净门PB={fmt_num(pb)}<1"
    else:
        gate = (
            f"相对低估 PE={fmt_num(pe, 1)}/板中位{fmt_num(med.get('pe'), 1)} "
            f"PB={fmt_num(pb)}/板中位{fmt_num(med.get('pb'))}"
        )
    gap = x.get("gap_pct")
    gap_s = fmt_pct(gap) if gap is not None else "缺失"
    return f"{gate}；行业{x.get('industry') or '缺失'}；高开{gap_s}；{align_of(x)}"


def tech_reason(x: dict) -> str:
    m = x["metrics"]
    stack = []
    if m.get("above_ma20"):
        stack.append("站上MA20")
    if m.get("ma5_gt_ma20"):
        stack.append("MA5>MA20")
    if m.get("above_ma60"):
        stack.append("站上MA60")
    return (
        f"{'/'.join(stack) or '均线'}；vsMA20 {fmt_pct(m.get('dev_ma20'))}；"
        f"非近板；高开{fmt_pct(x.get('gap_pct'))}；行业{x.get('industry') or '缺失'}"
    )


def name_of(scored: list[dict], code: str, fallback: str = "") -> str:
    hit = next((x for x in scored if x["code"] == code), None)
    if hit:
        return f"`{code} {hit['name']}`"
    return f"`{code} {fallback}`".rstrip() if fallback else f"`{code}`"


def vs_morning_oversold(scored: list[dict], picked: list[dict]) -> dict[str, list[str]]:
    short = {x["code"] for x in picked}
    keep, drop, new = [], [], []
    morning_codes = [c for c, _ in MORNING_OVERSOLD]
    for c, n in MORNING_OVERSOLD:
        if c in short:
            keep.append(c)
        else:
            drop.append(c)
    for x in picked:
        if x["code"] not in morning_codes:
            new.append(x["code"])
    return {"keep": keep, "drop": drop, "new": new}


def why_drop_oversold(scored: list[dict], code: str) -> str:
    x = next((z for z in scored if z["code"] == code), None)
    if x is None:
        return "本窗未入宇宙或K线失败"
    bits = []
    if not x["a_hits"]:
        m = x["metrics"]
        bits.append(
            f"A未过门(20d={fmt_pct(m.get('ret_20d'))},5d={fmt_pct(m.get('ret_5d'))},"
            f"MA20={fmt_pct(m.get('dev_ma20'))},60d分位={fmt_pct(m.get('pctile_60d'), 0)})"
        )
    else:
        bits.append("A=" + "".join(x["a_hits"]))
    if x["c_reasons"]:
        bits.append("C=" + ",".join(x["c_reasons"]))
    if x["is_held"]:
        bits.append("现持不占新观察")
    if not bits:
        bits.append("仍过A，分板/行业配额或估值排序未进前10")
    elif "C=" not in "；".join(bits) and x["a_hits"]:
        bits.append("分板/行业配额或排序未进前10")
    return "；".join(bits)


def vs_morning_value(picked_by_board: dict[str, list[dict]]) -> dict:
    out: dict[str, Any] = {}
    for b, morning in MORNING_VALUE_SIDE.items():
        eve = {x["code"] for x in picked_by_board.get(b, [])}
        keep = [c for c, _ in morning if c in eve]
        drop = [c for c, _ in morning if c not in eve]
        new = [x["code"] for x in picked_by_board.get(b, []) if x["code"] not in {c for c, _ in morning}]
        out[b] = {"keep": keep, "drop": drop, "new": new}
    return out


def header(title: str, fetched_at: str) -> list[str]:
    return [
        f"# {title}",
        "",
        f"> **窗口** {PRICE_ASOF} 收盘 → 次日 {WINDOW_NEXT}｜**price_asof** {PRICE_ASOF} 收盘｜"
        f"抓取 {fetched_at}｜价源：东财 clist+日K；短名单核价 新浪 `hq.sinajs.cn` + 腾讯 `qt.gtimg.cn`｜"
        "教育模拟｜**扫描 ≠ 买卖灯 ≠ 下单 ≠ 改灯**",
        "",
    ]


def held_line() -> str:
    return (
        "现持不占新观察主推："
        + "；".join(f"`{c} {n}`" for c, n in HELD.items())
        + "。已清不加回："
        + "；".join(f"`{c} {n}`" for c, n in CLEARED.items())
        + "。席5空。`603806 福斯特` 席6今日已入、勿再满开主推。"
    )


def quote_table(rows: list[dict], sina: dict, tencent: dict) -> list[str]:
    lines = [
        "## 核价（东财 / 新浪 / 腾讯）",
        "",
        "| 代码 | 东财收盘 | 新浪 | 腾讯 | asof |",
        "|------|----------|------|------|------|",
    ]
    for x in rows:
        q = quote_triple(x, sina, tencent)
        lines.append(
            f"| `{x['code']}` | {fmt_num(q['eastmoney'])} | {fmt_num(q['sina'])} | "
            f"{fmt_num(q['tencent'])} | {q['date']} |"
        )
    lines.append("")
    return lines


def build_value_md(
    picked: dict[str, list[dict]],
    funnel: dict,
    medians: dict,
    extra: dict,
    sina: dict,
    tencent: dict,
    fetch_meta: dict,
    scored: list[dict],
) -> str:
    fetched_at = now_cn()
    vs = vs_morning_value(picked)
    lines = header("晚筛细扫 · 线1 价值分板（主板破净 / 创业·科创相对低估）", fetched_at)
    lines += [
        "## 口径",
        "",
        "- 底层全板通扫；主板/创业/科创 **各≤5**。",
        "- 主板：**破净门 PB<1** 且 PE 落在 1.5–25；银行不占强制席。",
        "- 创业/科创：相对本板 PE/PB 中位放宽（创业 PE≤min(40,中位×1.15)、科创 PE≤min(55,中位×1.20)）。",
        "- 硬排除：电力（禁再开）、忌追袖（光模块/油运/连板近板/AI设备链残续硬追）、高开>1%、ST/无量僵尸/已持/已清。",
        "- 创业可对齐；科创一律 **观察·不对齐本账户开仓**。",
        "",
        "## 覆盖 / 踢出",
        "",
        f"- 宇宙 {funnel['universe']}（主板 {funnel['by_board'].get('主板', 0)} / "
        f"创业 {funnel['by_board'].get('创业板', 0)} / 科创 {funnel['by_board'].get('科创板', 0)}）。",
        f"- 估值门：主板 {funnel['pass_gate'].get('主板', 0)} / 创业 {funnel['pass_gate'].get('创业板', 0)} / "
        f"科创 {funnel['pass_gate'].get('科创板', 0)}。",
        f"- 过 C+高开：主板 {funnel['pass_c_and_gap'].get('主板', 0)} / 创业 {funnel['pass_c_and_gap'].get('创业板', 0)} / "
        f"科创 {funnel['pass_c_and_gap'].get('科创板', 0)}。",
        f"- 短名单：主板 {funnel['short_n'].get('主板', 0)} / 创业 {funnel['short_n'].get('创业板', 0)} / "
        f"科创 {funnel['short_n'].get('科创板', 0)}。",
        f"- 踢出计数（全宇宙，可重叠）：{funnel.get('kicked')}",
        f"- 板中位 PE/PB：主板 {fmt_num(medians.get('主板', {}).get('pe'), 1)}/{fmt_num(medians.get('主板', {}).get('pb'))}；"
        f"创业 {fmt_num(medians.get('创业板', {}).get('pe'), 1)}/{fmt_num(medians.get('创业板', {}).get('pb'))}；"
        f"科创 {fmt_num(medians.get('科创板', {}).get('pe'), 1)}/{fmt_num(medians.get('科创板', {}).get('pb'))}。",
        f"- 东财 clist reported_total={fetch_meta.get('clist_total')}；"
        f"跳过非60/00/300/301/688 "
        + ("、".join(f"`{c} {n}`" for c, n in (fetch_meta.get("skipped_names") or [])) or "无")
        + f"；K线空 {fetch_meta.get('empty_kline')}："
        + ("、".join(f"`{c} {n}`" for c, n in (fetch_meta.get("empty_names") or [])) or "无")
        + f"；涨停高度今日 max_lbc={fetch_meta.get('zt_height')}（闽发铝业 6 板）。",
        "",
        "## 方法盲点",
        "",
        "- 未全量核验立案/停牌公告全文；ST 按简称。缺 PE/PB/K 标「缺失」，不填假数。",
        "- 相对低估用东财动态 PE/PB 截面中位，非一致预期。电力按行业字段+火力发电概念，电力设备不杀。",
        "- 早盘「价值旁注」挂在超跌漏斗下，本窗是独立破净/相对低估门，维持少、纠偏多是口径切换，不是漏扫。",
        f"- {held_line()}",
        "",
    ]
    all_rows = []
    for b in ("主板", "创业板", "科创板"):
        lines.append(f"## {b}短名单（≤5）")
        lines.append("")
        arr = picked.get(b) or []
        if not arr:
            lines.append("（过门不足，不硬凑）")
            lines.append("")
            continue
        for x in arr:
            lines.append("- " + short_line(x, sina, tencent, value_reason(x, medians)))
            all_rows.append(x)
        lines.append("")
        v = vs.get(b) or {}
        lines.append(
            f"相对早盘价值旁注：维持 "
            + ("、".join(name_of(scored, c) for c in v.get("keep") or []) or "无")
            + "；新增 "
            + ("、".join(name_of(scored, c) for c in v.get("new") or []) or "无")
            + "；纠偏换出 "
            + ("、".join(name_of(scored, c) for c in v.get("drop") or []) or "无")
            + "。"
        )
        lines.append("")
    lines += quote_table(all_rows, sina, tencent)
    lines.append("扫描≠买卖灯｜教育模拟，非投资建议。")
    lines.append("")
    return "\n".join(lines)


def build_tech_md(
    picked: list[dict],
    funnel: dict,
    sina: dict,
    tencent: dict,
    fetch_meta: dict,
    value_codes: set[str],
) -> str:
    fetched_at = now_cn()
    lines = header("晚筛细扫 · 线2 技术独立（站上均线 / 非近板 / 高开≤1%）", fetched_at)
    lines += [
        "## 口径",
        "",
        "- 收盘站上 MA20 且 MA5>MA20；vsMA20 在 0–8%（未过度偏离）。",
        "- 非近板、高开≤1%；硬排除电力；已持/已清不主推；**不复述价值短名单**。",
        "- 独立≤5；创业可对齐，科创观察·不对齐。",
        "",
        "## 覆盖 / 踢出",
        "",
        f"- 宇宙 {funnel['universe']}；站上MA20 {funnel.get('above_ma20')}；均线堆叠且未伸展 {funnel.get('stack_ok')}。",
        f"- 与价值短名单重叠剔除 {funnel.get('kicked_value_overlap')}；已持/已清剔除 {funnel.get('kicked_held')}。",
        f"- 过排除且流动性够 {funnel.get('after_excludes')} → 短名单 **{len(picked)}**。",
        f"- 价值票禁复述：{sorted(value_codes)}",
        "",
        "## 方法盲点",
        "",
        "- 「站上均线」用未复权 MA5/MA20/MA60，不含周线/筹码。近板用涨停池+5日涨幅阈值，非盘口封单。",
        f"- {held_line()}",
        "",
        "## 短名单（≤5）",
        "",
    ]
    if not picked:
        lines.append("（过门不足，不硬凑）")
        lines.append("")
    for x in picked:
        lines.append("- " + short_line(x, sina, tencent, tech_reason(x) + f"；{align_of(x)}"))
    lines.append("")
    lines.append("相对早盘：早盘无独立技术线，本窗为新增独立席；不把价值票改头换面塞入。")
    lines.append("")
    lines += quote_table(picked, sina, tencent)
    lines.append("扫描≠买卖灯｜教育模拟，非投资建议。")
    lines.append("")
    return "\n".join(lines)


def build_oversold_md(
    picked: list[dict],
    funnel: dict,
    extra: dict,
    sina: dict,
    tencent: dict,
    fetch_meta: dict,
    scored: list[dict],
) -> str:
    fetched_at = now_cn()
    vs = vs_morning_oversold(scored, picked)
    lines = header("晚筛细扫 · 线2b 全A超跌（A硬≥1，满2优先｜建议并乙）", fetched_at)
    lines += [
        "## 口径",
        "",
        "- **A硬 ≥1**（满2优先）：①近20日≤−12% 或 近5日≤−6%；②相对MA20≤−6%；③近60日价格分位≤40%。",
        "- **B软**：PE>0；破净/低PE优先；畸高PE/PB降权；非脉冲阴跌；非ST。",
        "- **C排除**：忌追袖、连板/近板（高度今日6对照）、高开>1%、电力、无量僵尸、已持不占新观察、已清不加回。",
        "- 默认建议进 **乙**。科创观察·不对齐。必须用 11/09 收盘重算，早盘十票仅对照。",
        "",
        "## 覆盖 / 踢出",
        "",
        f"- 扫描 {funnel['universe']}（主板 {funnel['by_board'].get('主板', 0)} / "
        f"创业 {funnel['by_board'].get('创业板', 0)} / 科创 {funnel['by_board'].get('科创板', 0)}）→ "
        f"K线有效 {funnel['kline_ok']} → 过A {funnel['pass_A']} "
        f"（主板 {funnel['pass_A_by_board'].get('主板', 0)} / 创业 {funnel['pass_A_by_board'].get('创业板', 0)} / "
        f"科创 {funnel['pass_A_by_board'].get('科创板', 0)}；满2 {funnel['pass_A2plus']}）→ "
        f"过C {funnel['after_C']} → 价值质量 {funnel['after_B_quality']} → 短名单 **{len(picked)}**。",
        f"- 踢出计数：{funnel.get('kicked')}",
        f"- 忌追袖：油运BK={extra.get('oil_bk')} n={len(extra.get('oil_codes') or [])}；"
        f"光模块用代码+简称兜底（BK1136 过宽，不整组踢出）；"
        f"算力/AI BK={extra.get('ai_bk')} n={len(extra.get('ai_codes') or [])}，仅残续硬追（近板/大涨）才踢。"
        f"今日约半数高开>1%，是相对早盘纠偏主因，不编造低开。",
        "",
        "## 方法盲点",
        "",
        "- 不复权日K；A③单独过门很宽，短名单只从满2条A且过 B/C 的票里按分板/行业配额取 5–10。",
        "- 未全量核验立案/停牌全文。",
        f"- {held_line()}",
        "",
        "## 超跌短名单（建议并乙｜5–10）",
        "",
        "| # | 代码+全称 | 板 | 收盘/涨跌% | A触发 | B软 | 一句理由 | 对齐 |",
        "|---|-----------|----|-----------|------|-----|----------|------|",
    ]
    for i, x in enumerate(picked, 1):
        q = quote_triple(x, sina, tencent)
        pct = f"{q['pct']:+.2f}%" if q["pct"] is not None else "缺失"
        lines.append(
            f"| {i} | `{x['code']} {x['name']}` | {x['board']} | {fmt_num(q['close'])} / {pct} | "
            f"{a_trigger_text(x)} | {b_sentence(x)} | {oversold_reason(x)} | {align_of(x)} |"
        )
    lines.append("")
    lines.append("### 分板")
    lines.append("")
    for b in ("主板", "创业板", "科创板"):
        n = sum(1 for x in picked if x["board"] == b)
        lines.append(f"- {b}：**{n}**")
    lines.append("")
    lines.append("## 相对早盘（11/06 收盘十票，必须用 11/09 重算）")
    lines.append("")
    lines.append("- 维持：" + ("、".join(name_of(scored, c) for c in vs["keep"]) if vs["keep"] else "无"))
    lines.append(
        "- 纠偏换出："
        + (
            "、".join(f"{name_of(scored, c)}（{why_drop_oversold(scored, c)}）" for c in vs["drop"])
            if vs["drop"]
            else "无"
        )
    )
    lines.append("- 新增：" + ("、".join(name_of(scored, c) for c in vs["new"]) if vs["new"] else "无"))
    lines.append(
        "- 双现：`688267 中触媒` 同时在科创价值观察与超跌乙；科创仍不对齐开仓，扫描≠改灯。"
    )
    lines.append("")
    lines += quote_table(picked, sina, tencent)
    lines.append("扫描≠买卖灯｜建议默认进乙｜教育模拟，非投资建议。")
    lines.append("")
    return "\n".join(lines)


def build_digest(
    value_picked: dict[str, list[dict]],
    tech_picked: list[dict],
    oversold_picked: list[dict],
    value_funnel: dict,
    tech_funnel: dict,
    oversold_funnel: dict,
    medians: dict,
    sina: dict,
    tencent: dict,
    scored: list[dict],
    fetch_meta: dict,
) -> str:
    fetched_at = now_cn()
    vs_o = vs_morning_oversold(scored, oversold_picked)
    vs_v = vs_morning_value(value_picked)
    lines = header("晚筛细扫摘要（交投资席｜三线一页）", fetched_at)
    lines += [
        "**扫描 ≠ 买卖灯 ≠ 下单 ≠ 改灯。** 不下真单、不连券商。科创一律观察·不对齐；创业可对齐。超跌默认并乙。",
        "",
        f"覆盖：宇宙 {oversold_funnel['universe']}｜K线有效 {oversold_funnel['kline_ok']}｜"
        f"空K {fetch_meta.get('empty_kline')} "
        + ("、".join(f"`{c} {n}`" for c, n in (fetch_meta.get("empty_names") or [])) or "")
        + f"｜涨停高度今日 {fetch_meta.get('zt_height')}｜"
        f"高开>1%踢出约 { (oversold_funnel.get('kicked') or {}).get('高开>1%', 0) }（今日宽基高开，纠偏早盘）。",
        "",
        "## 线1 价值分板",
        "",
    ]
    for b in ("主板", "创业板", "科创板"):
        arr = value_picked.get(b) or []
        lines.append(f"### {b}（{len(arr)}/5）")
        if not arr:
            lines.append("- （过门不足）")
        for x in arr:
            lines.append("- " + short_line(x, sina, tencent, value_reason(x, medians)))
        v = vs_v.get(b) or {}
        lines.append(
            f"相对早盘：维持 {len(v.get('keep') or [])} / 新增 {len(v.get('new') or [])} / 纠偏 {len(v.get('drop') or [])}"
        )
        lines.append("")
    lines += [
        f"价值漏斗：门 {value_funnel.get('pass_gate')} → 过C {value_funnel.get('pass_c_and_gap')}。"
        "早盘价值旁注挂在超跌漏斗下，本窗改独立破净/相对低估门，维持少是口径切换。",
        "",
        "## 线2 技术独立",
        "",
    ]
    if not tech_picked:
        lines.append("- （过门不足）")
    for x in tech_picked:
        lines.append("- " + short_line(x, sina, tencent, tech_reason(x) + f"；{align_of(x)}"))
    lines += [
        "",
        f"技术漏斗：站上MA20 {tech_funnel.get('above_ma20')} → 堆叠未伸展 {tech_funnel.get('stack_ok')} → "
        f"过排除 {tech_funnel.get('after_excludes')} → {len(tech_picked)}。"
        f"价值代码重叠剔除 {tech_funnel.get('kicked_value_overlap')}；价值同业剔除 {tech_funnel.get('kicked_value_industry')}。",
        "",
        "## 线2b 全A超跌（并乙）",
        "",
    ]
    for x in oversold_picked:
        lines.append(
            "- "
            + short_line(x, sina, tencent, a_trigger_text(x) + "｜" + oversold_reason(x) + f"；{align_of(x)}")
        )
    lines += [
        "",
        f"超跌漏斗：过A {oversold_funnel.get('pass_A')}（满2 {oversold_funnel.get('pass_A2plus')}）→ "
        f"过C {oversold_funnel.get('after_C')} → 质量 {oversold_funnel.get('after_B_quality')} → {len(oversold_picked)}。",
        "- 相对早盘维持："
        + ("、".join(name_of(scored, c) for c in vs_o["keep"]) if vs_o["keep"] else "无"),
        "- 相对早盘纠偏："
        + ("、".join(name_of(scored, c) for c in vs_o["drop"]) if vs_o["drop"] else "无"),
        "- 相对早盘新增："
        + ("、".join(name_of(scored, c) for c in vs_o["new"]) if vs_o["new"] else "无"),
        "- `688267 中触媒` 价值观察与超跌乙双现；科创不对齐，不改灯。",
        "",
        "## 持仓对照（不占新观察）",
        "",
        held_line(),
        "",
        "新闻线本席不做。扫描≠买卖灯｜教育模拟，非投资建议。",
        "",
    ]
    return "\n".join(lines)


def slim_row(x: dict, sina: dict, tencent: dict, extra_reason: str) -> dict:
    q = quote_triple(x, sina, tencent)
    m = x["metrics"]
    return {
        "code": x["code"],
        "name": x["name"],
        "board": x["board"],
        "close": q["close"],
        "pct": q["pct"],
        "open": q["open"],
        "gap_pct": x.get("gap_pct"),
        "pe": x.get("pe"),
        "pb": x.get("pb"),
        "industry": x.get("industry"),
        "a_hits": x.get("a_hits"),
        "ret_5d": m.get("ret_5d"),
        "ret_20d": m.get("ret_20d"),
        "dev_ma20": m.get("dev_ma20"),
        "pctile_60d": m.get("pctile_60d"),
        "align": align_of(x),
        "reason": extra_reason,
        "sina_close": q["sina"],
        "tencent_close": q["tencent"],
        "eastmoney_close": q["eastmoney"],
        "k_asof": m.get("k_asof"),
    }
