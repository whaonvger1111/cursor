#!/usr/bin/env python3
"""沪深全A价值超跌硬扫（教育模拟｜扫描≠买卖灯）。

复用 a_share_monitor 的板块分类与腾讯核价，价源对齐晚筛：东财 clist + 不复权日K，
短名单再交叉新浪 hq / 腾讯 qt。
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

from a_share_monitor.markets import align_label, board_label, classify_board

ASOF_DEFAULT = "2026-11-11"
WINDOW_DATE = "2026-11-12"
WINDOW_LABEL = "2026-11-12 周四盘前"
SCAN_STAMP = "20261112"
NEAR_BOARD_HEIGHT_REF = 4
SHANGHAI = ZoneInfo("Asia/Shanghai")
CLIST_HOSTS = [
    "https://88.push2.eastmoney.com",
    "https://82.push2.eastmoney.com",
    "https://87.push2.eastmoney.com",
    "https://83.push2.eastmoney.com",
    "https://85.push2.eastmoney.com",
    "https://79.push2.eastmoney.com",
    "https://80.push2.eastmoney.com",
    "https://81.push2.eastmoney.com",
    "https://push2delay.eastmoney.com",
    "https://push2.eastmoney.com",
]
KLINE_HOSTS = [
    "https://88.push2his.eastmoney.com",
    "https://82.push2his.eastmoney.com",
    "https://87.push2his.eastmoney.com",
    "https://83.push2his.eastmoney.com",
    "https://79.push2his.eastmoney.com",
    "https://80.push2his.eastmoney.com",
]
ZT_URL = "https://push2ex.eastmoney.com/getTopicZTPool"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
CLIST_FS = "m:1+t:2,m:1+t:23,m:0+t:6,m:0+t:80"
CLIST_FIELDS = (
    "f2,f3,f5,f6,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,"
    "f24,f25,f100,f102,f103,f115"
)

HELD = {
    "601318": "中国平安",
    "000429": "粤高速A",
    "601088": "中国神华",
    "300926": "博俊科技",
    "603806": "福斯特",
}
CLEARED = {
    "300059": "东方财富",
    "000333": "美的集团",
    "601006": "大秦铁路",
    "601166": "兴业银行",
}
WATCH_ONLY = {"002736": "国信证券"}
FALSE_STABLE = {"002415": "海康威视"}
# 油运已观察，不占新观察席（逐票，非整组踢袖）
OIL_WATCHED = {
    "601872": "招商轮船",
    "600026": "中远海能",
    "601975": "招商南油",
}
# 油运低位须单独评估：下跌≠抄底，无公司订单/新锚不进短名单前列
OIL_LOW_REVIEW = {"000520": "凤凰航运"}
NAMED_NOT_FORCE = {
    "600567",
    "600546",
    "600938",
    "301563",
    "300839",
    "688613",
    "688519",
    "301282",
    "603707",
}
# 主对照：昨晚晚筛超跌十票（同一 price_asof=11/11 收盘；禁止抄名单）
EVENING_TEN = [
    "600938",  # 中国海油
    "002772",  # 众兴菌业
    "301345",  # 涛涛车业
    "300483",  # 首华燃气
    "600362",  # 江西铜业
    "603808",  # 歌力思
    "603055",  # 台华新材
    "688015",  # 交控科技
    "301219",  # 腾远钴业
    "300970",  # 华绿生物
]
EVENING_TEN_LABELS = {
    "600938": "中国海油（油气生产不是油运忌追袖，油气链偏弱只观察）",
    "002772": "众兴菌业",
    "301345": "涛涛车业（创业可对齐）",
    "300483": "首华燃气（创业可对齐）",
    "600362": "江西铜业（工业金属不整组剔除）",
    "603808": "歌力思（晚筛记 MA20=-5.75%，本窗若仅①③须如实写）",
    "603055": "台华新材",
    "688015": "交控科技（科创不对齐）",
    "301219": "腾远钴业（创业可对齐；晚筛记 MA20=-4.57%）",
    "300970": "华绿生物（创业可对齐；晚筛新入）",
}
# 次对照：11/11 盘前十票（asof=11/10，已过时仅旁注）
SECONDARY_TEN = [
    "002772",
    "603808",
    "600938",
    "603055",
    "600362",
    "688015",
    "301219",
    "301345",
    "300483",
    "688308",
]
SECONDARY_TEN_LABELS = {
    "002772": "众兴菌业",
    "603808": "歌力思",
    "600938": "中国海油",
    "603055": "台华新材",
    "600362": "江西铜业",
    "688015": "交控科技（科创不对齐）",
    "301219": "腾远钴业",
    "301345": "涛涛车业",
    "300483": "首华燃气",
    "688308": "欧科亿（晚筛已因 11/11 过高换出）",
}
HOT_SLEEVE_WATCH_NAMES = ("万辰集团", "联讯仪器")
NAMED_OPT_CHASE = {
    "002463": "沪电股份",
    "002916": "深南电路",
    "300502": "新易盛",
    "300394": "天孚通信",
    "601138": "工业富联",
}
EXTRA_NOTES = {
    "601699": "与已持神华同属煤炭链、忌叠力；煤炭不是电力，不因叠力整组抹掉；库档仍丙、不自动升乙，勿写成新晋乙",
    "601898": "与已持神华同属煤炭链、忌叠力；煤炭不是电力，不用发电禁令抹掉；只作超跌观察，不写成再开电力",
    "600938": "油气生产不是油运忌追袖，油气链偏弱只观察",
    "000429": "收购包只跟踪不加仓，不占新观察",
    "603806": "11/11 收 12.73，低于观察 12.88、高于失效 12.61，只观察；11:32 酌卖 600 仍待用户，勿再满开主推",
    "300926": "纸面仍持；实盘已清 0，两本分开写；09:25 卖 700 建议仍待用户，本扫不是卖单",
    "603707": "仅对照，禁止写成买尺候选",
    "000520": "油运低位须单独评估：11/11 收 2.81 / -5.07%，距涨停约 16%；下跌≠抄底；无公司订单/UKMTO 新锚不进短名单前列",
    "688308": "晚筛已因 11/11 收 54.04、+8.28%、5日 +10.7% 标过高忌追；独立重算过 A 也不得无解释塞回前列",
}

OIL_BK = "BK1482"
# 仅用东财「电力行业」BK0428。火电/核电/热电等概念板过宽，会误伤半导体等。
POWER_BKS = ("BK0428",)
OPT_NAME_KEYS = (
    "光模块",
    "光器件",
    "光芯片",
    "光迅",
    "旭创",
    "天孚通信",
    "新易盛",
    "源杰",
    "光库科技",
    "德科立",
    "腾景科技",
    "联特科技",
    "太辰光",
    "仕佳光子",
    "铭普光磁",
    "博创科技",
    "剑桥科技",
    "华工科技",
    "中川美",
    "长光华芯",
    "源杰科技",
)
OPT_CODES = {
    "300308",
    "300502",
    "300394",
    "002281",
    "688498",
    "603083",
    "000988",
    "300570",
    "688205",
    "301205",
    "300620",
    "688195",
    "002902",
    "300548",
    "688313",
    "688048",
    "301189",
    "688498",
    "002446",
    "300102",
}
POWER_INDUSTRY_KEYS = ("电力", "火力发电", "水力发电", "核力发电", "热力制供", "电网", "电能")
BANK_KEYS = ("银行",)
PV_KEYS = ("光伏", "硅料", "硅片", "电池组件")


def now_shanghai() -> datetime:
    return datetime.now(tz=SHANGHAI)


def digits(code: str) -> str:
    return "".join(ch for ch in code if ch.isdigit())[-6:]


def secid_of(code: str) -> str:
    num = digits(code)
    market = 1 if num.startswith(("6", "9")) else 0
    return f"{market}.{num}"


def sina_symbol(code: str) -> str:
    num = digits(code)
    return ("sh" if num.startswith(("6", "9")) else "sz") + num


def tencent_symbol(code: str) -> str:
    return sina_symbol(code)


def is_st(name: str) -> bool:
    n = name.upper().replace(" ", "")
    return "ST" in n or n.startswith("S*") or "*ST" in name


def is_delist(name: str) -> bool:
    return "退" in (name or "")


def limit_pct(code: str, name: str) -> float:
    if is_st(name):
        return 5.0
    board = classify_board(code)
    if board in {"chinext", "star"}:
        return 20.0
    return 10.0


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://quote.eastmoney.com/", "Accept": "*/*"})
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def log(msg: str) -> None:
    print(msg, flush=True)


def http_json(url: str, params: dict[str, Any] | None = None, tries: int = 3, timeout: int = 10) -> dict[str, Any]:
    last_err: Exception | str = "unknown"
    sess = _session()
    for i in range(tries):
        try:
            r = sess.get(url, params=params, timeout=timeout)
            if r.status_code == 200 and r.text.lstrip().startswith(("{", "jQuery", "(")):
                text = r.text
                if text.startswith("jQuery"):
                    text = text[text.find("(") + 1 : text.rfind(")")]
                data = json.loads(text)
                if isinstance(data, dict):
                    return data
                last_err = f"non-dict json {type(data)}"
            else:
                last_err = f"http {r.status_code} {r.text[:120]}"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.2 * (i + 1) + random.random() * 0.15)
    raise RuntimeError(f"GET failed {url} params={params} err={last_err}")


def clist_page(pn: int, pz: int = 100, fs: str = CLIST_FS, fields: str = CLIST_FIELDS) -> dict[str, Any]:
    params = {
        "pn": pn,
        "pz": pz,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f12",
        "fs": fs,
        "fields": fields,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
    }
    last_err: Exception | str = "unknown"
    hosts = list(CLIST_HOSTS)
    random.shuffle(hosts)
    attempts = hosts + hosts + hosts[:4]
    for i, host in enumerate(attempts):
        url = f"{host}/api/qt/clist/get"
        try:
            data = http_json(url, params, tries=2, timeout=12)
            if data.get("data"):
                return data
            last_err = f"empty data rc={data.get('rc')}"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            log(f"[clist-retry] pn={pn} host={host} err={last_err}")
        time.sleep(0.35 * (1 + i % 5) + random.random() * 0.4)
    raise RuntimeError(f"clist page {pn} failed: {last_err}")


def _sina_node_page(page: int, num: int = 80, node: str = "hs_a") -> list[dict[str, Any]]:
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
    params = {"page": page, "num": num, "sort": "symbol", "asc": 1, "node": node}
    last_err: Exception | str = "unknown"
    sess = _session()
    for i in range(5):
        try:
            r = sess.get(
                url,
                params=params,
                timeout=20,
                headers={"Referer": "https://finance.sina.com.cn", "User-Agent": UA},
            )
            if r.status_code == 200 and r.text.lstrip().startswith("["):
                data = json.loads(r.text)
                if isinstance(data, list):
                    return data
                last_err = f"non-list json {type(data)}"
            else:
                last_err = f"http {r.status_code} {r.text[:120]}"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.6 * (i + 1) + random.random() * 0.3)
    raise RuntimeError(f"sina node page {page} failed: {last_err}")


def sina_to_em(item: dict[str, Any]) -> dict[str, Any]:
    code = str(item.get("code") or "")
    close = _fnum(item.get("trade"))
    if close is not None and close <= 0:
        close = None
    pe = _fnum(item.get("per"))
    pb = _fnum(item.get("pb"))
    return {
        "f12": code,
        "f14": str(item.get("name") or ""),
        "f2": close,
        "f3": _fnum(item.get("changepercent")),
        "f9": pe,
        "f115": pe,
        "f23": pb,
        "f8": _fnum(item.get("turnoverratio")),
        "f6": _fnum(item.get("amount")),
        "f17": _fnum(item.get("open")),
        "f18": _fnum(item.get("settlement")),
        "f100": "",
        "_src": "sina",
    }


def fetch_clist_sina(cache_path: Path) -> list[dict[str, Any]]:
    """新浪 hs_a 全市场回退：东财 clist 502 时仍独立扫沪深主板+创业+科创。"""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 1
    empty_streak = 0
    while page <= 120:
        try:
            data = _sina_node_page(page, num=80, node="hs_a")
        except Exception as exc:  # noqa: BLE001
            empty_streak += 1
            log(f"[clist-sina] page {page} fail {exc} streak={empty_streak}")
            if empty_streak >= 4:
                break
            time.sleep(1.5 * empty_streak)
            continue
        if not data:
            break
        added = 0
        for item in data:
            rec = sina_to_em(item)
            code = rec["f12"]
            if classify_board(code) not in {"main", "chinext", "star"}:
                continue
            if code in seen:
                continue
            seen.add(code)
            rows.append(rec)
            added += 1
        log(f"[clist-sina] page {page} raw={len(data)} added={added} cumulative={len(rows)}")
        empty_streak = 0
        if len(data) < 80:
            break
        page += 1
        time.sleep(0.12)
    by_code = {str(x["f12"]): x for x in rows}
    rows = list(by_code.values())
    cache_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    log(f"[clist-sina] saved {len(rows)} -> {cache_path}")
    return rows


def fetch_clist_eastmoney(cache_path: Path, max_stall: int = 3) -> list[dict[str, Any]]:
    partial_path = cache_path.with_suffix(".partial.json")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    if partial_path.exists():
        try:
            rows = json.loads(partial_path.read_text(encoding="utf-8"))
            seen = {str(x.get("f12")) for x in rows}
            log(f"[cache] clist partial {len(rows)} from {partial_path}")
        except Exception as exc:  # noqa: BLE001
            log(f"[cache] partial unreadable {exc}")
            rows = []
            seen = set()
    pn = max(1, (len(rows) // 100) + 1)
    stall = 0
    while True:
        try:
            payload = clist_page(pn, pz=100)
        except Exception as exc:  # noqa: BLE001
            stall += 1
            log(f"[clist] page {pn} hard-fail {exc} stall={stall}")
            if stall >= max_stall:
                raise
            time.sleep(2.0 * stall)
            continue
        data = payload.get("data") or {}
        total = int(data.get("total") or 0)
        diff = data.get("diff") or []
        if not diff:
            break
        added = 0
        for item in diff:
            code = str(item.get("f12") or "")
            board = classify_board(code)
            if board not in {"main", "chinext", "star"}:
                continue
            if code in seen:
                continue
            seen.add(code)
            item["_src"] = "eastmoney"
            rows.append(item)
            added += 1
        log(f"[clist] page {pn} got {len(diff)} added={added} cumulative={len(rows)} total={total}")
        partial_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        stall = 0
        if pn * 100 >= total:
            break
        pn += 1
        time.sleep(0.08)
    by_code = {str(item["f12"]): item for item in rows}
    rows = list(by_code.values())
    cache_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    if partial_path.exists():
        partial_path.unlink()
    log(f"[clist] saved {len(rows)} -> {cache_path}")
    return rows


def fetch_clist_all(cache_path: Path) -> list[dict[str, Any]]:
    if cache_path.exists():
        rows = json.loads(cache_path.read_text(encoding="utf-8"))
        if len(rows) > 4000:
            log(f"[cache] clist {len(rows)} from {cache_path}")
            return rows
    partial_path = cache_path.with_suffix(".partial.json")
    if partial_path.exists():
        log("[clist] eastmoney partial exists but incomplete; skip further EM clist hammering, fallback sina hs_a")
        return fetch_clist_sina(cache_path)
    try:
        rows = fetch_clist_eastmoney(cache_path, max_stall=2)
        if len(rows) > 4000:
            return rows
        log(f"[clist] eastmoney incomplete n={len(rows)}; fallback sina")
    except Exception as exc:  # noqa: BLE001
        log(f"[clist] eastmoney failed ({exc}); fallback sina hs_a")
    return fetch_clist_sina(cache_path)


def fetch_bk_codes(bk: str) -> set[str]:
    codes: set[str] = set()
    pn = 1
    while pn <= 20:
        try:
            payload = clist_page(pn, pz=100, fs=f"b:{bk}", fields="f12,f14")
        except Exception as exc:  # noqa: BLE001
            log(f"[bk] {bk} page {pn} fail {exc}")
            break
        data = payload.get("data") or {}
        diff = data.get("diff") or []
        total = int(data.get("total") or 0)
        for item in diff:
            codes.add(str(item.get("f12") or ""))
        if not diff or pn * 100 >= total:
            break
        pn += 1
    log(f"[bk] {bk} n={len(codes)}")
    return codes


def oil_sleeve_codes(fetched: set[str], rows: list[dict[str, Any]]) -> set[str]:
    """油运袖：优先东财 BK1482；失败则用已点名+简称，禁止把失败当成整组清零。"""
    out = set(fetched)
    out |= set(OIL_WATCHED)
    out |= set(OIL_LOW_REVIEW)
    if len(fetched) >= 10:
        return out
    for rec in rows:
        name = rec.get("name") or rec.get("f14") or ""
        if any(k in name for k in ("油运", "油轮", "油品运输")):
            out.add(str(rec.get("code") or rec.get("f12") or ""))
    return {c for c in out if c}


def fetch_zt_pool(date_yyyymmdd: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 0
    while page <= 10:
        params = {
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "dpt": "wz.ztzt",
            "Pageindex": page,
            "pagesize": 200,
            "sort": "zdp:desc",
            "date": date_yyyymmdd,
        }
        try:
            payload = http_json(ZT_URL, params, tries=4, timeout=20)
        except Exception as exc:  # noqa: BLE001
            log(f"[zt] {date_yyyymmdd} page {page} fail {exc}")
            break
        data = payload.get("data") or {}
        pool = data.get("pool") or []
        rows.extend(pool)
        tc = int(data.get("tc") or 0)
        if not pool or (page + 1) * 200 >= tc:
            break
        page += 1
    log(f"[zt] {date_yyyymmdd} n={len(rows)}")
    return rows


def trading_days_back(asof: str, n: int = 8) -> list[str]:
    """Calendar walk; 涨停池接口对非交易日返回空。"""
    d0 = datetime.strptime(asof, "%Y-%m-%d")
    out: list[str] = []
    cur = d0
    for _ in range(20):
        out.append(cur.strftime("%Y%m%d"))
        cur -= timedelta(days=1)
        if len(out) >= n + 4:
            break
    return out


def fetch_kline_tencent(code: str) -> list[dict[str, float | str]]:
    """腾讯不复权日K（param 末位 n）。东财 kline 失败时回退。"""
    sym = tencent_symbol(code)
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    payload = http_json(url, {"param": f"{sym},day,,,90,n"}, tries=3, timeout=15)
    node = ((payload.get("data") or {}).get(sym) or {})
    bars = node.get("day") or node.get("nday") or []
    rows: list[dict[str, float | str]] = []
    prev = None
    for line in bars:
        if not isinstance(line, (list, tuple)) or len(line) < 5:
            continue
        close = float(line[2])
        open_ = float(line[1])
        vol = float(line[5] if len(line) > 5 else 0)
        pct = ((close / prev - 1.0) * 100.0) if prev else 0.0
        rows.append(
            {
                "date": str(line[0])[:10],
                "open": open_,
                "close": close,
                "high": float(line[3]),
                "low": float(line[4]),
                "vol": vol,
                "amt": vol * close * 100.0,
                "pct": pct,
            }
        )
        prev = close
    return [r for r in rows if str(r["date"]) <= ASOF_DEFAULT]


def fetch_kline(code: str) -> list[dict[str, float | str]]:
    params = {
        "secid": secid_of(code),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
        "end": ASOF_DEFAULT.replace("-", ""),
        "lmt": "90",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
    }
    last_err: Exception | str = "unknown"
    hosts = list(KLINE_HOSTS)
    random.shuffle(hosts)
    for i, host in enumerate(hosts[:2]):
        try:
            payload = http_json(f"{host}/api/qt/stock/kline/get", params, tries=1, timeout=15)
            data = payload.get("data") or {}
            klines = data.get("klines") or []
            rows: list[dict[str, float | str]] = []
            for line in klines:
                p = str(line).split(",")
                if len(p) < 9:
                    continue
                rows.append(
                    {
                        "date": p[0],
                        "open": float(p[1]),
                        "close": float(p[2]),
                        "high": float(p[3]),
                        "low": float(p[4]),
                        "vol": float(p[5] or 0),
                        "amt": float(p[6] or 0),
                        "pct": float(p[8] or 0),
                    }
                )
            rows = [r for r in rows if str(r["date"]) <= ASOF_DEFAULT]
            if rows:
                return rows
            last_err = "empty klines"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.12 * (i + 1))
    try:
        rows = fetch_kline_tencent(code)
        if rows:
            return rows
        last_err = "tencent empty"
    except Exception as exc:  # noqa: BLE001
        last_err = exc
    raise RuntimeError(f"kline {code} failed: {last_err}")


def load_or_fetch_klines(codes: list[str], cache_dir: Path, workers: int = 16) -> dict[str, list[dict[str, Any]]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for code in codes:
        fp = cache_dir / f"{code}.json"
        if fp.exists():
            try:
                rows = json.loads(fp.read_text(encoding="utf-8"))
                if isinstance(rows, list):
                    out[code] = rows
                    continue
            except Exception:  # noqa: BLE001
                pass
        missing.append(code)
    log(f"[kline] cached={len(out)} missing={len(missing)}")
    if not missing:
        return out

    def _job(code: str) -> tuple[str, list[dict[str, Any]] | None, str]:
        try:
            rows = fetch_kline(code)
            (cache_dir / f"{code}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            return code, rows, ""
        except Exception as exc:  # noqa: BLE001
            return code, None, str(exc)

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
                    log(f"[kline-fail] {code} {err}")
            if done % 200 == 0 or done == len(missing):
                log(f"[kline] progress {done}/{len(missing)} ok={len(out)} fail={fail}")
    return out


def _fnum(v: Any) -> float | None:
    if v is None or v == "" or v == "-" or v == "—":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return x


def a_metrics(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = [r for r in rows if str(r.get("date", "")) <= ASOF_DEFAULT]
    if len(rows) < 21:
        return None
    closes = [float(r["close"]) for r in rows]
    last = closes[-1]
    if last <= 0:
        return None
    ret_5d = last / closes[-6] - 1 if len(closes) >= 6 else None
    ret_20d = last / closes[-21] - 1
    ma20 = sum(closes[-20:]) / 20.0
    dev_ma20 = last / ma20 - 1
    window = closes[-60:] if len(closes) >= 60 else closes
    pctile_60d = 100.0 * sum(1 for c in window if c <= last) / len(window)
    amt20 = sum(float(r.get("amt") or 0) for r in rows[-20:]) / min(20, len(rows))
    vol20 = sum(float(r.get("vol") or 0) for r in rows[-20:]) / min(20, len(rows))
    last_bar = rows[-1]
    prev_close = closes[-2] if len(closes) >= 2 else last
    gap = (float(last_bar["open"]) / prev_close - 1) if prev_close else 0.0
    # consecutive limit-up / recent limit-up from kline pct
    return {
        "close": last,
        "ret_5d": ret_5d,
        "ret_20d": ret_20d,
        "dev_ma20": dev_ma20,
        "pctile_60d": pctile_60d,
        "amt20": amt20,
        "vol20": vol20,
        "asof_bar": last_bar,
        "prev_close": prev_close,
        "gap_asof": gap,
        "pct_asof": float(last_bar.get("pct") or 0),
        "open_asof": float(last_bar.get("open") or 0),
        "bars": rows,
    }


def detect_a_hits(m: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    r5 = m.get("ret_5d")
    r20 = m.get("ret_20d")
    if r20 is not None and r20 <= -0.12:
        hits.append("①")
    elif r5 is not None and r5 <= -0.06:
        hits.append("①")
    if m.get("dev_ma20") is not None and m["dev_ma20"] <= -0.06:
        hits.append("②")
    if m.get("pctile_60d") is not None and m["pctile_60d"] <= 40.0:
        hits.append("③")
    return hits


def is_limit_up(pct: float, code: str, name: str) -> bool:
    lim = limit_pct(code, name)
    return pct >= lim - 0.15


def near_limit_asof(pct: float, code: str, name: str) -> bool:
    """距涨停约 2 个百分点以内：主板 ≥8%，创业/科创 ≥18%。逐票，非整组。"""
    lim = limit_pct(code, name)
    return pct >= lim - 2.0


def dist_to_limit_pct(close: float | None, prev_close: float | None, code: str, name: str) -> float | None:
    if close is None or prev_close is None or close <= 0 or prev_close <= 0:
        return None
    limit_px = prev_close * (1.0 + limit_pct(code, name) / 100.0)
    return (limit_px / close - 1.0) * 100.0


def too_high(m: dict[str, Any]) -> bool:
    """已相对高、忌追：5 日急弹 ≥+10%，或收盘已远离近低。"""
    r5 = m.get("ret_5d")
    pctile = m.get("pctile_60d")
    if r5 is not None and r5 >= 0.10:
        return True
    if pctile is not None and pctile >= 70:
        return True
    return False


def kline_limit_flags(code: str, name: str, rows: list[dict[str, Any]], lookback: int = 5) -> dict[str, Any]:
    bars = [r for r in rows if str(r.get("date", "")) <= ASOF_DEFAULT]
    recent = bars[-lookback:]
    recent_lu = [r for r in recent if is_limit_up(float(r.get("pct") or 0), code, name)]
    streak = 0
    for r in reversed(bars):
        if is_limit_up(float(r.get("pct") or 0), code, name):
            streak += 1
        else:
            break
    pulse = False
    last5 = bars[-5:]
    if last5:
        worst = min(float(r.get("pct") or 0) for r in last5)
        thresh = -12.0 if classify_board(code) in {"chinext", "star"} else -8.0
        if worst <= thresh:
            rest = sum(float(r.get("pct") or 0) for r in last5) - worst
            # 单日占 5 日跌幅主体才算脉冲；多日阴跌不算
            if abs(worst) >= abs(rest) * 1.5:
                pulse = True
    return {
        "near_board": bool(recent_lu),
        "limit_streak": streak,
        "pulse": pulse,
        "worst_5d_pct": min((float(r.get("pct") or 0) for r in last5), default=0.0),
    }


def value_ok(pe: float | None, pb: float | None, close: float | None = None, name: str = "") -> bool:
    if is_st(name) or is_delist(name):
        return False
    if close is not None and close < 1.0:
        return False
    if pe is None or pe < 5.0 or pe > 40.0:
        return False
    if pb is None or pb < 0.4 or pb > 4.0:
        return False
    return True


def b_note(pe: float | None, pb: float | None, pulse: bool) -> str:
    bits: list[str] = []
    if pb is not None and 0 < pb < 1:
        bits.append(f"破净PB={pb:.2f}")
    elif pb is not None:
        bits.append(f"PB={pb:.2f}")
    if pe is not None and pe > 0:
        if pe <= 15:
            bits.append(f"低PE={pe:.1f}")
        else:
            bits.append(f"PE={pe:.1f}")
    bits.append("脉冲阴跌" if pulse else "非脉冲阴跌")
    return "；".join(bits)


def score_row(row: dict[str, Any]) -> float:
    n = len(row["a_hits"])
    r20 = (row.get("ret_20d") or 0) * 100
    r5 = (row.get("ret_5d") or 0) * 100
    dev = (row.get("dev_ma20") or 0) * 100
    pctile = row.get("pctile_60d") or 50
    pe = row.get("pe")
    pb = row.get("pb")
    s = 48.0 * n
    # 价值超跌：价值权重大于单边暴跌幅度，避免退市刀/题材回撤占满前排
    s += min(16.0, max(0.0, -r20) * 0.55)
    s += min(8.0, max(0.0, -r5) * 0.25)
    s += min(12.0, max(0.0, -dev))
    s += max(0.0, (40.0 - pctile) * 0.4)
    if pe is not None and 5 <= pe <= 12:
        s += 22
    elif pe is not None and pe <= 16:
        s += 16
    elif pe is not None and pe <= 22:
        s += 8
    elif pe is not None and pe <= 28:
        s += 1
    elif pe is not None and pe > 28:
        s -= 12
    if pb is not None and 0.4 <= pb < 1:
        s += 18
    elif pb is not None and pb < 1.5:
        s += 12
    elif pb is not None and pb < 2.2:
        s += 6
    elif pb is not None and pb > 3.2:
        s -= 10
    if row.get("pulse"):
        s -= 6
    if (row.get("turnover") or 0) > 15:
        s -= 8
    ind = row.get("industry") or ""
    if any(k in ind for k in ("多元金融", "房地产开发", "证券Ⅱ")):
        s -= 10
    if any(k in ind for k in ("元件", "其他电子")) and (pb or 0) > 3:
        s -= 8
    return s


def industry_of(item: dict[str, Any]) -> str:
    for key in ("f100", "f102", "f103"):
        v = item.get(key)
        if isinstance(v, str) and v and v not in {"-", "—"}:
            return v
    return ""


def is_power(code: str, name: str, industry: str, power_codes: set[str]) -> bool:
    if code in power_codes:
        return True
    ind = industry or ""
    if any(k in ind for k in ("电气设备", "电网设备", "光伏", "风电设备", "电池")):
        return False
    if any(k in ind for k in POWER_INDUSTRY_KEYS):
        if "设备" in ind:
            return False
        return True
    if "电力" in name and "电气" not in name and "设备" not in name:
        return True
    return False


def is_opt_mod(code: str, name: str) -> bool:
    if code in OPT_CODES:
        return True
    return any(k in name for k in OPT_NAME_KEYS)


def is_bank(industry: str, name: str) -> bool:
    return "银行" in (industry or "") or name.endswith("银行") or "银行" in name


def is_broker(industry: str, name: str) -> bool:
    blob = (industry or "") + (name or "")
    return any(k in blob for k in ("证券", "券商"))


def is_pv(industry: str, name: str) -> bool:
    blob = (industry or "") + name
    return any(k in blob for k in PV_KEYS)


def pick_shortlist(cands: list[dict[str, Any]], n_min: int = 5, n_max: int = 10) -> list[dict[str, Any]]:
    """满2优先，分板/行业配额，硬约束：电力/已持/已清不进主推，银行最多1。"""
    pool = [
        r
        for r in cands
        if len(r["a_hits"]) >= 2
        and r.get("value_ok")
        and ("①" in r["a_hits"] or "②" in r["a_hits"])
    ]
    pool.sort(key=lambda r: (-len(r["a_hits"]), -r["score"], r.get("pctile_60d") or 99))
    picked: list[dict[str, Any]] = []
    used_ind: set[str] = set()
    board_cap = {"main": 5, "chinext": 3, "star": 2}
    board_n: Counter[str] = Counter()
    for row in pool:
        if len(picked) >= n_max:
            break
        code = row["code"]
        if code in HELD or code in CLEARED or code in WATCH_ONLY:
            continue
        if code in OIL_WATCHED or code in OIL_LOW_REVIEW or code in FALSE_STABLE:
            continue
        if code == "603707":
            continue  # 仅对照，禁止写成买尺候选
        if is_delist(row.get("name") or "") or is_st(row.get("name") or ""):
            continue
        if (row.get("close") or 0) < 1.0:
            continue
        if row.get("c_reasons"):
            continue
        if row.get("is_power"):
            continue
        if row.get("is_broker"):
            continue
        board = row["board"]
        if board_n[board] >= board_cap.get(board, 2):
            continue
        ind = row.get("industry") or row["code"]
        if ind in used_ind:
            continue
        if row.get("is_bank"):
            # 短名单银行最多 1 且只能仅对照；本窗不占超跌主观察席
            continue
        if board == "star":
            row = dict(row)
            row["align"] = "观察·不对齐本账户开仓"
        elif board == "chinext" and not str(row.get("align", "")).startswith("仅对照"):
            row = dict(row)
            row["align"] = "可对齐"
        elif board == "main" and not str(row.get("align", "")).startswith("仅对照"):
            row = dict(row)
            row["align"] = "主板"
        extra = EXTRA_NOTES.get(code)
        if extra:
            row = dict(row)
            row["extra_note"] = extra
        picked.append(row)
        used_ind.add(ind)
        board_n[board] += 1
    # if under min, relax industry uniqueness but keep other caps
    if len(picked) < n_min:
        for row in pool:
            if len(picked) >= n_min:
                break
            if any(x["code"] == row["code"] for x in picked):
                continue
            if row["code"] in HELD or row["code"] in CLEARED or row.get("is_power") or row.get("c_reasons"):
                continue
            if row["code"] in OIL_WATCHED or row["code"] in OIL_LOW_REVIEW or row["code"] in FALSE_STABLE:
                continue
            if row.get("is_broker"):
                continue
            board = row["board"]
            if board_n[board] >= board_cap.get(board, 2):
                continue
            row = dict(row)
            row["align"] = align_label(board)
            picked.append(row)
            board_n[board] += 1
    return picked


def fetch_tencent_fundamentals(codes: list[str]) -> dict[str, dict[str, Any]]:
    """腾讯批量：昨收、TTM PE(f39)、静态PE(f53)、PB(f46)。用于覆盖新浪静态市盈率。"""
    out: dict[str, dict[str, Any]] = {}
    sess = _session()
    chunk = 60
    for i in range(0, len(codes), chunk):
        part = codes[i : i + chunk]
        ts = ",".join(tencent_symbol(c) for c in part)
        try:
            r = sess.get(f"https://qt.gtimg.cn/q={ts}", timeout=20)
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log(f"[tencent-fund] chunk {i} fail {exc}")
            continue
        for line in r.text.strip().split(";"):
            if "~" not in line:
                continue
            payload = line.split("=", 1)[1].strip('"')
            p = payload.split("~")
            if len(p) < 47:
                continue
            code = p[2]
            pe_ttm = _fnum(p[39]) if len(p) > 39 else None
            pe_lyr = _fnum(p[53]) if len(p) > 53 else None
            out[code] = {
                "name": p[1],
                "last": _fnum(p[3]),
                "prev": _fnum(p[4]),
                "open": _fnum(p[5]),
                "pe_ttm": pe_ttm,
                "pe_lyr": pe_lyr,
                "pb": _fnum(p[46]),
                "time": p[30] if len(p) > 30 else "",
            }
        time.sleep(0.05)
    log(f"[tencent-fund] n={len(out)}/{len(codes)}")
    return out


def cross_quotes(codes: list[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {c: {} for c in codes}
    # tencent batch
    ts = ",".join(tencent_symbol(c) for c in codes)
    try:
        r = _session().get(f"https://qt.gtimg.cn/q={ts}", timeout=15)
        r.raise_for_status()
        for line in r.text.strip().split(";"):
            if "~" not in line:
                continue
            payload = line.split("=", 1)[1].strip('"')
            parts = payload.split("~")
            if len(parts) < 5:
                continue
            code = parts[2]
            out.setdefault(code, {})
            out[code]["tencent_name"] = parts[1]
            out[code]["tencent_close"] = _fnum(parts[3])
            out[code]["tencent_prev"] = _fnum(parts[4])
            out[code]["tencent_time"] = parts[30] if len(parts) > 30 else ""
    except Exception as exc:  # noqa: BLE001
        log(f"[tencent] fail {exc}")
    # sina
    sl = ",".join(sina_symbol(c) for c in codes)
    try:
        r = _session().get(
            f"https://hq.sinajs.cn/list={sl}",
            headers={"Referer": "https://finance.sina.com.cn", "User-Agent": UA},
            timeout=15,
        )
        r.encoding = "gb18030"
        for line in r.text.splitlines():
            if '"' not in line:
                continue
            left, right = line.split("=", 1)
            code = left.split("_")[-1][-6:]
            payload = right.strip().strip(";").strip('"')
            parts = payload.split(",")
            if len(parts) < 4:
                continue
            out.setdefault(code, {})
            out[code]["sina_name"] = parts[0]
            out[code]["sina_close"] = _fnum(parts[3])
            out[code]["sina_prev"] = _fnum(parts[2])
            out[code]["sina_date"] = parts[30] if len(parts) > 30 else ""
    except Exception as exc:  # noqa: BLE001
        log(f"[sina] fail {exc}")
    return out


def fmt_pct(x: float | None, digits_: int = 1) -> str:
    if x is None:
        return "NA"
    return f"{x * 100:.{digits_}f}%"


def fmt_a(row: dict[str, Any]) -> str:
    bits = []
    if "①" in row["a_hits"]:
        bits.append(f"①跌幅20d={fmt_pct(row.get('ret_20d'))}/5d={fmt_pct(row.get('ret_5d'))}")
    if "②" in row["a_hits"]:
        bits.append(f"②vsMA20={fmt_pct(row.get('dev_ma20'))}")
    if "③" in row["a_hits"]:
        p = row.get("pctile_60d")
        bits.append(f"③60d分位={p:.0f}%" if p is not None else "③60d分位=NA")
    return "; ".join(bits)


def reason_line(row: dict[str, Any]) -> str:
    n = len(row["a_hits"])
    pe = row.get("pe")
    pb = row.get("pb")
    pe_s = f"{pe:.1f}" if pe is not None else "NA"
    pb_s = f"{pb:.2f}" if pb is not None else "NA"
    pctile = row.get("pctile_60d")
    pctile_s = f"{pctile:.0f}%" if pctile is not None else "NA"
    return (
        f"满A{n}；20d {fmt_pct(row.get('ret_20d'))} / vsMA20 {fmt_pct(row.get('dev_ma20'))} / "
        f"60d分位 {pctile_s}；行业{row.get('industry') or 'NA'}；PE={pe_s}/PB={pb_s}"
    )


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
        f"11/11收{close_s}/{chg_s}；距涨停约{dist_s}；"
        f"11/11高开>1%={gap_flag}（开盘相对前收{gap_n:+.2f}%，仅解释不是今开）"
    )


def quotes_agree(q: dict[str, Any], close: float | None) -> str:
    """核 11/11 收盘：优先新浪/腾讯昨收。盘中现价不得当作 asof。"""
    sina = q.get("sina_prev")
    tenc = q.get("tencent_prev")
    if sina is None:
        sina = q.get("sina_close")
    if tenc is None:
        tenc = q.get("tencent_close")
    if close is None or sina is None or tenc is None:
        return "缺失"
    if abs(sina - close) <= 0.011 and abs(tenc - close) <= 0.011:
        return "11/11收盘三源一致（昨收交叉；盘中现价≠asof）"
    return "11/11收盘不一致"


def build_reports(
    rows: list[dict[str, Any]],
    shortlist: list[dict[str, Any]],
    stats: dict[str, Any],
    quotes: dict[str, dict[str, Any]],
    out_dir: Path,
    fetch_time: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"oversold-scan-{SCAN_STAMP}.md"
    js_path = out_dir / f"oversold-scan-{SCAN_STAMP}.json"

    evening_map = {r["code"]: r for r in rows if r["code"] in EVENING_TEN}
    keep, drop, new = [], [], []
    short_codes = [r["code"] for r in shortlist]
    for code in EVENING_TEN:
        if code in short_codes:
            keep.append(code)
        else:
            rec = evening_map.get(code) or {}
            why = rec.get("drop_why") or ",".join(rec.get("c_reasons") or []) or "独立重算后未进分板/行业配额前10"
            drop.append(f"`{code} {rec.get('name') or EVENING_TEN_LABELS.get(code, '')}`（{why}）")
    for rec in shortlist:
        if rec["code"] not in EVENING_TEN:
            new.append(f"`{rec['code']} {rec['name']}`")

    board_short = Counter(r["board"] for r in shortlist)
    evening_bits = "｜".join(
        f"`{c} {EVENING_TEN_LABELS[c]}`" for c in EVENING_TEN
    )
    sec_bits = "｜".join(f"`{c} {SECONDARY_TEN_LABELS[c]}`" for c in SECONDARY_TEN)
    keep_disp = "、".join(
        f"`{c} {evening_map.get(c, {}).get('name') or EVENING_TEN_LABELS.get(c, '')}`" for c in keep
    )
    lines: list[str] = []
    lines.append(f"# 早盘全A价值超跌硬扫 · {WINDOW_DATE}")
    lines.append("")
    lines.append(
        f"> **窗口** {WINDOW_LABEL}（Asia/Shanghai）｜**price_asof** {ASOF_DEFAULT} 收盘"
        f"（窗口按未开盘口径；日K asof 停在 11/11）｜抓取开始 {fetch_time}｜"
        "价源：东财不复权日K（clist 主域 502 后全A名单回退新浪 hs_a）；"
        "短名单 11/11 收盘交叉新浪昨收 + 腾讯昨收（盘中现价只旁注，不当 asof）｜教育模拟｜"
        "**扫描 ≠ 买卖灯 ≠ 下单 ≠ 改灯**"
    )
    lines.append("")
    lines.append("## 口径")
    lines.append("")
    lines.append(
        "- **A硬 ≥1**（满2优先）：①近20日≤−12% 或 近5日≤−6%；②相对MA20≤−6%；③近60日价格分位≤40%。"
        "60日分位 = 近60根收盘中 ≤ 现价 的占比（与晚筛同口径）。"
    )
    lines.append(
        "- **B软**：PE>0；破净/低PE优先；畸高PE/PB降权；非脉冲阴跌；非ST。"
    )
    lines.append(
        "- **C排除必须逐票可核验**，禁止用「油运忌追 / 光模块忌追」整组清零。"
        f"涨停/连板/近板（11/11 官方涨停池旁证：85 涨停 / 0 跌停 / 最高连板 {NEAR_BOARD_HEIGHT_REF}＝大东方、日出东方）、"
        "已相对高（5日急弹≥+10% 或 60日分位≥70%）忌追、无量僵尸、停牌、ST、电力不进短名单、"
        "已持不占新观察、已清不加回主推前列。"
        "油运 sleeve_hot 仍 yes，但低位票须单独评估；光模块只踢涨停/近板/大涨那几只，未近板且过A不因主题删除。"
        f"**不用「今日高开>1%」作C排除**（C 按未开盘口径；{ASOF_DEFAULT} 当日高开仅作相对晚筛解释，"
        "11/12 开盘/盘中现价不当 asof、不写入 C）。"
        "停牌须有公开证据；原因不明标 UNKNOWN，不编造停牌。"
    )
    lines.append("- 创业板资格已开通 → **可对齐**。科创板入短名单必须标 **观察·不对齐本账户开仓**。银行最多 1 只且仅对照，不把第二只银行塞成强制席。")
    lines.append(
        f"- 默认建议进 **乙**（`601699 潞安环能` 若入短名单仍旁注库档丙、不自动升乙）。"
        f"必须独立用 {ASOF_DEFAULT} 收盘对沪深全A重算，禁止抄晚筛名单。"
        "LME Official 铜仍 10 Nov（11/12 未挂），不因此整组剔除工业金属。"
        "纸面规则 v3.9.2.70 SHA8 a5803743；决策闸 v0.19；v3.9.2.69 禁主题整组否决与逐票可证伪忌追仍有效。本扫不对齐改规则文件。"
    )
    lines.append("")
    lines.append("## 覆盖 / 踢出")
    lines.append("")
    lines.append(stats["coverage_line"])
    lines.append(f"- 踢出计数：{stats['kick_counts']}")
    lines.append(
        f"- 油运BK={OIL_BK} n={stats['oil_n']}（sleeve_hot=yes，**不整组踢出**；已观察不占新席："
        "`601872 招商轮船`/`600026 中远海能`/`601975 招商南油`；低位须单独评估 `000520 凤凰航运`）。"
        "光模块用代码+简称点名近板/涨停票，不整组踢 BK1136。"
        f"电力BK并集 n={stats['power_n']}（煤炭/油不是电力，不因神华叠力而开电力，也不用电力禁令抹掉煤炭票）。"
        f"{ASOF_DEFAULT} 涨停池 n={stats['zt_asof_n']}，近{stats['near_days']}个交易日涨停去重 n={stats['near_n']}，"
        f"连板高度对照任务书={NEAR_BOARD_HEIGHT_REF}，本窗涨停池 max_lbc={stats['max_lbc']}。"
    )
    lines.append(
        f"- 本窗 C 按未开盘口径：**不用「今日高开>1%」作排除**，也不把未知/已发生的 11/12 开盘写成 11/11 缺口。"
        f"若把 {ASOF_DEFAULT} 当日高开>1% 当 C，将多踢 {stats['gap_asof_n']} 只（仅解释，不作为本窗排除）。"
        "11/11 官方涨停池旁证：85 涨停 / 0 跌停 / 最高连板 4（大东方、日出东方）。"
    )
    lines.append("")
    lines.append("## 方法盲点")
    lines.append("")
    for b in stats["blindspots"]:
        lines.append(f"- {b}")
    lines.append(
        "- 现持不占新观察主推（纸面仍冻在 11/11 11:30 午盘：现金 53209.93 / 权益 102213.93 / 仓约 47.94% / 席5空；"
        "下列收盘仅旁证，不改账）："
        "`601318 中国平安` 200 收 53.41；"
        "`000429 粤高速A` 700 收 13.62（收购包只跟踪不加仓，不占新观察）；"
        "`601088 中国神华` 200 收 49.00（忌叠力·禁再开电力）；"
        "`300926 博俊科技` 700 纸面仍持、收 15.98（实盘已清 0，两本分开写；09:25 卖700 建议仍待用户，本扫不是卖单）；"
        "`603806 福斯特` 600 收 12.73（低于观察 12.88、高于失效 12.61，只观察；11:32 酌卖600 仍待用户，勿再满开主推）。"
        "已清不加回：`300059 东方财富`；`000333 美的集团`；`601006 大秦铁路`；`601166 兴业银行`。"
        "旁观不占价值席：`002736 国信证券`；`002415 海康威视` 伪稳、不升进攻。券商不进席5/6。"
        "本扫不改买卖灯。"
    )
    lines.append("")
    lines.append("## 超跌短名单（建议并乙｜5–10）")
    lines.append("")
    lines.append("| # | 代码+全称 | 板 | 昨收/相对前收 | A触发（①②③） | B软一句 | 一句理由 | 对齐 |")
    lines.append("|---|-----------|----|-----------|------|----------|------|------|")
    for i, row in enumerate(shortlist, 1):
        chg = row.get("chg_pct")
        chg_s = f"{chg:+.2f}%" if chg is not None else "NA"
        reason = reason_line(row)
        extra = row.get("extra_note")
        if extra:
            reason = reason + "；" + extra
        lines.append(
            f"| {i} | `{row['code']} {row['name']}` | {board_label(row['board'])} | "
            f"{row['close']:.2f} / {chg_s} | {fmt_a(row)} | {row['b_note']} | {reason} | {row['align']} |"
        )
    lines.append("")
    lines.append("### 分板")
    lines.append("")
    lines.append(f"- 主板：**{board_short.get('main', 0)}**")
    lines.append(f"- 创业板：**{board_short.get('chinext', 0)}**")
    lines.append(f"- 科创板：**{board_short.get('star', 0)}**")
    lines.append("")
    side = stats.get("side_notes") or {}
    if side:
        lines.append("### 分板价值旁注（不占超跌短名单名额）")
        lines.append("")
        for key, title in (("main", "主板"), ("chinext", "创业板"), ("star", "科创板")):
            items = side.get(key) or []
            if not items:
                continue
            bits = []
            for r in items:
                al = align_label(r["board"]) if key != "main" else "主板"
                bits.append(
                    f"`{r['code']} {r['name']}` A={''.join(r['a_hits'])} PE={r.get('pe'):.1f}/PB={r.get('pb'):.2f}（{al}）"
                    if r.get("pe") is not None and r.get("pb") is not None
                    else f"`{r['code']} {r['name']}`"
                )
            lines.append(f"- {title}：" + "；".join(bits))
        lines.append("")
    lines.append("## 相对昨晚晚筛十票（同一 price_asof=11/11 收盘，独立全A重算）")
    lines.append("")
    lines.append(
        "晚筛对照来源 agent `bc-4fefb39d`。本窗对沪深全A独立重算，禁止抄昨晚短名单。"
        f"晚筛十票：{evening_bits}"
    )
    lines.append("")
    lines.append("- 保留：" + (keep_disp if keep else "无"))
    lines.append("- 换出：" + ("、".join(drop) if drop else "无"))
    lines.append("- 新入：" + ("、".join(new) if new else "无"))
    lines.append("- 去留解释：" + (stats.get("vs_explain") or "见各票独立重算字段。"))
    if stats.get("hot_sleeve_note"):
        lines.append("- 热袖已剔除对照：" + stats["hot_sleeve_note"])
    if stats.get("oil_review"):
        lines.append("- 油运逐票（不整组删除）：" + stats["oil_review"])
    if stats.get("opt_review"):
        lines.append("- 光模块逐票（不整组删除）：" + stats["opt_review"])
    if stats.get("oke_note"):
        lines.append("- 欧科亿对照：" + stats["oke_note"])
    if stats.get("luan_note"):
        lines.append("- 潞安环能对照：" + stats["luan_note"])
    lines.append("")
    lines.append("### 晚筛十票独立重算交叉（禁止抄晚筛数字）")
    lines.append("")
    lines.append("| 代码 | 本窗收盘 | A触发 | 20日 | 5日 | MA20偏离 | 60日分位 | PE/PB | 去留 |")
    lines.append("|------|----------|------|------|-----|----------|----------|-------|------|")
    by_code = {r["code"]: r for r in rows}
    for code in EVENING_TEN:
        rec = by_code.get(code) or {}
        a = "".join(rec.get("a_hits") or []) or "无"
        close = rec.get("close")
        close_s = f"{close:.2f}" if isinstance(close, (int, float)) else "NA"
        pe, pb = rec.get("pe"), rec.get("pb")
        pepb = f"{pe:.2f}/{pb:.2f}" if pe is not None and pb is not None else "缺失"
        pctile = rec.get("pctile_60d")
        pctile_s = f"{pctile:.2f}" if pctile is not None else "NA"
        stay = "保留" if code in keep else "换出"
        lines.append(
            f"| `{code}` | {close_s} | {a} | {fmt_pct(rec.get('ret_20d'))} | "
            f"{fmt_pct(rec.get('ret_5d'))} | {fmt_pct(rec.get('dev_ma20'))} | {pctile_s} | {pepb} | {stay} |"
        )
    lines.append("")
    lines.append(
        "- 次对照（11/11 盘前十票，asof=11/10，已过时仅旁注）："
        f"{sec_bits}。"
        + (stats.get("secondary_note") or "")
    )
    lines.append("")
    lines.append("## 核价（东财 / 新浪 / 腾讯）")
    lines.append("")
    lines.append("| 代码 | 日K 11/11收 | 新浪昨收 | 腾讯昨收 | 是否一致 | 盘中现价(≠asof) |")
    lines.append("|------|-------------|----------|----------|----------|-----------------|")
    for row in shortlist:
        q = quotes.get(row["code"], {})
        sina_p = q.get("sina_prev")
        tenc_p = q.get("tencent_prev")
        sina_s = f"{sina_p:.2f}" if sina_p is not None else "NA"
        tenc_s = f"{tenc_p:.2f}" if tenc_p is not None else "NA"
        live_s = q.get("tencent_close")
        live = f"{live_s:.2f}" if live_s is not None else "NA"
        agree = quotes_agree(q, row.get("close"))
        lines.append(
            f"| `{row['code']}` | {row['close']:.2f} | {sina_s} | {tenc_s} | {agree} | {live} |"
        )
    lines.append("")
    lines.append("扫描≠买卖灯｜建议默认进乙｜教育模拟，非投资建议。")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "window": f"{WINDOW_LABEL} Asia/Shanghai",
        "price_asof": ASOF_DEFAULT,
        "fetched_at": fetch_time,
        "education_only": True,
        "scan_is_not_trade_signal": True,
        "paper_rules": "v3.9.2.70 SHA8 a5803743",
        "decision_gate": "v0.19",
        "coverage": stats["coverage"],
        "kick_counts": stats["kick_counts"],
        "blindspots": stats["blindspots"],
        "vs_evening": {
            "keep": keep,
            "drop": drop,
            "new": new,
            "evening_ten": EVENING_TEN,
            "explain": stats.get("vs_explain"),
        },
        "vs_secondary": {
            "secondary_ten": SECONDARY_TEN,
            "note": stats.get("secondary_note"),
            "asof": "2026-11-10",
        },
        "oil_review": stats.get("oil_review"),
        "opt_review": stats.get("opt_review"),
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
                "note": (reason_line(r) + ("；" + r["extra_note"] if r.get("extra_note") else "")),
                "b_note": r.get("b_note"),
                "align": r["align"],
                "pe_src": r.get("pe_src"),
                "quotes": quotes.get(r["code"], {}),
                "quotes_agree": quotes_agree(quotes.get(r["code"], {}), r.get("close")),
            }
            for r in shortlist
        ],
        "held_not_new": HELD,
        "cleared_not_back": CLEARED,
        "oil_watched_not_new": OIL_WATCHED,
    }
    js_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, js_path


def run(cache_dir: Path, out_dirs: list[Path], workers: int) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    stamp_path = cache_dir / "fetch_started.txt"
    if stamp_path.exists():
        fetch_time = stamp_path.read_text(encoding="utf-8").strip()
    else:
        fetch_time = now_shanghai().strftime("%Y-%m-%d %H:%M:%S UTC+08:00")
        stamp_path.write_text(fetch_time, encoding="utf-8")

    clist = fetch_clist_all(cache_dir / "clist.json")
    clist_src = (clist[0].get("_src") if clist else "") or "eastmoney"
    log(f"[clist] source={clist_src} n={len(clist)}")
    bk_cache = cache_dir / "bk_codes.json"
    oil_codes: set[str] = set()
    power_codes: set[str] = set()
    if bk_cache.exists():
        bk_payload = json.loads(bk_cache.read_text(encoding="utf-8"))
        oil_codes = set(bk_payload.get("oil", []))
        power_codes = set(bk_payload.get("power", []))
        log(f"[cache] bk oil={len(oil_codes)} power={len(power_codes)}")
    if clist_src != "sina" and (len(oil_codes) < 10 or not (50 <= len(power_codes) <= 200)):
        try:
            oil_codes = fetch_bk_codes(OIL_BK)
            power_codes = set()
            for bk in POWER_BKS:
                power_codes |= fetch_bk_codes(bk)
            bk_cache.write_text(
                json.dumps({"oil": sorted(oil_codes), "power": sorted(power_codes)}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            log(f"[bk] fetch failed {exc}; keyword fallback")
    elif clist_src == "sina":
        log("[bk] skip eastmoney BK clist (universe already on sina fallback)")
    oil_codes = oil_sleeve_codes(oil_codes, [{"code": x.get("f12"), "name": x.get("f14")} for x in clist])

    zt_cache = cache_dir / "zt_pools.json"
    if zt_cache.exists():
        zt_by_date = json.loads(zt_cache.read_text(encoding="utf-8"))
    else:
        zt_by_date = {}
        for d in trading_days_back(ASOF_DEFAULT, 8):
            pool = fetch_zt_pool(d)
            if pool:
                zt_by_date[d] = pool
        zt_cache.write_text(json.dumps(zt_by_date, ensure_ascii=False), encoding="utf-8")

    asof_key = ASOF_DEFAULT.replace("-", "")
    zt_asof = {str(x.get("c")): x for x in zt_by_date.get(asof_key, [])}
    near_dates = sorted(zt_by_date.keys(), reverse=True)
    # last 5 sessions with non-empty pools
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
    tencent_fund = fetch_tencent_fundamentals(codes)

    kick: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    board_scan: Counter[str] = Counter()
    board_a: Counter[str] = Counter()
    a_ge1 = a_ge2 = k_ok = 0

    for item in clist:
        code = str(item["f12"])
        name = str(item.get("f14") or "")
        board = classify_board(code) or ""
        board_scan[board] += 1
        close = _fnum(item.get("f2"))
        chg = _fnum(item.get("f3"))
        pe = _fnum(item.get("f115"))
        if pe is None or pe <= 0:
            pe = _fnum(item.get("f9"))
        pb = _fnum(item.get("f23"))
        tf = tencent_fund.get(code) or {}
        # 腾讯 f39=TTM（可负）；新浪 per 多为静态。价值门用 TTM。
        if tf.get("pe_ttm") is not None:
            pe = tf["pe_ttm"]
        if tf.get("pb") is not None:
            pb = tf["pb"]
        rec_pe_src = "tencent_ttm" if tf.get("pe_ttm") is not None else "sina_static"
        turnover = _fnum(item.get("f8"))
        amount = _fnum(item.get("f6"))
        industry = industry_of(item)
        bars = klines.get(code)
        rec: dict[str, Any] = {
            "code": code,
            "name": name,
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
        }
        if is_st(name):
            rec["c_reasons"].append("ST")
            kick["ST"] += 1
        if is_delist(name):
            rec["c_reasons"].append("退市整理")
            kick["退市整理"] += 1
        if close is None:
            if not is_st(name) and not is_delist(name):
                rec["c_reasons"].append("停牌或无价")
                kick["停牌或无价"] += 1
            rows.append(rec)
            continue
        if not bars or len(bars) < 21 or str(bars[-1].get("date")) != ASOF_DEFAULT:
            rec["c_reasons"].append("K线空")
            kick["K线空"] += 1
            rows.append(rec)
            continue
        k_ok += 1
        m = a_metrics(bars)
        if not m:
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
        hits = detect_a_hits(m)
        rec["a_hits"] = hits
        flags = kline_limit_flags(code, name, bars, lookback=5)
        rec["pulse"] = flags["pulse"]
        rec["near_board_k"] = flags["near_board"]
        rec["limit_streak"] = flags["limit_streak"]
        rec["dist_to_limit"] = dist_to_limit_pct(m["close"], m.get("prev_close"), code, name)
        rec["sleeve_oil"] = code in oil_codes
        rec["sleeve_opt"] = is_opt_mod(code, name) or code in NAMED_OPT_CHASE
        rec["too_high"] = too_high(m)
        rec["near_limit"] = near_limit_asof(m["pct_asof"], code, name)

        if hits:
            a_ge1 += 1
            board_a[board] += 1
            if len(hits) >= 2:
                a_ge2 += 1

        # C 必须逐票可核验。禁止用「油运忌追 / 光模块忌追」整组清零。
        # 不用「今日高开>1%」作 C（WINDOW_DATE 开盘尚未发生）。
        if code in zt_asof:
            rec["c_reasons"].append("涨停池残续")
            kick["涨停池残续"] += 1
        if code in lianban_codes or flags["limit_streak"] >= 2:
            rec["c_reasons"].append("连板")
            kick["连板"] += 1
        if is_limit_up(m["pct_asof"], code, name):
            rec["c_reasons"].append("涨停")
            kick["涨停"] += 1
        elif rec["near_limit"] or flags["near_board"] or code in near_codes:
            rec["c_reasons"].append("近板忌追")
            kick["近板忌追"] += 1
        if hits and rec["too_high"]:
            rec["c_reasons"].append("已相对高忌追")
            kick["已相对高忌追"] += 1
        if code in NAMED_OPT_CHASE and m["pct_asof"] >= 5.0 and "涨停" not in rec["c_reasons"]:
            rec["c_reasons"].append("点名大涨忌追")
            kick["点名大涨忌追"] += 1
        amt20 = m["amt20"]
        if (turnover is not None and turnover < 0.15 and (amount or 0) < 8_000_000) or amt20 < 3_000_000:
            rec["c_reasons"].append("无量僵尸")
            kick["无量僵尸"] += 1

        rec["is_power"] = is_power(code, name, industry, power_codes)
        rec["is_bank"] = is_bank(industry, name)
        rec["is_broker"] = is_broker(industry, name)
        rec["is_pv"] = is_pv(industry, name)
        rec["value_ok"] = value_ok(pe, pb, close=rec.get("close"), name=name)
        rec["b_note"] = b_note(pe, pb, rec.get("pulse") or False)
        rec["score"] = score_row(rec)
        rec["gap_asof_gt1"] = (m["gap_asof"] or 0) > 0.01
        if rec["is_power"]:
            kick["电力"] += 1
        rows.append(rec)

    gap_n = sum(1 for r in rows if r.get("gap_asof_gt1"))
    passed_a = [r for r in rows if r["a_hits"]]
    passed_c = [
        r
        for r in passed_a
        if not r["c_reasons"] and not r.get("is_power")
    ]
    # 电力：过C统计里晚筛是单独踢出；短名单再滤。这里过C不含电力。
    value_q = [r for r in passed_c if r.get("value_ok") and len(r["a_hits"]) >= 2]

    # annotate evening ten drop reasons for report
    for r in rows:
        if r["code"] in EVENING_TEN or r["code"] in {"688308", "601699", "000520"}:
            if r.get("is_power"):
                r["drop_why"] = "电力（发电禁再开，不是煤炭/油整组）"
            elif r["c_reasons"]:
                r["drop_why"] = ",".join(r["c_reasons"])
            elif not r.get("value_ok"):
                r["drop_why"] = "价值质量未过（PE/PB）"
            elif "②" not in (r.get("a_hits") or []) and len(r.get("a_hits") or []) < 3:
                r["drop_why"] = (
                    f"仅{''.join(r.get('a_hits') or [])}（②未过，MA20={fmt_pct(r.get('dev_ma20'))}），"
                    "不改②定义保席"
                )
            elif len(r.get("a_hits") or []) < 2:
                r["drop_why"] = f"A={''.join(r.get('a_hits') or []) or '无'}"
            elif r["code"] in OIL_LOW_REVIEW:
                r["drop_why"] = EXTRA_NOTES.get(r["code"], "油运低位单独评估，不进前列")
            else:
                extra = EXTRA_NOTES.get(r["code"], "")
                r["drop_why"] = "满A且过B/C，分板/行业配额或价值排序未进前10" + (
                    f"；{extra}" if extra else ""
                )

    shortlist = pick_shortlist(value_q, n_min=5, n_max=10)
    taken = {r["code"] for r in shortlist}
    side_notes: dict[str, list[dict[str, Any]]] = {"main": [], "chinext": [], "star": []}
    for r in sorted(value_q, key=lambda x: (-len(x["a_hits"]), -(x.get("score") or 0))):
        if r["code"] in taken or r["code"] in HELD or r["code"] in CLEARED or r.get("is_bank"):
            continue
        if r["code"] in OIL_WATCHED or r["code"] in OIL_LOW_REVIEW or r["code"] in FALSE_STABLE:
            continue
        if r.get("is_broker"):
            continue
        b = r["board"]
        if b in side_notes and len(side_notes[b]) < 5:
            side_notes[b].append(r)

    by_code = {r["code"]: r for r in rows}
    sec_bits_live = []
    for c in SECONDARY_TEN:
        rec = by_code.get(c)
        if not rec:
            sec_bits_live.append(f"`{c}`缺数据")
            continue
        a = "".join(rec.get("a_hits") or []) or "无"
        extra = ""
        if rec.get("gap_asof_gt1"):
            extra = f"；{ASOF_DEFAULT[5:].replace('-', '/')}曾高开>1%（可解释去留，本窗不作C）"
        if rec.get("c_reasons"):
            extra += "；本窗C=" + ",".join(rec["c_reasons"])
        if rec["code"] in taken:
            extra += "；本窗保留/新入短名单"
        elif rec.get("value_ok") and len(rec.get("a_hits") or []) >= 2 and not rec.get("c_reasons") and not rec.get("is_power"):
            extra += "；满A过B/C未进配额前10"
        sec_bits_live.append(f"`{c}`A={a}{extra}")

    hot_bits = []
    for r in rows:
        if any(k in (r.get("name") or "") for k in HOT_SLEEVE_WATCH_NAMES):
            a = "".join(r.get("a_hits") or []) or "无"
            why = ",".join(r.get("c_reasons") or []) or (
                "热袖/高波动，忌追杀反弹，不进短名单前列"
            )
            hot_bits.append(
                f"`{r['code']} {r['name']}` A={a} C={why}；晚筛已剔除，本窗独立重算仍不进前列"
            )

    def _review_line(code: str, fallback_name: str, extra: str = "") -> str:
        rec = by_code.get(code) or {}
        name = rec.get("name") or fallback_name
        a = "".join(rec.get("a_hits") or []) or "无"
        fact = chase_fact(rec) if rec else "缺K"
        cwhy = ",".join(rec.get("c_reasons") or []) or "无C"
        stay = "短名单" if code in taken else "不进前列"
        bits = [f"`{code} {name}` A={a}", fact, f"C={cwhy}", stay]
        if extra:
            bits.append(extra)
        return "；".join(bits)

    oil_bits = [
        _review_line("601872", "招商轮船", "已观察不占新席；11/11旁证收16.25/+2.52%/开+0.06%/距涨停约7.32%；微回调≠抄底"),
        _review_line("600026", "中远海能", "已观察不占新席；11/11旁证收16.96/+1.68%"),
        _review_line("601975", "招商南油", "已观察不占新席；11/11旁证收3.55/+2.60%"),
        _review_line(
            "000520",
            "凤凰航运",
            "低位须单独评估；11/11旁证收2.81/-5.07%/开-2.70%/距涨停约16.01%；下跌≠抄底；腾讯TTM PE/PB约49/6.25畸高；无公司订单/UKMTO新锚不进前列；过A也不默删油运袖；复评条件=有对得上UKMTO文本的公司订单或新锚且估值不再畸高",
        ),
    ]
    oil_pass_a = [
        r for r in rows
        if r.get("sleeve_oil") and r.get("a_hits") and r["code"] not in {"601872", "600026", "601975", "000520"}
    ]
    oil_pass_a.sort(key=lambda x: (-len(x["a_hits"]), -(x.get("score") or 0)))
    for r in oil_pass_a[:8]:
        oil_bits.append(_review_line(r["code"], r.get("name") or "", "油运过A逐票，不因袖标签删除"))

    opt_bits = []
    for code, nm in NAMED_OPT_CHASE.items():
        rec = by_code.get(code) or {}
        extra = "点名近板/涨停/大涨忌追；未近板且过A不得因光模块主题删除"
        opt_bits.append(_review_line(code, nm, extra))
    other_opt = [
        r for r in rows
        if r.get("sleeve_opt") and r["code"] not in NAMED_OPT_CHASE and r.get("a_hits") and not r.get("c_reasons")
    ]
    other_opt.sort(key=lambda x: (-len(x["a_hits"]), -(x.get("score") or 0)))
    for r in other_opt[:6]:
        opt_bits.append(_review_line(r["code"], r.get("name") or "", "未近板且过A，不因光模块主题删除"))

    oke = by_code.get("688308") or {}
    oke_note = _review_line(
        "688308",
        "欧科亿",
        "晚筛已因过高换出；独立重算过A也不得无解释塞回前列；科创观察·不对齐本账户开仓",
    )
    luan = by_code.get("601699") or {}
    luan_a = "".join(luan.get("a_hits") or []) or "无"
    luan_note = (
        f"`601699 潞安环能` 本窗A={luan_a}；{chase_fact(luan) if luan else '缺K'}；"
        f"C={','.join(luan.get('c_reasons') or []) or '无C'}；"
        "仍过硬门则可写入并旁注库档丙、不自动升乙；煤炭不是电力，不用发电禁令抹掉且不留注。"
        + ("本窗入短名单。" if "601699" in taken else "本窗未进短名单前列。")
    )

    keep_codes = [r["code"] for r in shortlist if r["code"] in EVENING_TEN]
    drop_codes = [c for c in EVENING_TEN if c not in keep_codes]
    explain_bits = [
        "对照昨晚晚筛十票（agent bc-4fefb39d，同一 price_asof=11/11），本窗全A独立重算，禁止抄名单。",
        f"C 按未开盘口径，未把今日高开>1%写入C；{ASOF_DEFAULT} 当日高开>1%仅作相对晚筛解释；核价时虽已开盘，11/12 现价不当 asof、不写入 C。",
        "LME Official 铜仍 10 Nov（11/12 未挂），不因此整组剔除工业金属；`600362` 去留只看本窗 A/B/C。",
        "UKMTO 最高仍 202-26（不是沉船）；Hormuz 仍 Restricted 未重开；2026-11-12 08:00 新浪 WTI 86.226 / Brent 92.423 vs 11/11 20:59：-1.260% / -0.877%，无新≥3%大动。微回调≠抄底油运，但低位票须逐票评估、禁止整组默删。",
    ]
    for c in drop_codes:
        rec = by_code.get(c) or {}
        name = rec.get("name") or EVENING_TEN_LABELS.get(c, "")
        explain_bits.append(f"`{c} {name}` 换出：{rec.get('drop_why') or '未进前10'}。")
    for r in shortlist:
        if r["code"] not in EVENING_TEN:
            explain_bits.append(
                f"`{r['code']} {r['name']}` 新入：满A{len(r['a_hits'])}、过B/C，分板/行业配额入席。"
            )
    if "601699" in keep_codes:
        explain_bits.append(
            "`601699 潞安环能` 独立重算仍过门，写入短名单但库档仍丙、不自动升乙；与神华同属煤炭链、忌叠力；煤炭不是电力。"
        )
    if "600938" in keep_codes:
        explain_bits.append("`600938 中国海油` 油气生产不是油运忌追袖，油气链偏弱只观察。")
    for code in ("603808", "301219"):
        rec = by_code.get(code) or {}
        hits = rec.get("a_hits") or []
        if hits and "②" not in hits:
            explain_bits.append(
                f"`{code} {rec.get('name') or ''}` 本窗A={''.join(hits)}，MA20偏离={fmt_pct(rec.get('dev_ma20'))}，"
                "未改②定义去保席；若仅①③如实写。"
            )

    coverage = {
        "scanned": len(clist),
        "boards": dict(board_scan),
        "k_valid": k_ok,
        "pass_a": a_ge1,
        "pass_a_boards": dict(board_a),
        "pass_a2": a_ge2,
        "pass_c": len(passed_c),
        "value_quality": len(value_q),
        "shortlist": len(shortlist),
    }
    coverage_line = (
        f"- 扫描 {coverage['scanned']}（主板 {board_scan.get('main', 0)} / 创业 {board_scan.get('chinext', 0)} / "
        f"科创 {board_scan.get('star', 0)}）→ K线有效 {k_ok} → 过A {a_ge1} "
        f"（主板 {board_a.get('main', 0)} / 创业 {board_a.get('chinext', 0)} / 科创 {board_a.get('star', 0)}；"
        f"满2 {a_ge2}）→ 过C {len(passed_c)} → 价值质量(满2且PE/PB) {len(value_q)} → 短名单 **{len(shortlist)}**。"
    )
    halt_n = kick.get("停牌或无价", 0) + kick.get("退市整理", 0)
    kline_empty = kick.get("K线空", 0)
    blindspots = [
        "不复权日K（fqt=0）；A③单独过门很宽，短名单只从满2条A（且至少含①或②）且过 B/C 的票里按分板/行业配额取 5–10，不用仅③票凑数。",
        "未全量核验立案/停牌全文；无价票多为退市整理/长期停牌/已吸收合并，不以假收盘补齐；停牌原因不明标 UNKNOWN，不编造。",
        "东财 push2 主域 502；clist 优先东财镜像，失败则回退新浪 hs_a（剔北交所），日K 优先东财不复权、失败回退腾讯不复权。失败票计入 K线空，不编造。",
        "油运/光模块不整组踢出；近板/涨停/5日急弹≥+10% 按票踢。光模块点名表可能漏侧链。",
        "60日分位用近60根收盘 ≤ 现价 占比；晚筛十票用本窗独立重算交叉，禁止抄晚筛数字。",
        f"clist 源={clist_src}；无 {ASOF_DEFAULT} 收盘 {halt_n}（退市/停牌/ST 无价，不计入 K 线 API 失败）；K线空 {kline_empty}。新浪回退时行业字段缺失，电力识别靠简称关键词+已知点名，可能漏发电名，短名单仍禁电力。",
        f"窗口按未开盘口径写 C（不用今日高开>1%）。日K 拉取耗时长，核价时已开盘，故 11/11 收盘用新浪/腾讯**昨收**交叉，盘中现价只旁注。",
        "PE 价值门用腾讯 TTM（qt 字段 39），不用新浪静态市盈率；TTM≤0 或 >40 记价值未过，不编造。",
        "价值质量要求 PE∈[5,40]、PB∈[0.4,4]、现价≥1，退市整理不进短名单；短名单排序把低PE/破净权重大于单边暴跌。畸高PE/PB降权，不排短名单最前。",
        "本窗对沪深全A逐只拉不复权日K；相对晚筛的换入/换出来自独立重算，不是抄名单。",
    ]
    stats = {
        "coverage": coverage,
        "coverage_line": coverage_line,
        "kick_counts": dict(kick),
        "oil_n": len(oil_codes),
        "power_n": len(power_codes),
        "zt_asof_n": len(zt_asof),
        "near_n": len(near_codes),
        "near_days": len(session_dates),
        "max_lbc": max_lbc,
        "gap_asof_n": gap_n,
        "blindspots": blindspots,
        "secondary_note": "本窗旁注：" + "；".join(sec_bits_live[:10]) + "。",
        "side_notes": side_notes,
        "vs_explain": "".join(explain_bits),
        "hot_sleeve_note": "；".join(hot_bits) if hot_bits else "未在全A名单中解析到万辰集团/联讯仪器简称。",
        "oil_review": "；".join(oil_bits),
        "opt_review": "；".join(opt_bits),
        "oke_note": oke_note,
        "luan_note": luan_note,
    }

    quotes = cross_quotes([r["code"] for r in shortlist])
    # sanity: flag mismatches
    for r in shortlist:
        q = quotes.get(r["code"], {})
        for src in ("sina_prev", "tencent_prev"):
            v = q.get(src)
            if v is not None and abs(v - r["close"]) > 0.011:
                log(f"[quote-mismatch] {r['code']} kline={r['close']} {src}={v}")

    written: list[Path] = []
    for d in out_dirs:
        md, js = build_reports(rows, shortlist, stats, quotes, d, fetch_time)
        written.extend([md, js])
        log(f"[write] {md}")
        log(f"[write] {js}")

    # also dump top candidates for audit
    audit = [
        {
            "code": r["code"],
            "name": r["name"],
            "board": r["board"],
            "close": r["close"],
            "a_hits": r["a_hits"],
            "score": round(r.get("score") or 0, 2),
            "pe": r.get("pe"),
            "pb": r.get("pb"),
            "industry": r.get("industry"),
            "c_reasons": r.get("c_reasons"),
            "ret_20d": r.get("ret_20d"),
            "dev_ma20": r.get("dev_ma20"),
            "pctile_60d": r.get("pctile_60d"),
        }
        for r in sorted(value_q, key=lambda x: (-len(x["a_hits"]), -(x.get("score") or 0)))[:80]
    ]
    (cache_dir / "top80.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (cache_dir / "shortlist_preview.json").write_text(
        json.dumps([r["code"] + " " + r["name"] + " " + "".join(r["a_hits"]) for r in shortlist], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log("SHORTLIST:")
    for i, r in enumerate(shortlist, 1):
        log(f"  {i}. {r['code']} {r['name']} {r['board']} A={''.join(r['a_hits'])} pe={r.get('pe')} pb={r.get('pb')} {r.get('industry')}")
    log("done files: " + ", ".join(str(p) for p in written))


def main() -> int:
    parser = argparse.ArgumentParser(description="沪深全A价值超跌硬扫")
    parser.add_argument("--asof", default=ASOF_DEFAULT)
    parser.add_argument("--cache", type=Path, default=Path("cache/oversold-20261112"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument(
        "--out",
        type=Path,
        nargs="+",
        default=[
            Path("."),
            Path("artifacts/morning-2026-11-12"),
            Path("/opt/cursor/artifacts"),
        ],
    )
    args = parser.parse_args()
    globals()["ASOF_DEFAULT"] = args.asof
    run(args.cache, args.out, args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
