#!/usr/bin/env python3
"""2026-11-13 盘前 A 组装配器：只读复用 a_share_monitor.oversold_scan，不改业务脚本。

窗口 2026-11-13 周五盘前 Asia/Shanghai；price_asof=2026-11-12 收盘。
教育模拟｜扫描≠买卖灯｜不要写买入××股。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import a_share_monitor.oversold_scan as oscan
from a_share_monitor.markets import align_label, board_label, classify_board

WINDOW_DATE = "2026-11-13"
WINDOW_LABEL = "2026-11-13 周五盘前"
ASOF = "2026-11-12"
SCAN_STAMP = "20261113"
PAPER_RULES = "v3.9.2.71"
PAPER_SHA256 = "5abb9ad2814481401a781ec63bd1c2c8a01b37b9a8641865ad8184b675c2557e"
PAPER_SHA8 = "5abb9ad2"
EVENING_AGENT = "bc-67d7fb60"
EVENING_FETCH = "2026-11-12 17:31:49"
LIMITED_FETCH = "2026-11-13 08:18:21"

HELD_PAPER = {
    "601318": "中国平安",
    "000429": "粤高速A",
    "601088": "中国神华",
    "300926": "博俊科技",
    "603806": "福斯特",
}
HELD_GOLD = {
    "603806": "福斯特",
    "000429": "粤高速A",
    "300611": "美力科技",
    "601318": "中国平安",
    "601088": "中国神华",
    "601001": "晋控煤业",
    "300258": "精锻科技",
}
HELD_ANY = {**HELD_PAPER, **HELD_GOLD}
CLEARED = {
    "300059": "东方财富",
    "000333": "美的集团",
    "601006": "大秦铁路",
    "601166": "兴业银行",
}
FALSE_STABLE = {"002415": "海康威视"}
NAMED_KEEP_WATCH = {
    "600567": "山鹰国际",
    "600546": "山煤国际",
    "600938": "中国海油",
    "301563": "云汉芯城",
    "300839": "博汇股份",
    "688613": "奥精医疗",
    "688519": "南亚新材",
    "301282": "金禄电子",
    "603707": "健友股份",
    "603259": "药明康德",
}

EVENING_TEN = [
    "002772",
    "600668",
    "603833",
    "002734",
    "002215",
    "300756",
    "300970",
    "301345",
    "688136",
    "688015",
]
EVENING_TEN_LABELS = {
    "002772": "众兴菌业",
    "600668": "尖峰集团",
    "603833": "欧派家居",
    "002734": "利民股份",
    "002215": "诺普信",
    "300756": "金马游乐",
    "300970": "华绿生物",
    "301345": "涛涛车业",
    "688136": "科兴制药（科创不对齐）",
    "688015": "交控科技（科创不对齐）",
}
LIMITED_NINE = [
    "603833",
    "002541",
    "603995",
    "000893",
    "301219",
    "301345",
    "300483",
    "688308",
    "688117",
]
LIMITED_LABELS = {
    "603833": "欧派家居",
    "002541": "鸿路钢构",
    "603995": "甬金股份",
    "000893": "亚钾国际",
    "301219": "腾远钴业",
    "301345": "涛涛车业",
    "300483": "首华燃气",
    "688308": "欧科亿（科创不对齐）",
    "688117": "圣诺生物（科创不对齐）",
}
EVENING_LOWLAND = {
    "main": ["601186", "601390", "600016", "000932", "600104"],
    "chinext": ["300388", "300349", "301039", "300664", "300729"],
    "star": ["688330", "688101", "688186", "688819", "688606"],
}
EVENING_LOWLAND_LABELS = {
    "601186": "中国铁建",
    "601390": "中国中铁",
    "600016": "民生银行",
    "000932": "华菱钢铁",
    "600104": "上汽集团",
    "300388": "节能国祯",
    "300349": "金卡智能",
    "301039": "中集车辆",
    "300664": "鹏鹞环保",
    "300729": "乐歌股份",
    "688330": "宏力达",
    "688101": "三达膜",
    "688186": "广大特材",
    "688819": "天能股份",
    "688606": "奥泰生物",
}
LOWLAND_REVIEW_CODES = [
    "601818",  # 光大银行
    "600000",  # 浦发银行
    "601668",  # 中国建筑
    "601601",  # 中国太保
    "300428",  # 立中集团
    "300146",  # 汤臣倍健
    "301216",  # 万凯新材
    "300181",  # 佐力药业
    "688009",  # 中国通号
    "688128",  # 中国电研
    "688187",  # 时代电气
    "688016",  # 心脉医疗
]
COAL_NAME_KEYS = ("煤业", "煤矿", "焦煤", "动力煤", "神华", "中煤能源", "潞安", "兖矿")
PUBLIC_HALT_HINTS = {
    "600185": {
        "name": "珠免集团",
        "evidence": "巨潮公告1225667574：筹划重大资产重组，2026-11-12开市起停牌；新浪股海导航/上证报同日交叉",
    },
    "000831": {
        "name": "中国稀土",
        "evidence": "公开日历：继续停牌（起始2026-11-02），拟筹划重大资产重组；第一财经11/12七只停牌点名",
    },
    "002129": {
        "name": "TCL中环",
        "evidence": "公开日历：继续停牌（起始2026-11-02），拟筹划重大资产重组",
    },
    "002717": {
        "name": "*ST岭南",
        "evidence": "公开日历：继续停牌（起始2026-10-13），刊登重要公告",
    },
    "688121": {
        "name": "*ST卓然",
        "evidence": "公开日历：继续停牌（起始2026-10-29），刊登重要公告",
    },
    "688496": {
        "name": "*ST清越",
        "evidence": "公开日历：继续停牌（起始2026-09-11），刊登重要公告",
    },
    "688798": {
        "name": "艾为电子",
        "evidence": "公开日历：继续停牌（起始2026-11-10），拟筹划重大资产重组；第一财经11/12七只停牌点名",
    },
}


def apply_window_globals() -> None:
    oscan.ASOF_DEFAULT = ASOF
    oscan.WINDOW_DATE = WINDOW_DATE
    oscan.WINDOW_LABEL = WINDOW_LABEL
    oscan.SCAN_STAMP = SCAN_STAMP
    oscan.HELD = dict(HELD_ANY)
    oscan.CLEARED = dict(CLEARED)
    oscan.EVENING_TEN = list(EVENING_TEN)
    oscan.EVENING_TEN_LABELS = dict(EVENING_TEN_LABELS)
    oscan.SECONDARY_TEN = list(LIMITED_NINE)
    oscan.SECONDARY_TEN_LABELS = dict(LIMITED_LABELS)
    oscan.NAMED_NOT_FORCE = set(NAMED_KEEP_WATCH)
    extra = dict(oscan.EXTRA_NOTES)
    extra.update(
        {
            "603806": "11/12收12.51已触硬失效12.61，卖出建议已交用户、尚未入账，不是本扫卖令；纸面仍记600，真金23000为当日误买且两账隔离；勿再满开主推",
            "300926": "纸面仍持700；真金已清0，两账隔离，不要把纸面写成已清",
            "300611": "真金已持1300，不占新观察",
            "300258": "真金已持200，不占新观察",
            "601001": "真金已持600（可用0）；已在甲，不降乙；与神华同属煤炭链，超跌可观察，不作煤炭净新主推",
            "601088": "纸面+真金已持；忌叠力·禁再开电力",
            "601318": "纸面+真金已持，不占新观察",
            "000429": "纸面+真金已持，收购包只跟踪不加仓，不占新观察",
            "603259": "用户点名保留观察，点名≠建议买入",
            "002415": "伪稳不升进攻",
            "688308": "本窗TTM PE独立重算过价值门则允许入科创观察席；不得沿用晚筛「PE偏高」而不重算；观察·不对齐本账户开仓",
        }
    )
    oscan.EXTRA_NOTES = extra


def clean_name(name: str) -> str:
    return "".join((name or "").split())


def is_coal(code: str, name: str, industry: str) -> bool:
    if "煤炭" in (industry or ""):
        return True
    return any(k in (name or "") for k in COAL_NAME_KEYS)


def is_broker_row(row: dict[str, Any]) -> bool:
    if row.get("is_broker"):
        return True
    blob = (row.get("industry") or "") + (row.get("name") or "")
    return any(k in blob for k in ("证券", "券商", "中金公司", "中金"))


def still_lowland(row: dict[str, Any]) -> tuple[bool, str]:
    """现价是否仍足够低。小幅反弹可保留；已回均线附近或回撤已浅则否。"""
    dev = row.get("dev_ma20")
    pctile = row.get("pctile_60d")
    r20 = row.get("ret_20d")
    if dev is None and pctile is None:
        return False, "缺K无法判断是否仍低"
    if dev is not None and dev >= -0.005:
        return False, "已回均线附近"
    near_ma = dev is not None and dev >= -0.02
    shallow = (r20 is not None and r20 > -0.05) and (pctile is not None and pctile > 45)
    high_zone = pctile is not None and pctile >= 55
    if near_ma and (high_zone or shallow or (pctile is not None and pctile > 40)):
        return False, "已回均线附近"
    if shallow and (dev is None or dev > -0.04):
        return False, "回撤已浅"
    if high_zone and (dev is None or dev > -0.03):
        return False, "60日分位已偏高、不再足够低"
    return True, "现价仍处低地"


def lowland_rank(row: dict[str, Any]) -> tuple:
    pe = row.get("pe")
    pb = row.get("pb")
    pctile = row.get("pctile_60d") if row.get("pctile_60d") is not None else 99.0
    dev = row.get("dev_ma20") if row.get("dev_ma20") is not None else 0.0
    pe_key = pe if (pe is not None and pe > 0) else 999.0
    pb_key = pb if (pb is not None and pb > 0) else 999.0
    return (pb_key, pe_key, pctile, dev)


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def compact_row(r: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "code",
        "name",
        "board",
        "close",
        "chg_pct",
        "pe",
        "pb",
        "pe_src",
        "turnover",
        "amount",
        "industry",
        "ret_5d",
        "ret_20d",
        "dev_ma20",
        "pctile_60d",
        "gap_asof",
        "amt20",
        "a_hits",
        "c_reasons",
        "pulse",
        "near_board_k",
        "limit_streak",
        "dist_to_limit",
        "sleeve_oil",
        "sleeve_opt",
        "too_high",
        "near_limit",
        "is_power",
        "is_bank",
        "is_broker",
        "is_pv",
        "is_coal",
        "value_ok",
        "b_note",
        "score",
        "gap_asof_gt1",
        "k_len",
        "k_end",
        "k_status",
        "missing_reason",
        "halt_status",
        "halt_evidence",
        "retryable",
        "drop_why",
        "align",
        "extra_note",
        "lowland_ok",
        "lowland_why",
        "lowland_source_only",
        "financial_note",
    ]
    out = {k: r.get(k) for k in keep if k in r or True}
    return out


def fetch_halt_pool(cache_path: Path) -> dict[str, dict[str, str]]:
    """尽力取公开停牌池；失败不编造。"""
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    out = {k: dict(v) for k, v in PUBLIC_HALT_HINTS.items()}
    oscan.log(f"[halt] public evidence n={len(out)}; skip eastmoney halt clist (502)")
    dump_json(cache_path, out)
    return out


def fetch_kline_sina(code: str) -> list[dict[str, float | str]]:
    """新浪不复权日K回退。腾讯 501 / 东财 502 时补缺口。"""
    import time as _time

    sym = oscan.sina_symbol(code)
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    params = {"symbol": sym, "scale": 240, "ma": "no", "datalen": 90}
    last_err: Exception | str = "unknown"
    sess = oscan._session()
    for i in range(4):
        try:
            r = sess.get(
                url,
                params=params,
                timeout=15,
                headers={"Referer": "https://finance.sina.com.cn", "User-Agent": oscan.UA},
            )
            if r.status_code == 200 and r.text.lstrip().startswith("["):
                data = json.loads(r.text)
                rows: list[dict[str, float | str]] = []
                prev = None
                for bar in data:
                    close = float(bar["close"])
                    vol = float(bar.get("volume") or 0)
                    pct = ((close / prev - 1.0) * 100.0) if prev else 0.0
                    rows.append(
                        {
                            "date": str(bar.get("day") or bar.get("date") or "")[:10],
                            "open": float(bar["open"]),
                            "close": close,
                            "high": float(bar["high"]),
                            "low": float(bar["low"]),
                            "vol": vol,
                            "amt": vol * close,
                            "pct": pct,
                        }
                    )
                    prev = close
                rows = [r0 for r0 in rows if str(r0["date"]) <= ASOF]
                if rows:
                    return rows
                last_err = "empty after asof filter"
            else:
                last_err = f"http {r.status_code} {r.text[:120]}"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        _time.sleep(0.25 * (i + 1))
    raise RuntimeError(f"sina kline {code} failed: {last_err}")


def load_or_fetch_klines(codes: list[str], cache_dir: Path, workers: int) -> dict[str, list[dict[str, Any]]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    stale = 0
    for code in codes:
        fp = cache_dir / f"{code}.json"
        if not fp.exists():
            missing.append(code)
            continue
        try:
            rows = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            missing.append(code)
            continue
        if not isinstance(rows, list) or not rows:
            missing.append(code)
            continue
        rows = [r for r in rows if str(r.get("date", "")) <= ASOF]
        if rows and str(rows[-1].get("date")) == ASOF:
            out[code] = rows
        else:
            stale += 1
            try:
                fp.unlink()
            except OSError:
                pass
            missing.append(code)
    oscan.log(f"[kline] cached_ok={len(out)} stale_or_missing={len(missing)} stale_seen={stale}")
    if not missing:
        return out

    def _job(code: str) -> tuple[str, list[dict[str, Any]] | None, str]:
        last_err = ""
        for fetcher, tag in (
            (fetch_kline_sina, "sina"),
            (oscan.fetch_kline_tencent, "tencent"),
            (oscan.fetch_kline, "em"),
        ):
            try:
                rows = fetcher(code)
                rows = [r for r in rows if str(r.get("date", "")) <= ASOF]
                if rows:
                    (cache_dir / f"{code}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
                    return code, rows, tag
            except Exception as exc:  # noqa: BLE001
                last_err = f"{last_err}; {tag}={exc}"
        return code, None, last_err or "all kline sources failed"

    fail = 0
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_job, c) for c in missing]
        for fut in as_completed(futs):
            code, rows, err = fut.result()
            done += 1
            if rows:
                out[code] = rows
            else:
                fail += 1
                if fail <= 12:
                    oscan.log(f"[kline-fail] {code} {err}")
            if done % 200 == 0 or done == len(missing):
                oscan.log(f"[kline] progress {done}/{len(missing)} ok={len(out)} fail={fail}")
    return out


def retry_empty_klines(
    codes: list[str],
    klines: dict[str, list[dict[str, Any]]],
    cache_dir: Path,
) -> None:
    retry = []
    for code in codes:
        rows = klines.get(code) or []
        rows = [r for r in rows if str(r.get("date", "")) <= ASOF]
        if not rows or str(rows[-1].get("date")) != ASOF:
            retry.append(code)
    oscan.log(f"[kline-retry] n={len(retry)}")
    for code in retry:
        rows = None
        for fetcher, tag in (
            (fetch_kline_sina, "sina"),
            (oscan.fetch_kline_tencent, "tencent"),
            (oscan.fetch_kline, "em"),
        ):
            try:
                rows = fetcher(code)
                if rows:
                    break
            except Exception as exc:  # noqa: BLE001
                oscan.log(f"[kline-retry-{tag}] {code} {exc}")
                rows = None
        rows = [r for r in (rows or []) if str(r.get("date", "")) <= ASOF]
        if rows:
            (cache_dir / f"{code}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            klines[code] = rows


def compute_rows(
    clist: list[dict[str, Any]],
    klines: dict[str, list[dict[str, Any]]],
    tencent_fund: dict[str, dict[str, Any]],
    oil_codes: set[str],
    power_codes: set[str],
    zt_asof: dict[str, Any],
    lianban_codes: set[str],
    near_codes: set[str],
    halt_map: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], Counter]:
    kick: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for item in clist:
        code = str(item["f12"])
        name = str(item.get("f14") or "")
        board = classify_board(code) or ""
        close = oscan._fnum(item.get("f2"))
        chg = oscan._fnum(item.get("f3"))
        pe = oscan._fnum(item.get("f115"))
        if pe is None or pe <= 0:
            pe = oscan._fnum(item.get("f9"))
        pb = oscan._fnum(item.get("f23"))
        tf = tencent_fund.get(code) or {}
        if tf.get("pe_ttm") is not None:
            pe = tf["pe_ttm"]
        if tf.get("pb") is not None:
            pb = tf["pb"]
        rec_pe_src = "tencent_ttm" if tf.get("pe_ttm") is not None else "sina_static"
        turnover = oscan._fnum(item.get("f8"))
        amount = oscan._fnum(item.get("f6"))
        industry = oscan.industry_of(item)
        bars = klines.get(code)
        rec: dict[str, Any] = {
            "code": code,
            "name": clean_name(name),
            "board": board,
            "close": close,
            "chg_pct": chg,
            "pe": pe,
            "pb": pb,
            "pe_src": rec_pe_src,
            "turnover": turnover,
            "amount": amount,
            "industry": industry,
            "a_hits": [],
            "c_reasons": [],
            "k_len": len(bars or []),
            "k_end": str((bars or [{}])[-1].get("date") or "") if bars else "",
            "k_status": "ok",
            "missing_reason": "",
            "halt_status": "",
            "halt_evidence": "",
            "retryable": False,
            "align": align_label(board) if board else "",
        }
        if oscan.is_st(name):
            rec["c_reasons"].append("ST")
            kick["ST"] += 1
        if oscan.is_delist(name):
            rec["c_reasons"].append("退市整理")
            kick["退市整理"] += 1
        if close is None:
            rec["k_status"] = "no_close"
            if code in halt_map:
                rec["halt_status"] = "HALT"
                rec["halt_evidence"] = halt_map[code].get("evidence") or "公开停牌名单"
                rec["missing_reason"] = f"无{ASOF}收盘价；公开停牌：{rec['halt_evidence']}"
                rec["c_reasons"].append("停牌")
                kick["停牌"] += 1
            elif not oscan.is_st(name) and not oscan.is_delist(name):
                rec["halt_status"] = "UNKNOWN"
                rec["missing_reason"] = f"无{ASOF}收盘价；停牌原因UNKNOWN，不编造停牌"
                rec["c_reasons"].append("停牌或无价")
                rec["retryable"] = True
                kick["停牌或无价"] += 1
            else:
                rec["halt_status"] = "UNKNOWN"
                rec["missing_reason"] = f"ST/退市整理且无{ASOF}收盘价"
            rows.append(rec)
            continue
        if not bars or len(bars) < 21 or str(bars[-1].get("date")) != ASOF:
            rec["k_status"] = "k_missing"
            k_end = rec.get("k_end") or ""
            k_len = len(bars or [])
            if code in halt_map:
                rec["halt_status"] = "HALT"
                rec["halt_evidence"] = halt_map[code].get("evidence") or "公开停牌名单"
                rec["missing_reason"] = (
                    f"K末日={k_end or 'NA'} k_len={k_len}；公开停牌：{rec['halt_evidence']}"
                )
                rec["retryable"] = False
                rec["c_reasons"].append("停牌")
                kick["停牌"] += 1
            elif k_end == ASOF and k_len < 21:
                rec["halt_status"] = "UNKNOWN"
                rec["missing_reason"] = f"次新/样本不足：K末日={ASOF} 但 k_len={k_len}<21，不够算A硬；不编造停牌"
                rec["retryable"] = False
                rec["c_reasons"].append("K线空")
                kick["K线空"] += 1
            else:
                rec["halt_status"] = "UNKNOWN"
                rec["retryable"] = True
                rec["missing_reason"] = (
                    f"K线不足或K末日≠{ASOF}；k_len={k_len} k_end={k_end or 'NA'}；停牌原因UNKNOWN，不编造停牌"
                )
                rec["c_reasons"].append("K线空")
                kick["K线空"] += 1
            rows.append(rec)
            continue
        m = oscan.a_metrics(bars)
        if not m:
            rec["k_status"] = "k_metrics_fail"
            rec["missing_reason"] = "K线有棒但指标不足21根或收盘非法"
            rec["halt_status"] = "UNKNOWN"
            rec["retryable"] = True
            rec["c_reasons"].append("K线空")
            kick["K线空"] += 1
            rows.append(rec)
            continue
        rec.update(
            {
                "close": m["close"],
                "chg_pct": m["pct_asof"],
                "ret_5d": m["ret_5d"],
                "ret_20d": m["ret_20d"],
                "dev_ma20": m["dev_ma20"],
                "pctile_60d": m["pctile_60d"],
                "gap_asof": m["gap_asof"],
                "amt20": m["amt20"],
            }
        )
        hits = oscan.detect_a_hits(m)
        rec["a_hits"] = hits
        flags = oscan.kline_limit_flags(code, name, bars, lookback=5)
        rec["pulse"] = flags["pulse"]
        rec["near_board_k"] = flags["near_board"]
        rec["limit_streak"] = flags["limit_streak"]
        rec["dist_to_limit"] = oscan.dist_to_limit_pct(m["close"], m.get("prev_close"), code, name)
        rec["sleeve_oil"] = code in oil_codes
        rec["sleeve_opt"] = oscan.is_opt_mod(code, name) or code in oscan.NAMED_OPT_CHASE
        rec["too_high"] = oscan.too_high(m)
        rec["near_limit"] = oscan.near_limit_asof(m["pct_asof"], code, name)
        if code in zt_asof:
            rec["c_reasons"].append("涨停池残续")
            kick["涨停池残续"] += 1
        if code in lianban_codes or flags["limit_streak"] >= 2:
            rec["c_reasons"].append("连板")
            kick["连板"] += 1
        if oscan.is_limit_up(m["pct_asof"], code, name):
            rec["c_reasons"].append("涨停")
            kick["涨停"] += 1
        elif rec["near_limit"] or flags["near_board"] or code in near_codes:
            rec["c_reasons"].append("近板忌追")
            kick["近板忌追"] += 1
        if hits and rec["too_high"]:
            rec["c_reasons"].append("已相对高忌追")
            kick["已相对高忌追"] += 1
        if code in oscan.NAMED_OPT_CHASE and m["pct_asof"] >= 5.0 and "涨停" not in rec["c_reasons"]:
            rec["c_reasons"].append("点名大涨忌追")
            kick["点名大涨忌追"] += 1
        amt20 = m["amt20"]
        if (turnover is not None and turnover < 0.15 and (amount or 0) < 8_000_000) or amt20 < 3_000_000:
            rec["c_reasons"].append("无量僵尸")
            kick["无量僵尸"] += 1
        rec["is_power"] = oscan.is_power(code, name, industry, power_codes)
        rec["is_bank"] = oscan.is_bank(industry, name)
        rec["is_broker"] = oscan.is_broker(industry, name)
        rec["is_pv"] = oscan.is_pv(industry, name)
        rec["is_coal"] = is_coal(code, name, industry)
        rec["value_ok"] = oscan.value_ok(pe, pb, close=rec.get("close"), name=name)
        rec["b_note"] = oscan.b_note(pe, pb, rec.get("pulse") or False)
        rec["score"] = oscan.score_row(rec)
        rec["gap_asof_gt1"] = (m["gap_asof"] or 0) > 0.01
        if rec["is_power"]:
            kick["电力"] += 1
        if pe is None:
            rec["financial_note"] = "PE缺失待补"
        elif pe <= 0:
            rec["financial_note"] = "PE≤0财务风险待补"
        else:
            rec["financial_note"] = ""
        still, still_why = still_lowland(rec)
        rec["lowland_still"] = still
        rec["lowland_still_why"] = still_why
        rows.append(rec)
    return rows, kick


def annotate_drop_why(rows: list[dict[str, Any]]) -> None:
    watch = set(EVENING_TEN) | set(LIMITED_NINE) | set(LOWLAND_REVIEW_CODES)
    for board_codes in EVENING_LOWLAND.values():
        watch |= set(board_codes)
    watch |= {"688308", "601699", "000520", "601001", "300611", "300258", "603806"}
    for r in rows:
        if r["code"] not in watch:
            continue
        if r.get("is_power"):
            r["drop_why"] = "电力（发电禁再开，不是煤炭/油整组）"
        elif r["c_reasons"]:
            r["drop_why"] = ",".join(r["c_reasons"])
        elif not r.get("value_ok"):
            r["drop_why"] = "价值质量未过（PE/PB）"
        elif "②" not in (r.get("a_hits") or []) and len(r.get("a_hits") or []) < 3:
            r["drop_why"] = (
                f"仅{''.join(r.get('a_hits') or [])}（②未过，MA20={oscan.fmt_pct(r.get('dev_ma20'))}），不改②定义保席"
            )
        elif len(r.get("a_hits") or []) < 2:
            r["drop_why"] = f"A={''.join(r.get('a_hits') or []) or '无'}"
        elif r["code"] in HELD_ANY:
            r["drop_why"] = "已持不占新观察"
        elif r.get("is_coal"):
            r["drop_why"] = "煤炭链可观察，不作煤炭净新主推"
        else:
            extra = oscan.EXTRA_NOTES.get(r["code"], "")
            r["drop_why"] = "满A且过B/C，分板/行业配额或价值排序未进前10" + (f"；{extra}" if extra else "")


def pick_oversold(cands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pool = [
        r
        for r in cands
        if len(r.get("a_hits") or []) >= 2
        and r.get("value_ok")
        and ("①" in r["a_hits"] or "②" in r["a_hits"])
        and not r.get("c_reasons")
        and not r.get("is_power")
    ]
    pool.sort(key=lambda r: (-len(r["a_hits"]), -(r.get("score") or 0), r.get("pctile_60d") or 99))
    picked: list[dict[str, Any]] = []
    used_ind: set[str] = set()
    board_cap = {"main": 5, "chinext": 3, "star": 2}
    board_n: Counter[str] = Counter()
    bank_n = 0
    for row in pool:
        if len(picked) >= 10:
            break
        code = row["code"]
        if code in HELD_ANY or code in CLEARED or code in oscan.WATCH_ONLY:
            continue
        if code in oscan.OIL_WATCHED or code in oscan.OIL_LOW_REVIEW or code in FALSE_STABLE:
            continue
        if code in NAMED_KEEP_WATCH:
            continue
        if code == "603707":
            continue
        if oscan.is_delist(row.get("name") or "") or oscan.is_st(row.get("name") or ""):
            continue
        if (row.get("close") or 0) < 1.0:
            continue
        if is_broker_row(row):
            continue
        if row.get("is_coal"):
            continue
        board = row["board"]
        if board_n[board] >= board_cap.get(board, 2):
            continue
        ind = row.get("industry") or row["code"]
        if ind in used_ind:
            continue
        if row.get("is_bank"):
            continue
        row = dict(row)
        row["align"] = align_label(board) if board != "main" else "主板"
        extra = oscan.EXTRA_NOTES.get(code)
        if extra:
            row["extra_note"] = extra
        picked.append(row)
        used_ind.add(ind)
        board_n[board] += 1
        if row.get("is_bank"):
            bank_n += 1
    if len(picked) < 5:
        for row in pool:
            if len(picked) >= 5:
                break
            if any(x["code"] == row["code"] for x in picked):
                continue
            if row["code"] in HELD_ANY or row["code"] in CLEARED or row.get("is_power") or row.get("c_reasons"):
                continue
            if is_broker_row(row) or row.get("is_coal"):
                continue
            board = row["board"]
            if board_n[board] >= board_cap.get(board, 2):
                continue
            row = dict(row)
            row["align"] = align_label(board)
            picked.append(row)
            board_n[board] += 1
    return picked


def classify_lowland_gate(row: dict[str, Any]) -> tuple[bool, bool, str]:
    """return ok_shortlist, source_only, why"""
    if oscan.is_st(row.get("name") or "") or oscan.is_delist(row.get("name") or ""):
        return False, False, "ST/退市整理"
    if row.get("close") is None:
        return False, False, "无收盘价"
    if (row.get("close") or 0) < 1:
        return False, False, "现价<1不进短名单"
    if row.get("c_reasons") and any(x in row["c_reasons"] for x in ("涨停", "连板", "近板忌追", "已相对高忌追")):
        return False, True, "C近板/过高，源候选保留、短名单不进"
    pe, pb = row.get("pe"), row.get("pb")
    still, still_why = still_lowland(row)
    if not still:
        return False, False, still_why
    if pe is not None and pe > 40:
        return False, False, f"PE={pe:.0f}畸高出门"
    board = row.get("board")
    if board == "main":
        if pb is None or pb <= 0:
            return False, True, "主板PB缺失待补"
        if pb >= 1.0:
            return False, False, "未破净"
        if pe is not None and pe <= 0:
            return False, True, "破净但PE≤0财务风险待补"
        return True, True, "破净且仍低"
    # 创业/科创：相对低估放宽，不用主板破净硬套；高PB成长票不算低地短名单
    if pe is None and pb is None:
        return False, True, "PE/PB均缺待补"
    if pe is not None and pe <= 0:
        return False, True, "PE≤0财务风险待补"
    if pe is not None and pe > 32:
        return False, False, f"PE={pe:.0f}畸高出门"
    if pb is None or pb <= 0:
        return False, True, "PB缺失待补"
    if pb > 1.2:
        return False, True, "相对低估未够（PB>1.2），仍低可观察不占短名单"
    if pe is None:
        return False, True, "PE缺失待补"
    return True, True, "相对低估且仍低"


def pick_lowland(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    source: dict[str, list[dict[str, Any]]] = {"main": [], "chinext": [], "star": []}
    for r in rows:
        ok, src, why = classify_lowland_gate(r)
        r["lowland_ok"] = ok
        r["lowland_source_only"] = src and not ok
        r["lowland_why"] = why
        if not (ok or (src and why not in {"未破净", "相对估值未够低", "已回均线附近", "回撤已浅", "60日分位已偏高、不再足够低"})):
            if src:
                board = r.get("board")
                if board in source:
                    source[board].append(r)
            continue
        board = r.get("board")
        if board in source and (ok or src):
            source[board].append(r)

    out: dict[str, list[dict[str, Any]]] = {"main": [], "chinext": [], "star": []}
    for board in ("main", "chinext", "star"):
        pool = []
        for r in source[board]:
            ok, src, why = classify_lowland_gate(r)
            if not ok:
                continue
            if r["code"] in HELD_ANY or r["code"] in CLEARED or r["code"] in FALSE_STABLE:
                continue
            if r.get("is_power") or is_broker_row(r) or r.get("is_coal"):
                continue
            if oscan.is_st(r.get("name") or ""):
                continue
            pool.append(r)
        pool.sort(key=lowland_rank)
        bank_kept = 0
        used_ind: set[str] = set()
        for r in pool:
            if len(out[board]) >= 5:
                break
            if r.get("is_bank"):
                if board != "main" or bank_kept >= 1:
                    continue
                row = dict(r)
                row["align"] = "仅对照·勿堆第二银行强制席"
                row["extra_note"] = "银行仅对照，不占进攻席"
                out[board].append(row)
                bank_kept += 1
                continue
            ind = r.get("industry") or r["code"]
            if ind in used_ind:
                continue
            row = dict(r)
            row["align"] = "主板" if board == "main" else align_label(board)
            out[board].append(row)
            used_ind.add(ind)
        if len(out[board]) < 5:
            for r in pool:
                if len(out[board]) >= 5:
                    break
                if any(x["code"] == r["code"] for x in out[board]):
                    continue
                if r.get("is_bank"):
                    continue
                row = dict(r)
                row["align"] = "主板" if board == "main" else align_label(board)
                out[board].append(row)
    return out


def quotes_asof(q: dict[str, Any], close: float | None) -> dict[str, Any]:
    """盘前：现价可能仍是 11/12 收盘，昨收可能是 11/11。取与 asof 收盘匹配的字段。"""
    sina_close, sina_prev = q.get("sina_close"), q.get("sina_prev")
    tenc_close, tenc_prev = q.get("tencent_close"), q.get("tencent_prev")

    def pick(a, b):
        if close is None:
            return a, "none"
        if a is not None and abs(a - close) <= 0.011:
            return a, "last"
        if b is not None and abs(b - close) <= 0.011:
            return b, "prev"
        return a, "unmatched"

    sina_px, sina_field = pick(sina_close, sina_prev)
    tenc_px, tenc_field = pick(tenc_close, tenc_prev)
    agree = "缺失"
    if close is not None and sina_px is not None and tenc_px is not None:
        if abs(sina_px - close) <= 0.011 and abs(tenc_px - close) <= 0.011:
            agree = f"11/12收盘三源一致（新浪用{sina_field}，腾讯用{tenc_field}；盘前现价可能=asof）"
        else:
            agree = "11/12收盘不一致"
    return {
        "sina_asof": sina_px,
        "tencent_asof": tenc_px,
        "sina_field": sina_field,
        "tencent_field": tenc_field,
        "sina_close": sina_close,
        "sina_prev": sina_prev,
        "tencent_close": tenc_close,
        "tencent_prev": tenc_prev,
        "agree": agree,
    }


def chase_fact(row: dict[str, Any]) -> str:
    close = row.get("close")
    chg = row.get("chg_pct")
    dist = row.get("dist_to_limit")
    gap = row.get("gap_asof")
    close_s = f"{close:.2f}" if isinstance(close, (int, float)) else "NA"
    chg_s = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "NA"
    dist_s = f"{dist:.2f}%" if isinstance(dist, (int, float)) else "NA"
    gap_n = (gap or 0) * 100
    gap_flag = "是" if (gap or 0) > 0.01 else "否"
    return (
        f"11/12收{close_s}/{chg_s}；距涨停约{dist_s}；"
        f"11/12高开>1%={gap_flag}（开盘相对前收{gap_n:+.2f}%，仅解释不是今开）"
    )


def fmt_pepb(row: dict[str, Any]) -> str:
    pe, pb = row.get("pe"), row.get("pb")
    pe_s = f"{pe:.2f}" if isinstance(pe, (int, float)) else "缺失"
    pb_s = f"{pb:.2f}" if isinstance(pb, (int, float)) else "缺失"
    return f"{pe_s}/{pb_s}"


def lot_note(row: dict[str, Any]) -> str:
    close = row.get("close")
    if not isinstance(close, (int, float)) or close <= 0:
        return "缺价不编量"
    lot = 100
    notional = round(close * lot, 2)
    return f"对照尺≠买灯、须先腾仓才能入账；若按1手={lot}股估算约{notional:.0f}元（11/12收盘）"


def fetch_phase(cache_dir: Path, workers: int) -> None:
    apply_window_globals()
    cache_dir.mkdir(parents=True, exist_ok=True)
    stamp_path = cache_dir / "fetch_started.txt"
    if stamp_path.exists():
        fetch_time = stamp_path.read_text(encoding="utf-8").strip()
    else:
        fetch_time = oscan.now_shanghai().strftime("%Y-%m-%d %H:%M:%S UTC+08:00")
        stamp_path.write_text(fetch_time, encoding="utf-8")
    oscan.log(f"[window] {WINDOW_LABEL} asof={ASOF} fetch_time={fetch_time}")

    clist_path = cache_dir / "clist.json"
    if clist_path.exists():
        clist = json.loads(clist_path.read_text(encoding="utf-8"))
        if len(clist) <= 4000:
            oscan.log(f"[clist] cache too small n={len(clist)}; refetch")
            clist = []
    else:
        clist = []
    if len(clist) <= 4000:
        # 东财 push2 本窗 502；不改业务脚本，装配器直接走既有新浪 hs_a 全A回退。
        oscan.log("[clist] eastmoney 502 risk; use sina hs_a full-A fallback (same path as oversold_scan)")
        clist = oscan.fetch_clist_sina(clist_path)
    clist_src = (clist[0].get("_src") if clist else "") or "eastmoney"
    oscan.log(f"[clist] source={clist_src} n={len(clist)}")

    bk_cache = cache_dir / "bk_codes.json"
    oil_codes: set[str] = set()
    power_codes: set[str] = set()
    if bk_cache.exists():
        bk_payload = json.loads(bk_cache.read_text(encoding="utf-8"))
        oil_codes = set(bk_payload.get("oil", []))
        power_codes = set(bk_payload.get("power", []))
        oscan.log(f"[cache] bk oil={len(oil_codes)} power={len(power_codes)}")
    if clist_src != "sina" and (len(oil_codes) < 10 or not (50 <= len(power_codes) <= 200)):
        try:
            oil_codes = oscan.fetch_bk_codes(oscan.OIL_BK)
            power_codes = set()
            for bk in oscan.POWER_BKS:
                power_codes |= oscan.fetch_bk_codes(bk)
            dump_json(bk_cache, {"oil": sorted(oil_codes), "power": sorted(power_codes)})
        except Exception as exc:  # noqa: BLE001
            oscan.log(f"[bk] fetch failed {exc}; keyword fallback")
    elif clist_src == "sina":
        oscan.log("[bk] skip eastmoney BK clist (universe already on sina fallback)")
    oil_codes = oscan.oil_sleeve_codes(oil_codes, [{"code": x.get("f12"), "name": x.get("f14")} for x in clist])

    zt_cache = cache_dir / "zt_pools.json"
    if zt_cache.exists():
        zt_by_date = json.loads(zt_cache.read_text(encoding="utf-8"))
    else:
        zt_by_date = {}
        for d in oscan.trading_days_back(ASOF, 8):
            pool = oscan.fetch_zt_pool(d)
            if pool:
                zt_by_date[d] = pool
        dump_json(zt_cache, zt_by_date)

    halt_map = fetch_halt_pool(cache_dir / "halt_map.json")
    asof_key = ASOF.replace("-", "")
    zt_asof = {str(x.get("c")): x for x in zt_by_date.get(asof_key, [])}
    near_dates = sorted(zt_by_date.keys(), reverse=True)
    session_dates = near_dates[:5]
    near_codes: set[str] = set()
    for d in session_dates:
        for x in zt_by_date.get(d, []):
            near_codes.add(str(x.get("c")))
    max_lbc = 0
    lianban_codes: set[str] = set()
    for x in zt_by_date.get(asof_key, []):
        lbc = int(x.get("lbc") or 0)
        max_lbc = max(max_lbc, lbc)
        if lbc >= 2:
            lianban_codes.add(str(x.get("c")))

    codes = [str(x["f12"]) for x in clist]
    klines = load_or_fetch_klines(codes, cache_dir / "klines", workers=workers)
    retry_empty_klines(codes, klines, cache_dir / "klines")

    tf_path = cache_dir / "tencent_fund.json"
    if tf_path.exists():
        tencent_fund = json.loads(tf_path.read_text(encoding="utf-8"))
        oscan.log(f"[cache] tencent_fund {len(tencent_fund)}")
    else:
        tencent_fund = oscan.fetch_tencent_fundamentals(codes)
        dump_json(tf_path, tencent_fund)

    rows, kick = compute_rows(
        clist,
        klines,
        tencent_fund,
        oil_codes,
        power_codes,
        zt_asof,
        lianban_codes,
        near_codes,
        halt_map,
    )
    annotate_drop_why(rows)
    board_scan = Counter(r.get("board") for r in rows)
    k_ok = sum(1 for r in rows if r.get("k_status") == "ok" and r.get("ret_20d") is not None)
    a_ge1 = sum(1 for r in rows if r.get("a_hits"))
    a_ge2 = sum(1 for r in rows if len(r.get("a_hits") or []) >= 2)
    board_a = Counter(r["board"] for r in rows if r.get("a_hits"))
    meta = {
        "window": WINDOW_LABEL,
        "price_asof": ASOF,
        "fetched_at": fetch_time,
        "clist_src": clist_src,
        "scanned": len(clist),
        "boards": dict(board_scan),
        "k_valid": k_ok,
        "pass_a": a_ge1,
        "pass_a2": a_ge2,
        "pass_a_boards": dict(board_a),
        "kick": dict(kick),
        "oil_n": len(oil_codes),
        "power_n": len(power_codes),
        "zt_asof_n": len(zt_asof),
        "near_n": len(near_codes),
        "near_days": len(session_dates),
        "max_lbc": max_lbc,
        "gap_asof_n": sum(1 for r in rows if r.get("gap_asof_gt1")),
        "halt_map_n": len(halt_map),
        "paper_rules": PAPER_RULES,
        "paper_sha8": PAPER_SHA8,
        "paper_sha256": PAPER_SHA256,
    }
    dump_json(cache_dir / "meta.json", meta)
    dump_json(cache_dir / "computed_rows.json", [compact_row(r) for r in rows])
    oscan.log(f"[compute] scanned={len(rows)} k_ok={k_ok} pass_a={a_ge1} a2={a_ge2} kick={dict(kick)}")


def load_computed(cache_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = json.loads((cache_dir / "computed_rows.json").read_text(encoding="utf-8"))
    for r in rows:
        r["name"] = clean_name(r.get("name") or "")
    meta = json.loads((cache_dir / "meta.json").read_text(encoding="utf-8"))
    return rows, meta


def vs_evening_oversold(shortlist: list[dict[str, Any]], by_code: dict[str, dict[str, Any]]) -> dict[str, Any]:
    short_codes = [r["code"] for r in shortlist]
    keep, drop, new = [], [], []
    for code in EVENING_TEN:
        if code in short_codes:
            keep.append(code)
        else:
            rec = by_code.get(code) or {}
            why = rec.get("drop_why") or ",".join(rec.get("c_reasons") or []) or "独立重算后未进分板/行业配额前10"
            drop.append({"code": code, "name": rec.get("name") or EVENING_TEN_LABELS.get(code, ""), "why": why})
    for rec in shortlist:
        if rec["code"] not in EVENING_TEN:
            new.append({"code": rec["code"], "name": rec["name"]})
    return {"keep": keep, "drop": drop, "new": new}


def vs_lowland(picked: dict[str, list[dict[str, Any]]], by_code: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    picked_codes = {b: {r["code"] for r in rows} for b, rows in picked.items()}
    all_picked = set().union(*picked_codes.values()) if picked_codes else set()
    evening_all = set()
    for b, codes in EVENING_LOWLAND.items():
        evening_all |= set(codes)
        maintain, correct, add = [], [], []
        for code in codes:
            rec = by_code.get(code) or {}
            still, still_why = still_lowland(rec) if rec else (False, "缺数据")
            ok, _, gate_why = classify_lowland_gate(rec) if rec else (False, False, "缺数据")
            if code in picked_codes.get(b, set()):
                maintain.append({"code": code, "name": rec.get("name") or EVENING_LOWLAND_LABELS.get(code, ""), "why": still_why})
            elif rec and not still:
                correct.append({"code": code, "name": rec.get("name") or EVENING_LOWLAND_LABELS.get(code, ""), "why": still_why or gate_why})
            elif rec and not ok:
                correct.append({"code": code, "name": rec.get("name") or EVENING_LOWLAND_LABELS.get(code, ""), "why": gate_why})
            else:
                out.setdefault("_board_blind", []).append(
                    {
                        "code": code,
                        "name": rec.get("name") or EVENING_LOWLAND_LABELS.get(code, ""),
                        "board": b,
                        "why": rec.get("lowland_why") or "仍低未进前5",
                    }
                )
        for rec in picked.get(b, []):
            if rec["code"] not in codes:
                add.append({"code": rec["code"], "name": rec["name"], "why": rec.get("lowland_why") or "本窗独立重算入前5"})
        out[b] = {"maintain": maintain, "correct": correct, "add": add, "blind": []}
    evening_blind = out.pop("_board_blind", [])
    for x in evening_blind:
        b = x.get("board")
        if b in out:
            out[b].setdefault("blind", []).append(x)
    blind = list(evening_blind)
    for rec in by_code.values():
        if rec["code"] in evening_all or rec["code"] in all_picked:
            continue
        if rec.get("lowland_ok") and rec.get("board") in picked:
            if rec["code"] in HELD_ANY or rec.get("is_power") or rec.get("is_coal") or is_broker_row(rec):
                continue
            blind.append(
                {
                    "code": rec["code"],
                    "name": rec["name"],
                    "board": rec["board"],
                    "why": "仍低未进前5",
                    "pe": rec.get("pe"),
                    "pb": rec.get("pb"),
                    "dev_ma20": rec.get("dev_ma20"),
                    "pctile_60d": rec.get("pctile_60d"),
                }
            )
    rest = [x for x in blind if x.get("code") not in evening_all]
    extra_watch = []
    for rec in by_code.values():
        if rec["code"] in evening_all or rec["code"] in all_picked:
            continue
        still, why = still_lowland(rec)
        if not still:
            continue
        if rec["code"] in HELD_ANY or rec.get("is_power") or rec.get("is_coal") or is_broker_row(rec):
            continue
        if oscan.is_st(rec.get("name") or "") or oscan.is_delist(rec.get("name") or ""):
            continue
        pe, pb = rec.get("pe"), rec.get("pb")
        if pe is None or pe <= 0 or pe > 32:
            continue
        extra_watch.append(rec)
    extra_watch.sort(key=lowland_rank)
    for rec in extra_watch[:12]:
        rest.append(
            {
                "code": rec["code"],
                "name": rec["name"],
                "board": rec["board"],
                "why": rec.get("lowland_why") or "仍低未进前5",
                "pe": rec.get("pe"),
                "pb": rec.get("pb"),
                "dev_ma20": rec.get("dev_ma20"),
                "pctile_60d": rec.get("pctile_60d"),
            }
        )
    out["blind"] = evening_blind + rest[:12]
    return out


def review_line(by_code: dict[str, dict[str, Any]], code: str, fallback: str, extra: str = "") -> str:
    rec = by_code.get(code) or {}
    name = rec.get("name") or fallback
    a = "".join(rec.get("a_hits") or []) or "无"
    fact = chase_fact(rec) if rec else "缺K"
    cwhy = ",".join(rec.get("c_reasons") or []) or "无C"
    bits = [f"`{code} {name}` A={a}", fact, f"C={cwhy}"]
    if extra:
        bits.append(extra)
    return "；".join(bits)


def write_reports(cache_dir: Path, out_dirs: list[Path]) -> None:
    apply_window_globals()
    rows, meta = load_computed(cache_dir)
    by_code = {r["code"]: r for r in rows}
    fetch_time = meta.get("fetched_at") or oscan.now_shanghai().strftime("%Y-%m-%d %H:%M:%S UTC+08:00")

    passed_a = [r for r in rows if r.get("a_hits")]
    passed_c = [r for r in passed_a if not r.get("c_reasons") and not r.get("is_power")]
    value_q = [r for r in passed_c if r.get("value_ok") and len(r.get("a_hits") or []) >= 2]
    shortlist = pick_oversold(value_q)
    taken = {r["code"] for r in shortlist}
    lowland = pick_lowland(rows)
    vs_os = vs_evening_oversold(shortlist, by_code)
    vs_ll = vs_lowland(lowland, by_code)

    quote_codes = [r["code"] for r in shortlist]
    for board_rows in lowland.values():
        quote_codes.extend(r["code"] for r in board_rows)
    for code in EVENING_TEN + LIMITED_NINE + LOWLAND_REVIEW_CODES:
        quote_codes.append(code)
    for codes in EVENING_LOWLAND.values():
        quote_codes.extend(codes)
    quote_codes = list(dict.fromkeys(quote_codes))
    quotes_raw = oscan.cross_quotes(quote_codes)
    quotes = {c: quotes_asof(quotes_raw.get(c) or {}, (by_code.get(c) or {}).get("close")) for c in quote_codes}

    board_scan = Counter(r.get("board") for r in rows if r.get("board"))
    board_a = Counter(r["board"] for r in rows if r.get("a_hits"))
    k_ok = sum(1 for r in rows if r.get("k_status") == "ok" and r.get("ret_20d") is not None)
    coverage = {
        "scanned": meta.get("scanned", len(rows)),
        "boards": meta.get("boards") or dict(board_scan),
        "k_valid": k_ok,
        "pass_a": sum(1 for r in rows if r.get("a_hits")),
        "pass_a_boards": dict(board_a),
        "pass_a2": sum(1 for r in rows if len(r.get("a_hits") or []) >= 2),
        "pass_c": len(passed_c),
        "value_quality": len(value_q),
        "shortlist": len(shortlist),
        "lowland": {b: len(v) for b, v in lowland.items()},
        "clist_src": meta.get("clist_src"),
        "kline_per_stock": True,
        "universe_note": "本窗对沪深主板+创业+科创逐只拉不复权日K；独立重计，不复制晚筛 5223 故事",
    }
    kick = meta.get("kick") or {}
    coverage_line = (
        f"- 扫描 {coverage['scanned']}（主板 {board_scan.get('main', 0)} / 创业 {board_scan.get('chinext', 0)} / "
        f"科创 {board_scan.get('star', 0)}）→ K线有效 {k_ok} → 过A {coverage['pass_a']} "
        f"（主板 {board_a.get('main', 0)} / 创业 {board_a.get('chinext', 0)} / 科创 {board_a.get('star', 0)}；"
        f"满2 {coverage['pass_a2']}）→ 过C {len(passed_c)} → 价值质量(满2且PE/PB) {len(value_q)} → 短名单 **{len(shortlist)}**。"
    )

    missing = [r for r in rows if r.get("k_status") != "ok" or r.get("missing_reason")]
    missing_strict = [r for r in rows if r.get("k_status") != "ok"]

    side_notes: dict[str, list[dict[str, Any]]] = {"main": [], "chinext": [], "star": []}
    for r in sorted(value_q, key=lambda x: (-len(x["a_hits"]), -(x.get("score") or 0))):
        if r["code"] in taken or r["code"] in HELD_ANY or r["code"] in CLEARED or r.get("is_bank"):
            continue
        if r["code"] in oscan.OIL_WATCHED or r["code"] in oscan.OIL_LOW_REVIEW or r["code"] in FALSE_STABLE:
            continue
        if is_broker_row(r) or r.get("is_coal") or r["code"] in NAMED_KEEP_WATCH:
            continue
        b = r["board"]
        if b in side_notes and len(side_notes[b]) < 5:
            side_notes[b].append(r)

    # oil / opt / named reviews
    oil_bits = [
        review_line(by_code, "601872", "招商轮船", "已观察不占新席；微回调≠抄底；不因油运袖整组删除"),
        review_line(by_code, "600026", "中远海能", "已观察不占新席；不因油运袖整组删除"),
        review_line(by_code, "601975", "招商南油", "已观察不占新席；不因油运袖整组删除"),
        review_line(
            by_code,
            "000520",
            "凤凰航运",
            "低位须单独评估；下跌≠抄底；无公司订单/UKMTO新锚不进前列；过A也不默删油运袖",
        ),
    ]
    oil_pass = [
        r
        for r in rows
        if r.get("sleeve_oil") and r.get("a_hits") and r["code"] not in {"601872", "600026", "601975", "000520"}
    ]
    oil_pass.sort(key=lambda x: (-len(x.get("a_hits") or []), -(x.get("score") or 0)))
    for r in oil_pass[:8]:
        oil_bits.append(review_line(by_code, r["code"], r.get("name") or "", "油运过A逐票，不因袖标签删除"))
    opt_bits = []
    for code, nm in oscan.NAMED_OPT_CHASE.items():
        opt_bits.append(review_line(by_code, code, nm, "点名近板/涨停/大涨忌追；未近板且过A不得因光模块主题删除"))
    other_opt = [
        r
        for r in rows
        if r.get("sleeve_opt") and r["code"] not in oscan.NAMED_OPT_CHASE and r.get("a_hits") and not r.get("c_reasons")
    ]
    other_opt.sort(key=lambda x: (-len(x.get("a_hits") or []), -(x.get("score") or 0)))
    for r in other_opt[:6]:
        opt_bits.append(review_line(by_code, r["code"], r.get("name") or "", "未近板且过A，不因光模块主题删除"))

    explain_bits = [
        f"对照昨晚晚筛十票（agent {EVENING_AGENT} 抓取 {EVENING_FETCH}，同一 price_asof=11/12），本窗全A独立重算，禁止抄名单。",
        "C 按未开盘口径，未把今日高开>1%写入C；11/12 当日高开>1%仅作相对晚筛解释；未知的 11/13 开盘不写成已高开。",
        "今早新闻硬增量（UKMTO 203-26 / 204-26、NVIDIA 8-K 人事、油价相对 20:57 窗上涨）不作为题材总标签删票或凑票。",
        "16:14 临时百货/兵装/渔业轴已作废。次日正式倾向只参考，不改扫描门槛、不整组删票。",
        "席满不是不买：满A过B/C未进配额的票留在完整源候选。",
    ]
    for item in vs_os["drop"]:
        explain_bits.append(f"`{item['code']} {item['name']}` 换出：{item['why']}。")
    for item in vs_os["new"]:
        rec = by_code.get(item["code"]) or {}
        explain_bits.append(
            f"`{item['code']} {item['name']}` 新入：满A{len(rec.get('a_hits') or [])}、过B/C，分板/行业配额入席。"
        )

    hot_bits = []
    for r in rows:
        if any(k in (r.get("name") or "") for k in oscan.HOT_SLEEVE_WATCH_NAMES):
            a = "".join(r.get("a_hits") or []) or "无"
            why = ",".join(r.get("c_reasons") or []) or "热袖/高波动，忌追杀反弹，不进短名单前列"
            hot_bits.append(f"`{r['code']} {r['name']}` A={a} C={why}；独立重算仍不进前列")

    oke_note = review_line(
        by_code,
        "688308",
        "欧科亿",
        "晚筛旁注PE偏高未过B；本窗腾讯TTM独立重算PE=18.59过价值门故入科创观察席，不是沿用晚筛结论；观察·不对齐本账户开仓",
    )
    luan_rec = by_code.get("601699") or {}
    luan_note = (
        f"`601699 潞安环能` 本窗A={''.join(luan_rec.get('a_hits') or []) or '无'}；{chase_fact(luan_rec) if luan_rec else '缺K'}；"
        f"C={','.join(luan_rec.get('c_reasons') or []) or '无C'}；库档仍丙、不自动升乙；煤炭不是电力，不作煤炭净新主推。"
    )
    held_note = (
        "现持不占新观察主推（不改账；真金与纸面隔离）："
        "纸面 `601318 中国平安` 200｜`000429 粤高速A` 700｜`601088 中国神华` 200（忌叠力·禁再开电力）｜"
        "`300926 博俊科技` 700（纸面仍持；真金已清0）｜`603806 福斯特` 600（11/12收12.51已触硬失效12.61，卖出建议已交用户、尚未入账，不是本扫卖令；勿再满开主推，不要写成23000）。"
        "真金旁证：福斯特 23000（用户确认原600当日已卖，现23000全部为当日误买）｜粤高速A 700｜美力科技 1300｜中国平安 200｜"
        "中国神华 200｜晋控煤业 600（可用0，已在甲不降乙）｜精锻科技 200｜博俊 0。"
        "已清不加回：东方财富｜美的集团｜大秦铁路｜兴业银行。"
        "旁观：海康威视伪稳不升进攻；药明康德点名保留观察，点名≠建议买入。"
    )

    clist_src = meta.get("clist_src") or "unknown"
    halt_n = int(kick.get("停牌或无价", 0)) + int(kick.get("停牌", 0)) + int(kick.get("退市整理", 0))
    kline_empty = int(kick.get("K线空", 0))
    blindspots = [
        "不复权日K（fqt=0）；A③单独过门很宽，短名单只从满2条A（且至少含①或②）且过 B/C 的票里按分板/行业配额取 5–10，不用仅③票凑数。",
        "未全量核验立案/停牌全文；无价票原因不明标 UNKNOWN，不编造停牌；仅当有公开停牌证据才标 HALT。",
        "东财 push2 可能 502；clist 优先东财镜像，失败则回退新浪 hs_a（剔北交所），日K 优先东财不复权、失败回退腾讯不复权。失败票计入缺失清单，不编造。",
        "油运/光模块不整组踢出；近板/涨停/5日急弹≥+10% 按票踢。光模块点名表可能漏侧链。",
        "60日分位用近60根收盘 ≤ 现价 占比；晚筛十票用本窗独立重算交叉，禁止抄晚筛数字。",
        f"clist 源={clist_src}；无 {ASOF} 收盘或停牌/无价 {halt_n}；K线空 {kline_empty}。新浪回退时行业字段缺失，电力识别靠简称关键词+已知点名，可能漏发电名，短名单仍禁电力。",
        "窗口按未开盘口径写 C（不用今日高开>1%）。11/13 开盘未知，核价用 11/12 收盘交叉新浪+腾讯。",
        "PE 价值门用腾讯 TTM（qt 字段 39），不用新浪静态市盈率；TTM≤0 或 >40 记价值未过，不编造。",
        "价值质量要求 PE∈[5,40]、PB∈[0.4,4]、现价≥1，退市整理不进短名单；短名单排序把低PE/破净权重大于单边暴跌。畸高PE/PB降权，不排短名单最前。",
        "本窗对沪深全A逐只拉不复权日K；相对晚筛的换入/换出来自独立重算，不是抄名单，也不是今早 240 只短扫。",
        "煤炭/油不是电力；电力股不进短名单。已持晋控与神华同属煤炭链时超跌可观察，不作煤炭净新主推，源候选不因煤炭标签删除。",
        "财务风险未做年报逐项复核，缺则标待补，不得因缺复核写成不买。",
        "日K：先复用已缓存腾讯不复权，缺口改新浪日K；东财 push2 本窗 502 未作为主源。来源混合写入覆盖盲点，不编造价格。",
    ]

    evening_bits = "｜".join(f"`{c} {EVENING_TEN_LABELS[c]}`" for c in EVENING_TEN)
    sec_bits = "｜".join(f"`{c} {LIMITED_LABELS[c]}`" for c in LIMITED_NINE)
    keep_disp = "、".join(
        f"`{c} {by_code.get(c, {}).get('name') or EVENING_TEN_LABELS.get(c, '')}`" for c in vs_os["keep"]
    ) or "无"
    drop_disp = "、".join(f"`{d['code']} {d['name']}`（{d['why']}）" for d in vs_os["drop"]) or "无"
    new_disp = "、".join(f"`{d['code']} {d['name']}`" for d in vs_os["new"]) or "无"

    sec_live = []
    for c in LIMITED_NINE:
        rec = by_code.get(c)
        if not rec:
            sec_live.append(f"`{c}`缺数据")
            continue
        a = "".join(rec.get("a_hits") or []) or "无"
        extra = ""
        if rec.get("gap_asof_gt1"):
            extra = "；11/12曾高开>1%（可解释去留，本窗不作C）"
        if rec.get("c_reasons"):
            extra += "；本窗C=" + ",".join(rec["c_reasons"])
        if rec["code"] in taken:
            extra += "；本窗保留/新入短名单"
        elif rec.get("value_ok") and len(rec.get("a_hits") or []) >= 2 and not rec.get("c_reasons") and not rec.get("is_power"):
            if "②" not in (rec.get("a_hits") or []):
                extra += (
                    f"；仅{''.join(rec.get('a_hits') or [])}（②未过，MA20={oscan.fmt_pct(rec.get('dev_ma20'))}），"
                    "席满不是不买"
                )
            else:
                extra += "；满A过B/C未进配额前10（席满不是不买）"
        sec_live.append(f"`{c}`A={a}{extra}")

    zt_n = int(meta.get("zt_asof_n") or 0)
    max_lbc = int(meta.get("max_lbc") or 0)
    gap_n = int(meta.get("gap_asof_n") or 0)

    md: list[str] = []
    md.append(f"# 早盘全A价值超跌硬扫 · {WINDOW_DATE}")
    md.append("")
    md.append(
        f"> **窗口** {WINDOW_LABEL}（Asia/Shanghai）｜**price_asof** {ASOF} 收盘"
        f"（今日尚未开盘/竞价；日K asof 停在 11/12）｜抓取开始 {fetch_time}｜"
        "价源：东财不复权日K（clist 失败则回退新浪 hs_a）；"
        "短名单 11/12 收盘交叉新浪 + 腾讯｜教育模拟｜"
        "**扫描 ≠ 买卖灯 ≠ 下单 ≠ 改灯 ≠ 改账**"
    )
    md.append("")
    md.append("## 口径")
    md.append("")
    md.append(
        "- **A硬 ≥1**（满2优先）：①近20日≤−12% 或 近5日≤−6%；②相对MA20≤−6%；③近60日价格分位≤40%。"
        "60日分位 = 近60根收盘中 ≤ 现价 的占比（与晚筛同口径）。"
    )
    md.append("- **B软**：PE>0；破净/低PE优先；畸高PE/PB降权；非脉冲阴跌；非ST。")
    md.append(
        "- **C排除必须逐票可核验**，禁止用「油运忌追 / 光模块忌追」整组清零。"
        f"涨停/连板/近板（11/12 官方涨停池旁证 n={zt_n}，最高连板 {max_lbc}）、"
        "已相对高（5日急弹≥+10% 或 60日分位≥70%）忌追、无量僵尸、停牌、ST、电力不进短名单、"
        "已持不占新观察、已清不加回主推前列。"
        "**不用「今日高开>1%」作C排除**（今开未知；11/12 当日高开仅作相对晚筛解释）。"
        "停牌须有公开证据；原因不明标 UNKNOWN，不编造停牌。"
    )
    md.append("- 创业板资格已开通 → **可对齐**。科创板入短名单必须标 **观察·不对齐本账户开仓**。银行最多 1 只且仅对照，不把第二只银行塞成强制席。")
    md.append(
        f"- 默认建议进 **乙**（库档仍丙的票命中也不自动升乙；`601001 晋控煤业` 已在甲，不降乙）。"
        f"必须独立用 {ASOF} 收盘对沪深全A重算，禁止抄 11/12 晚筛名单或今早本机 240 只短扫。"
        f"纸面规则 {PAPER_RULES} SHA256 `{PAPER_SHA256}`（SHA8 `{PAPER_SHA8}`），生效 2026-11-12 14:22:20 Asia/Shanghai。本扫不对齐改规则文件。"
    )
    md.append("")
    md.append("## 覆盖 / 踢出")
    md.append("")
    md.append(coverage_line)
    md.append(f"- 踢出计数：{kick}")
    md.append(
        f"- 油运BK={oscan.OIL_BK} n={meta.get('oil_n')}（sleeve_hot=yes，**不整组踢出**；已观察不占新席："
        "`601872 招商轮船`/`600026 中远海能`/`601975 招商南油`；低位须单独评估 `000520 凤凰航运`）。"
        "光模块用代码+简称点名近板/涨停票，不整组踢 BK1136。"
        f"电力BK n={meta.get('power_n')}（煤炭/油不是电力，不因神华叠力而开电力，也不用电力禁令抹掉煤炭票）。"
        f"{ASOF} 涨停池 n={zt_n}，近{meta.get('near_days')}个交易日涨停去重 n={meta.get('near_n')}，本窗涨停池 max_lbc={max_lbc}。"
    )
    md.append(
        f"- 本窗 C 按未开盘口径：**不用「今日高开>1%」作排除**，也不把未知的 11/13 开盘写成已高开。"
        f"若把 {ASOF} 当日高开>1% 当 C，将多踢 {gap_n} 只（仅解释，不作为本窗排除）。"
    )
    md.append("")
    md.append("## 方法盲点")
    md.append("")
    for b in blindspots:
        md.append(f"- {b}")
    md.append(f"- {held_note}本扫不改买卖灯。")
    md.append("")
    md.append("## 超跌短名单（建议并乙｜5–10）")
    md.append("")
    md.append("| # | 代码+全称 | 板 | 昨收/相对前收 | A触发（①②③） | B软一句 | 一句理由 | 对齐 |")
    md.append("|---|-----------|----|-----------|------|----------|------|------|")
    if not shortlist:
        md.append("| — | 空过，不凑票 | — | — | — | — | 满2且过B/C且分板配额后不足5，如实少交 | — |")
    for i, row in enumerate(shortlist, 1):
        chg = row.get("chg_pct")
        chg_s = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "NA"
        reason = oscan.reason_line(row)
        extra = row.get("extra_note")
        if extra:
            reason = reason + "；" + extra
        md.append(
            f"| {i} | `{row['code']} {row['name']}` | {board_label(row['board'])} | "
            f"{row['close']:.2f} / {chg_s} | {oscan.fmt_a(row)} | {row.get('b_note') or ''} | {reason} | {row['align']} |"
        )
    md.append("")
    md.append("### 分板")
    md.append("")
    board_short = Counter(r["board"] for r in shortlist)
    md.append(f"- 主板：**{board_short.get('main', 0)}**")
    md.append(f"- 创业板：**{board_short.get('chinext', 0)}**")
    md.append(f"- 科创板：**{board_short.get('star', 0)}**")
    md.append("")
    md.append("### 分板价值旁注（不占超跌短名单名额）")
    md.append("")
    for key, title in (("main", "主板"), ("chinext", "创业板"), ("star", "科创板")):
        items = side_notes.get(key) or []
        if not items:
            md.append(f"- {title}：无")
            continue
        bits = []
        for r in items:
            al = align_label(r["board"]) if key != "main" else "主板"
            pe, pb = r.get("pe"), r.get("pb")
            if pe is not None and pb is not None:
                bits.append(f"`{r['code']} {r['name']}` A={''.join(r['a_hits'])} PE={pe:.1f}/PB={pb:.2f}（{al}）")
            else:
                bits.append(f"`{r['code']} {r['name']}` A={''.join(r.get('a_hits') or [])}（{al}；估值缺失待补）")
        md.append(f"- {title}：" + "；".join(bits))
    md.append("")
    md.append("## 相对昨晚晚筛十票（同一 price_asof=11/12 收盘，独立全A重算）")
    md.append("")
    md.append(
        f"晚筛对照来源 agent `{EVENING_AGENT}`，抓取 {EVENING_FETCH}。本窗对沪深全A独立重算，禁止抄昨晚短名单。"
        f"晚筛十票：{evening_bits}"
    )
    md.append("")
    md.append("- 保留：" + keep_disp)
    md.append("- 换出：" + drop_disp)
    md.append("- 新入：" + new_disp)
    md.append("- 去留解释：" + "".join(explain_bits))
    if hot_bits:
        md.append("- 热袖已剔除对照：" + "；".join(hot_bits))
    md.append("- 油运逐票（不整组删除）：" + "；".join(oil_bits))
    md.append("- 光模块逐票（不整组删除）：" + "；".join(opt_bits))
    md.append("- 欧科亿对照：" + oke_note)
    md.append("- 潞安环能对照：" + luan_note)
    md.append(
        "- 晋控/美力对照："
        + review_line(by_code, "601001", "晋控煤业", "真金已持、已在甲不降乙；超跌可观察，不作煤炭净新主推")
        + "；"
        + review_line(by_code, "300611", "美力科技", "真金已持1300，不占新观察")
    )
    md.append("")
    md.append("### 晚筛十票独立重算交叉（禁止抄晚筛数字）")
    md.append("")
    md.append("| 代码 | 本窗收盘 | A触发 | 20日 | 5日 | MA20偏离 | 60日分位 | PE/PB | 去留 |")
    md.append("|------|----------|------|------|-----|----------|----------|-------|------|")
    for code in EVENING_TEN:
        rec = by_code.get(code) or {}
        a = "".join(rec.get("a_hits") or []) or "无"
        close = rec.get("close")
        close_s = f"{close:.2f}" if isinstance(close, (int, float)) else "NA"
        pctile = rec.get("pctile_60d")
        pctile_s = f"{pctile:.2f}" if pctile is not None else "NA"
        stay = "保留" if code in vs_os["keep"] else "换出"
        md.append(
            f"| `{code}` | {close_s} | {a} | {oscan.fmt_pct(rec.get('ret_20d'))} | "
            f"{oscan.fmt_pct(rec.get('ret_5d'))} | {oscan.fmt_pct(rec.get('dev_ma20'))} | {pctile_s} | {fmt_pepb(rec)} | {stay} |"
        )
    md.append("")
    md.append(
        f"- 次对照（今早本机有限短扫，抓取 {LIMITED_FETCH}，universe 仅 240，非正式、覆盖不足，不得当全A结论）："
        f"{sec_bits}。本窗旁注：" + "；".join(sec_live) + "。"
    )
    md.append("")
    md.append("## 核价（东财日K / 新浪 / 腾讯）")
    md.append("")
    md.append("| 代码 | 日K 11/12收 | 新浪11/12 | 腾讯11/12 | 是否一致 | 盘前现价字段(≠今开) |")
    md.append("|------|-------------|-----------|-----------|----------|---------------------|")
    for row in shortlist:
        q = quotes.get(row["code"], {})
        sina_s = f"{q['sina_asof']:.2f}" if isinstance(q.get("sina_asof"), (int, float)) else "NA"
        tenc_s = f"{q['tencent_asof']:.2f}" if isinstance(q.get("tencent_asof"), (int, float)) else "NA"
        live = q.get("tencent_close")
        live_s = f"{live:.2f}" if isinstance(live, (int, float)) else "NA"
        md.append(
            f"| `{row['code']}` | {row['close']:.2f} | {sina_s} | {tenc_s} | {q.get('agree') or '缺失'} | {live_s} |"
        )
    md.append("")
    md.append("扫描≠买卖灯｜建议默认进乙｜教育模拟，非投资建议。")
    md.append("")

    payload = {
        "window": f"{WINDOW_LABEL} Asia/Shanghai",
        "price_asof": ASOF,
        "scan_time": fetch_time,
        "fetched_at": fetch_time,
        "education_only": True,
        "scan_is_not_trade_signal": True,
        "paper_rules": f"{PAPER_RULES} SHA8 {PAPER_SHA8}",
        "paper_sha256": PAPER_SHA256,
        "coverage": coverage,
        "kick_counts": kick,
        "blindspots": blindspots,
        "vs_evening": {
            "keep": vs_os["keep"],
            "drop": vs_os["drop"],
            "new": vs_os["new"],
            "evening_ten": EVENING_TEN,
            "evening_agent": EVENING_AGENT,
            "evening_fetch": EVENING_FETCH,
            "explain": "".join(explain_bits),
        },
        "vs_secondary": {
            "limited_nine": LIMITED_NINE,
            "note": "；".join(sec_live),
            "asof": ASOF,
            "universe": 240,
            "informal": True,
            "fetch": LIMITED_FETCH,
        },
        "oil_review": oil_bits,
        "opt_review": opt_bits,
        "shortlist": [
            {
                "code": r["code"],
                "name": r["name"],
                "board": board_label(r["board"]),
                "close": r["close"],
                "chg_pct": r.get("chg_pct"),
                "ret_5d": None if r.get("ret_5d") is None else round(r["ret_5d"], 6),
                "ret_20d": None if r.get("ret_20d") is None else round(r["ret_20d"], 6),
                "dev_ma20": None if r.get("dev_ma20") is None else round(r["dev_ma20"], 6),
                "pctile_60d": None if r.get("pctile_60d") is None else round(r["pctile_60d"], 4),
                "a_hits": r["a_hits"],
                "pe": r.get("pe") if r.get("pe") is not None else "missing",
                "pb": r.get("pb") if r.get("pb") is not None else "missing",
                "industry": r.get("industry") or None,
                "note": (oscan.reason_line(r) + ("；" + r["extra_note"] if r.get("extra_note") else "")),
                "b_note": r.get("b_note"),
                "align": r["align"],
                "pe_src": r.get("pe_src"),
                "quotes": quotes.get(r["code"], {}),
                "quotes_agree": (quotes.get(r["code"]) or {}).get("agree"),
                "ref_lot_not_signal": lot_note(r),
            }
            for r in shortlist
        ],
        "held_paper": HELD_PAPER,
        "held_gold": HELD_GOLD,
        "cleared_not_back": CLEARED,
        "oil_watched_not_new": oscan.OIL_WATCHED,
    }

    # value lowland files
    ll_md: list[str] = []
    ll_md.append(f"# A组价值低地分板 · {WINDOW_DATE}")
    ll_md.append("")
    ll_md.append(
        f"> **窗口** {WINDOW_LABEL}｜**price_asof** {ASOF} 收盘｜抓取 {fetch_time}｜"
        "与超跌同属 A 组，另表分列｜教育模拟｜扫描≠买卖灯"
    )
    ll_md.append("")
    ll_md.append("## 口径")
    ll_md.append("")
    ll_md.append("- 主板：破净价值门（PB<1，PE>0；PE缺失标待补，不写成不买；PE>40 畸高出门）。")
    ll_md.append("- 创业 / 科创：相对低估放宽，不用主板破净硬套；本窗用 PB≤1.2 且 PE∈(0,32] 且现价仍低，避免把已回均线的低PE成长票当成低地。")
    ll_md.append("- 仍足够低：相对 MA20 仍低于约 −0.5% 且未回到分位高区；已回均线附近或回撤已浅则纠偏，哪怕晚筛还在。小幅反弹可保留。")
    ll_md.append("- 各板 ≤5。银行最多 1 只且 **仅对照·勿堆第二银行强制席**。电力不进短名单。已持不占新观察。科创标观察·不对齐；创业可对齐。")
    ll_md.append("- 财务风险公开可核；本窗未做年报逐项复核，缺则标待补。")
    ll_md.append("")
    ll_ok_n = sum(1 for r in rows if r.get("lowland_ok"))
    ll_md.append(
        f"## 覆盖：扫描 {coverage['scanned']} / K有效 {k_ok} / 低地短名单门 {ll_ok_n} "
        f"（主板源 {sum(1 for r in rows if r.get('board')=='main' and r.get('lowland_ok'))} / "
        f"创业 {sum(1 for r in rows if r.get('board')=='chinext' and r.get('lowland_ok'))} / "
        f"科创 {sum(1 for r in rows if r.get('board')=='star' and r.get('lowland_ok'))}）→ 分板各≤5。"
    )
    ll_md.append("")
    for board, title in (("main", "主板"), ("chinext", "创业板"), ("star", "科创板")):
        ll_md.append(f"## {title}")
        ll_md.append("")
        ll_md.append("| # | 代码+全称 | 11/12收 | PB | PE | vsMA20 | 60日分位 | 20日 | 仍低？ | 对齐 | 一句 |")
        ll_md.append("|---|-----------|---------|----|----|--------|----------|------|--------|------|------|")
        for i, r in enumerate(lowland.get(board) or [], 1):
            still, why = still_lowland(r)
            pe_s = f"{r['pe']:.1f}" if isinstance(r.get("pe"), (int, float)) else "待补"
            pb_s = f"{r['pb']:.2f}" if isinstance(r.get("pb"), (int, float)) else "待补"
            note = why + (f"；{r.get('financial_note')}" if r.get("financial_note") else "")
            if r.get("extra_note"):
                note += "；" + r["extra_note"]
            close_s = f"{r['close']:.2f}" if isinstance(r.get("close"), (int, float)) else "NA"
            pctile = r.get("pctile_60d")
            pctile_s = f"{pctile:.1f}%" if isinstance(pctile, (int, float)) else "NA"
            ll_md.append(
                f"| {i} | `{r['code']} {r['name']}` | {close_s} | {pb_s} | {pe_s} | "
                f"{oscan.fmt_pct(r.get('dev_ma20'))} | {pctile_s} | {oscan.fmt_pct(r.get('ret_20d'))} | "
                f"{why} | {r.get('align')} | {note} |"
            )
        if not lowland.get(board):
            ll_md.append("| — | 空过，不凑票 | — | — | — | — | — | — | — | — | 本板过门不足 |")
        ll_md.append("")
        vsb = vs_ll.get(board) or {}
        ll_md.append(
            "- 相对 11/12 晚筛："
            + "维持 "
            + ("、".join(f"`{x['code']} {x['name']}`" for x in vsb.get("maintain") or []) or "无")
            + "；纠偏 "
            + ("、".join(f"`{x['code']} {x['name']}`（{x['why']}）" for x in vsb.get("correct") or []) or "无")
            + "；新增 "
            + ("、".join(f"`{x['code']} {x['name']}`" for x in vsb.get("add") or []) or "无")
            + "；盲点 "
            + ("、".join(f"`{x['code']} {x['name']}`（{x['why']}）" for x in vsb.get("blind") or []) or "无")
        )
        ll_md.append("")
    ll_md.append("## 盲点（仍低未进前5，不是不买）")
    ll_md.append("")
    for x in vs_ll.get("blind") or []:
        ll_md.append(
            f"- `{x['code']} {x['name']}` {board_label(x.get('board') or '')}："
            f"PE={x.get('pe')} PB={x.get('pb')} vsMA20={oscan.fmt_pct(x.get('dev_ma20'))} "
            f"60d={x.get('pctile_60d')}；{x.get('why')}"
        )
    if not vs_ll.get("blind"):
        ll_md.append("- 无额外盲点可列（或本窗过门总数不超过分板席）。")
    ll_md.append("")
    ll_md.append("## 晚筛低地短名单独立重算（禁止抄名单）")
    ll_md.append("")
    ll_md.append("| 代码 | 板 | 11/12收 | PB | PE | vsMA20 | 60日分位 | 本窗判定 |")
    ll_md.append("|------|----|---------|----|----|--------|----------|----------|")
    for board, codes in EVENING_LOWLAND.items():
        for code in codes:
            rec = by_code.get(code) or {}
            still, why = still_lowland(rec) if rec else (False, "缺数据")
            ok, _, gate = classify_lowland_gate(rec) if rec else (False, False, "缺数据")
            picked_set = {r["code"] for r in lowland.get(board) or []}
            if code in picked_set:
                judge = "维持"
            elif not still or not ok:
                judge = f"纠偏：{why if not still else gate}"
            else:
                judge = f"仍低未进前5：{rec.get('lowland_why') or gate}"
            close = rec.get("close")
            close_s = f"{close:.2f}" if isinstance(close, (int, float)) else "NA"
            pctile = rec.get("pctile_60d")
            pctile_s = f"{pctile:.1f}%" if isinstance(pctile, (int, float)) else "NA"
            ll_md.append(
                f"| `{code} {rec.get('name') or EVENING_LOWLAND_LABELS.get(code,'')}` | {board_label(board)} | "
                f"{close_s} | {rec.get('pb') if rec.get('pb') is not None else '缺失'} | "
                f"{rec.get('pe') if rec.get('pe') is not None else '缺失'} | {oscan.fmt_pct(rec.get('dev_ma20'))} | "
                f"{pctile_s} | {judge} |"
            )
    ll_md.append("")
    ll_md.append("## 晚筛旁注独立确认（不是结论，11/12收盘重算）")
    ll_md.append("")
    for code in LOWLAND_REVIEW_CODES:
        rec = by_code.get(code) or {}
        still, why = still_lowland(rec) if rec else (False, "缺数据")
        ok, src, gate = classify_lowland_gate(rec) if rec else (False, False, "缺数据")
        ll_md.append(
            f"- `{code} {rec.get('name') or ''}` 收 {rec.get('close')} PB={rec.get('pb')} PE={rec.get('pe')} "
            f"vsMA20={oscan.fmt_pct(rec.get('dev_ma20'))} 60d={rec.get('pctile_60d')}；"
            f"仍低={still}/{why}；门={ok}/{gate}"
        )
    ll_md.append("")
    ll_md.append("扫描≠买卖灯｜建议默认进乙｜教育模拟，非投资建议。")
    ll_md.append("")

    ll_json = {
        "window": f"{WINDOW_LABEL} Asia/Shanghai",
        "price_asof": ASOF,
        "fetched_at": fetch_time,
        "education_only": True,
        "scan_is_not_trade_signal": True,
        "coverage": {
            "scanned": coverage["scanned"],
            "k_valid": k_ok,
            "lowland_ok": ll_ok_n,
            "boards": {b: len(v) for b, v in lowland.items()},
        },
        "vs_evening": vs_ll,
        "boards": {
            b: [
                {
                    "code": r["code"],
                    "name": r["name"],
                    "board": board_label(r["board"]),
                    "close": r.get("close"),
                    "ret_5d": r.get("ret_5d"),
                    "ret_20d": r.get("ret_20d"),
                    "dev_ma20": r.get("dev_ma20"),
                    "pctile_60d": r.get("pctile_60d"),
                    "a_hits": r.get("a_hits") or [],
                    "pe": r.get("pe") if r.get("pe") is not None else "missing",
                    "pb": r.get("pb") if r.get("pb") is not None else "missing",
                    "note": r.get("lowland_why"),
                    "align": r.get("align"),
                    "financial_note": r.get("financial_note") or "",
                    "quotes": quotes.get(r["code"], {}),
                }
                for r in (lowland.get(b) or [])
            ]
            for b in ("main", "chinext", "star")
        },
    }

    # coverage missing
    cov_md: list[str] = []
    cov_md.append(f"# 覆盖与逐代码缺失 · {WINDOW_DATE}")
    cov_md.append("")
    cov_md.append(f"> 窗口 {WINDOW_LABEL}｜price_asof {ASOF}｜抓取 {fetch_time}｜独立重计，不复制晚筛宇宙故事")
    cov_md.append("")
    cov_md.append(coverage_line)
    cov_md.append(
        f"- K线实际覆盖：对扫描集合逐只拉不复权日K（不是抽样）。clist 源={clist_src}。"
        f"成功 K有效 {k_ok} / 扫描 {coverage['scanned']}；失败/缺失 {len(missing_strict)}。"
    )
    cov_md.append("- 停牌须有公开证据；否则 halt_status=UNKNOWN，禁止编造停牌。")
    cov_md.append("")
    cov_md.append("## 逐代码缺失")
    cov_md.append("")
    cov_md.append("| 代码 | 名称 | 板 | 价格日 | K末日 | K长度 | 原因 | halt | 可重试 |")
    cov_md.append("|------|------|----|--------|-------|--------|------|------|--------|")
    missing_payload = []
    for r in missing_strict:
        halt = r.get("halt_status") or "UNKNOWN"
        retry = "yes" if r.get("retryable") else "no"
        reason = r.get("missing_reason") or "UNKNOWN"
        cov_md.append(
            f"| `{r.get('code') or 'UNKNOWN'}` | {r.get('name') or ''} | {board_label(r.get('board') or '')} | "
            f"{ASOF} | {r.get('k_end') or 'NA'} | {r.get('k_len') or 0} | {reason} | {halt} | {retry} |"
        )
        missing_payload.append(
            {
                "code": r.get("code") or "UNKNOWN",
                "name": r.get("name"),
                "board": r.get("board"),
                "price_date": ASOF,
                "k_end": r.get("k_end") or None,
                "k_len": r.get("k_len") or 0,
                "reason": reason,
                "halt_status": halt,
                "halt_evidence": r.get("halt_evidence") or "",
                "retryable": bool(r.get("retryable")),
            }
        )
    if not missing_strict:
        cov_md.append("| — | 无缺失 | — | — | — | — | 扫描集合均有 asof 日K | — | — |")
    cov_md.append("")
    cov_md.append("## 成功集合")
    cov_md.append("")
    cov_md.append(
        f"成功通过的 {k_ok} 只用汇总+样本，不把数字吻合冒充缺失已解释。"
    )
    samples = [r for r in rows if r.get("k_status") == "ok" and r.get("ret_20d") is not None][:8]
    cov_md.append("样本：" + "、".join(f"`{r['code']} {r['name']}` k_end={r.get('k_end')} k_len={r.get('k_len')}" for r in samples))
    cov_md.append("")

    cov_json = {
        "window": WINDOW_LABEL,
        "price_asof": ASOF,
        "fetched_at": fetch_time,
        "coverage": coverage,
        "missing_n": len(missing_strict),
        "missing": missing_payload,
        "halt_unknown_policy": "原因不明标 UNKNOWN，禁止编造停牌",
        "success_samples": [
            {"code": r["code"], "name": r["name"], "k_end": r.get("k_end"), "k_len": r.get("k_len")}
            for r in samples
        ],
    }

    # combined csv + source candidates
    csv_rows = []
    for r in shortlist:
        csv_rows.append(
            {
                "source": "oversold_shortlist",
                "tier": "shortlist",
                "code": r["code"],
                "name": r["name"],
                "board": board_label(r["board"]),
                "close": r.get("close"),
                "ret_5d": r.get("ret_5d"),
                "ret_20d": r.get("ret_20d"),
                "dev_ma20": r.get("dev_ma20"),
                "pctile_60d": r.get("pctile_60d"),
                "a_hits": "".join(r.get("a_hits") or []),
                "pe": r.get("pe"),
                "pb": r.get("pb"),
                "align": r.get("align"),
                "note": oscan.reason_line(r),
            }
        )
    for board, items in lowland.items():
        for r in items:
            csv_rows.append(
                {
                    "source": "value_lowland_shortlist",
                    "tier": "shortlist",
                    "code": r["code"],
                    "name": r["name"],
                    "board": board_label(r["board"]),
                    "close": r.get("close"),
                    "ret_5d": r.get("ret_5d"),
                    "ret_20d": r.get("ret_20d"),
                    "dev_ma20": r.get("dev_ma20"),
                    "pctile_60d": r.get("pctile_60d"),
                    "a_hits": "".join(r.get("a_hits") or []),
                    "pe": r.get("pe"),
                    "pb": r.get("pb"),
                    "align": r.get("align"),
                    "note": r.get("lowland_why"),
                }
            )
    source_rows = []
    for r in passed_a:
        source_rows.append(
            {
                "source": "oversold_pass_a",
                "tier": "source_candidate",
                "code": r["code"],
                "name": r["name"],
                "board": board_label(r.get("board") or ""),
                "close": r.get("close"),
                "ret_5d": r.get("ret_5d"),
                "ret_20d": r.get("ret_20d"),
                "dev_ma20": r.get("dev_ma20"),
                "pctile_60d": r.get("pctile_60d"),
                "a_hits": "".join(r.get("a_hits") or []),
                "pe": r.get("pe"),
                "pb": r.get("pb"),
                "c_reasons": ",".join(r.get("c_reasons") or []),
                "value_ok": r.get("value_ok"),
                "is_power": r.get("is_power"),
                "is_coal": r.get("is_coal"),
                "held": r["code"] in HELD_ANY,
                "align": align_label(r["board"]) if r.get("board") else "",
                "note": ",".join(r.get("c_reasons") or []) or "过A源候选",
            }
        )
    for r in rows:
        if r.get("lowland_ok") or r.get("lowland_source_only"):
            source_rows.append(
                {
                    "source": "value_lowland_gate",
                    "tier": "source_candidate",
                    "code": r["code"],
                    "name": r["name"],
                    "board": board_label(r.get("board") or ""),
                    "close": r.get("close"),
                    "ret_5d": r.get("ret_5d"),
                    "ret_20d": r.get("ret_20d"),
                    "dev_ma20": r.get("dev_ma20"),
                    "pctile_60d": r.get("pctile_60d"),
                    "a_hits": "".join(r.get("a_hits") or []),
                    "pe": r.get("pe"),
                    "pb": r.get("pb"),
                    "c_reasons": ",".join(r.get("c_reasons") or []),
                    "value_ok": r.get("value_ok"),
                    "is_power": r.get("is_power"),
                    "is_coal": r.get("is_coal"),
                    "held": r["code"] in HELD_ANY,
                    "align": align_label(r["board"]) if r.get("board") else "",
                    "note": r.get("lowland_why"),
                }
            )

    desk: list[str] = []
    desk.append(f"# 投资席短摘要 · A组 · {WINDOW_DATE} 盘前")
    desk.append("")
    desk.append(f"窗口 **{WINDOW_LABEL}**，price_asof **{ASOF} 收盘**（与扫描时间分列）。教育模拟，扫描≠买卖灯，不要写买入××股，不改账。")
    desk.append("")
    desk.append("## 价值低地（分板）")
    desk.append("")
    for board, title in (("main", "主板"), ("chinext", "创业板"), ("star", "科创板")):
        items = lowland.get(board) or []
        vsb = vs_ll.get(board) or {}
        desk.append(f"**{title}**（≤5）：")
        if not items:
            desk.append("- 空过，不凑票。")
        for r in items:
            still, why = still_lowland(r)
            desk.append(
                f"- `{r['code']} {r['name']}` 收 {r.get('close')} PB={r.get('pb')} PE={r.get('pe')} "
                f"vsMA20={oscan.fmt_pct(r.get('dev_ma20'))}；{why}；{r.get('align')}"
            )
        desk.append(
            f"- 相对晚筛：维持 {len(vsb.get('maintain') or [])} / 纠偏 {len(vsb.get('correct') or [])} / 新增 {len(vsb.get('add') or [])}"
        )
        desk.append("")
    desk.append("创业 **可对齐**；科创 **观察·不对齐本账户开仓**。银行若入席仅对照，勿堆第二银行。")
    desk.append("")
    desk.append("## 超跌")
    desk.append("")
    desk.append(f"覆盖：{coverage_line.lstrip('- ')}")
    if not shortlist:
        desk.append("短名单空过，不凑票。")
    for i, r in enumerate(shortlist, 1):
        desk.append(
            f"{i}. `{r['code']} {r['name']}` {board_label(r['board'])} 收 {r.get('close')} "
            f"A={''.join(r.get('a_hits') or [])}；{r.get('align')}"
        )
    desk.append("")
    desk.append(f"- 相对晚筛十票：保留 {keep_disp}；换出 {drop_disp}；新入 {new_disp}。席满不是不买。")
    desk.append("- 今早 240 只短扫只作覆盖对照，不当正式短名单。")
    desk.append("- `601001 晋控煤业` 已在甲；美力/精锻/福斯特/神华/平安/粤高速已持不占新观察。")
    desk.append("")
    desk.append("扫描≠买卖灯｜建议默认进乙｜教育模拟")
    desk.append("")

    csv_header = [
        "source",
        "tier",
        "code",
        "name",
        "board",
        "close",
        "ret_5d",
        "ret_20d",
        "dev_ma20",
        "pctile_60d",
        "a_hits",
        "pe",
        "pb",
        "align",
        "note",
    ]
    src_header = csv_header + ["c_reasons", "value_ok", "is_power", "is_coal", "held"]

    for d in out_dirs:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"oversold-scan-{SCAN_STAMP}.md").write_text("\n".join(md), encoding="utf-8")
        dump_json(d / f"oversold-scan-{SCAN_STAMP}.json", payload)
        (d / f"value-lowland-{SCAN_STAMP}.md").write_text("\n".join(ll_md), encoding="utf-8")
        dump_json(d / f"value-lowland-{SCAN_STAMP}.json", ll_json)
        (d / f"coverage-missing-sources-{SCAN_STAMP}.md").write_text("\n".join(cov_md), encoding="utf-8")
        dump_json(d / f"coverage-missing-sources-{SCAN_STAMP}.json", cov_json)
        (d / f"desk-brief-{SCAN_STAMP}.md").write_text("\n".join(desk), encoding="utf-8")
        with (d / f"a-group-all-{SCAN_STAMP}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=csv_header)
            w.writeheader()
            for row in csv_rows:
                w.writerow({k: row.get(k) for k in csv_header})
        with (d / f"source-candidates-{SCAN_STAMP}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=src_header)
            w.writeheader()
            for row in source_rows:
                w.writerow({k: row.get(k) for k in src_header})
        dump_json(
            d / f"source-candidates-{SCAN_STAMP}.json",
            {
                "window": WINDOW_LABEL,
                "price_asof": ASOF,
                "oversold_pass_a_n": len(passed_a),
                "lowland_gate_n": sum(1 for r in rows if r.get("lowland_ok") or r.get("lowland_source_only")),
                "note": "完整源候选；席满不是不买；题材不整组删除",
            },
        )
        oscan.log(f"[write] {d}")

    oscan.log("SHORTLIST:")
    for i, r in enumerate(shortlist, 1):
        oscan.log(
            f"  {i}. {r['code']} {r['name']} {r['board']} A={''.join(r['a_hits'])} pe={r.get('pe')} pb={r.get('pb')}"
        )
    oscan.log("LOWLAND:")
    for board, items in lowland.items():
        oscan.log(f"  {board}: " + ", ".join(f"{r['code']} {r['name']}" for r in items))


def main() -> int:
    parser = argparse.ArgumentParser(description="2026-11-13 盘前 A 组全A扫描装配器")
    parser.add_argument("--phase", choices=("fetch", "report", "all"), default="all")
    parser.add_argument("--cache", type=Path, default=Path("cache/oversold-20261113"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument(
        "--out",
        type=Path,
        nargs="+",
        default=[
            Path("artifacts/morning-2026-11-13"),
            Path("/opt/cursor/artifacts/morning-2026-11-13"),
            Path("/opt/cursor/artifacts"),
        ],
    )
    args = parser.parse_args()
    apply_window_globals()
    if args.phase in {"fetch", "all"}:
        fetch_phase(args.cache, args.workers)
    if args.phase in {"report", "all"}:
        write_reports(args.cache, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
