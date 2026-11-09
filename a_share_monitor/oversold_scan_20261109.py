#!/usr/bin/env python3
"""全A价值超跌硬扫（教育模拟，扫描≠买卖灯）。

窗口：2026-11-09 周一盘前；price_asof=2026-11-06 收盘。
数据源：东财 clist + 日K；短名单报价新浪 hq + 腾讯 qt 交叉核价。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PRICE_ASOF = "2026-11-06"
WINDOW_DATE = "2026-11-09"
KLINE_END = "20261106"
TZ_CN = timezone(timedelta(hours=8))

CACHE_DIR = Path("/tmp/oversold-scan-20261109")
OUT_MD = Path("oversold-scan-20261109.md")
OUT_JSON = Path("oversold-scan-20261109.json")

HELD = {
    "601318": "中国平安",
    "000429": "粤高速A",
    "601088": "中国神华",
    "300926": "博俊科技",
}
CLEARED = {
    "300059": "东方财富",
    "000333": "美的集团",
    "601006": "大秦铁路",
    "601166": "兴业银行",
}
WATCH_ONLY = {"002736": "国信证券"}
FRIDAY_SHORTLIST = [
    "601229",
    "601699",
    "600736",
    "000906",
    "688275",
    "688379",
    "300611",
    "301305",
    "301223",
]
USER_NAMED_YI = {
    "600567",
    "600546",
    "600938",
    "301563",
    "300839",
    "688613",
    "688519",
}

# 忌追袖：油运续 + 光模块（代码兜底；概念成分会再并入）
OIL_SHIP_CODES = {
    "601872",  # 招商轮船
    "600026",  # 中远海能
    "601975",  # 招商南油
    "600428",  # 中远海特
    "601083",  # 锦江航运
    "603167",  # 渤海轮渡
    "002320",  # 海峡股份
    "603565",  # 中谷物流
    "601919",  # 中远海控（集运，袖热易传染，一并忌追）
    "601866",  # 中远海发
    "600798",  # 宁波海运
    "001326",  # 联域股份? skip if wrong — filtered by concept
    "603209",  # 兴通股份
    "001975",
}
OPTICAL_MODULE_CODES = {
    "300308",  # 中际旭创
    "300502",  # 新易盛
    "300394",  # 天孚通信
    "688498",  # 源杰科技
    "002281",  # 光迅科技
    "603083",  # 剑桥科技
    "688205",  # 德科立
    "000988",  # 华工科技
    "300570",  # 太辰光
    "300548",  # 长芯博创
    "301191",  # 菲菱科思
    "301205",  # 联特科技
    "300620",  # 光库科技
    "688048",  # 长光华芯
    "688313",  # 仕佳光子
    "688635",  # 长进光子
    "688195",  # 腾景科技
    "688143",  # 长盈通
}
OPTICAL_NAME_KEYS = (
    "旭创",
    "易盛",
    "天孚",
    "光迅",
    "太辰光",
    "源杰",
    "德科立",
    "剑桥科技",
    "光库",
    "博创",
    "联特科技",
    "仕佳光子",
    "长进光子",
    "长光华芯",
    "腾景科技",
    "长盈通",
)

POWER_INDUSTRY_EXACT = {
    "电力",
    "电力Ⅱ",
    "火力发电",
    "水力发电",
    "核力发电",
    "热电",
    "发电",
    "电网",
    "电力生产",
    "电力供应",
    "公用事业",
    "公用事业Ⅱ",
}
POWER_NAME_RE = re.compile(r"(电力|水电|火电|核电|电网|热电)$")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def now_cn() -> str:
    return datetime.now(TZ_CN).strftime("%Y-%m-%d %H:%M:%S %Z")


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=32))
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept": "*/*",
            "Referer": "https://quote.eastmoney.com/",
        }
    )
    return s


def to_float(v: Any) -> float | None:
    if v is None or v == "" or v == "-" or v == "--":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def board_of(code: str) -> str | None:
    if code.startswith("688"):
        return "科创板"
    if code.startswith(("300", "301")):
        return "创业板"
    if code.startswith(("60", "000", "001", "002", "003")):
        return "主板"
    return None


def secid_of(code: str, market: int | None = None) -> str:
    if market in (0, 1):
        return f"{market}.{code}"
    if code.startswith(("6", "9")):
        return f"1.{code}"
    return f"0.{code}"


def sina_symbol(code: str) -> str:
    return ("sh" if code.startswith(("6", "9")) else "sz") + code


def is_st(name: str) -> bool:
    n = (name or "").upper()
    return "ST" in n


def is_power_stock(name: str, industry: str | None) -> bool:
    """电力股=发电/供电公用事业，不含电力设备、电网设备。"""
    ind = industry or ""
    if ind in POWER_INDUSTRY_EXACT:
        return True
    if ind == "电力" or ind.startswith("电力"):
        return True
    if any(k in ind for k in ("火力发电", "水力发电", "核力发电", "光伏发电", "风力发电", "热电")):
        if "设备" in ind:
            return False
        return True
    return False


def is_bank(industry: str | None, name: str) -> bool:
    ind = industry or ""
    if "银行" in ind or (name or "").endswith("银行"):
        return True
    return False


def fetch_json(s: requests.Session, url: str, params: dict | None = None, timeout: int = 20) -> dict | None:
    try:
        r = s.get(url, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def fetch_clist_all(s: requests.Session) -> tuple[list[dict], dict]:
    """沪深全A：主板+创业板+科创板。分页拉东财 clist。"""
    hosts = [
        "https://82.push2.eastmoney.com/api/qt/clist/get",
        "https://88.push2.eastmoney.com/api/qt/clist/get",
        "https://43.push2.eastmoney.com/api/qt/clist/get",
        "https://push2.eastmoney.com/api/qt/clist/get",
    ]
    fields = ",".join(
        [
            "f2",
            "f3",
            "f5",
            "f6",
            "f8",
            "f9",
            "f10",
            "f12",
            "f13",
            "f14",
            "f18",
            "f20",
            "f23",
            "f24",
            "f25",
            "f100",
            "f109",
            "f114",
            "f115",
        ]
    )
    fs = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
    pz = 100
    rows: list[dict] = []
    meta = {"pages_ok": 0, "pages_fail": 0, "total_reported": None, "host": None}
    pn = 1
    total = None
    while True:
        params = {
            "pn": pn,
            "pz": pz,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f12",
            "fs": fs,
            "fields": fields,
        }
        data = None
        host_used = None
        for host in hosts:
            data = fetch_json(s, host, params)
            if data and data.get("data"):
                host_used = host
                break
            time.sleep(0.4)
        if not data or not data.get("data"):
            meta["pages_fail"] += 1
            break
        block = data["data"]
        total = block.get("total")
        meta["total_reported"] = total
        meta["host"] = host_used
        diff = block.get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        if not diff:
            break
        rows.extend(diff)
        meta["pages_ok"] += 1
        print(f"[clist] page {pn} +{len(diff)} cumulative={len(rows)} total={total}", flush=True)
        if total is not None and len(rows) >= int(total):
            break
        if len(diff) < pz:
            break
        pn += 1
        time.sleep(0.12)
    return rows, meta


def fetch_concept_codes(s: requests.Session, keyword: str) -> tuple[str | None, set[str]]:
    """在概念板块里找名称含 keyword 的 BK，再拉成分代码。"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 100,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:90+t:3+f:!50",
        "fields": "f12,f14",
    }
    bk = None
    # paginate a few pages of concepts
    for pn in range(1, 12):
        params["pn"] = pn
        data = fetch_json(s, url, params)
        time.sleep(0.15)
        if not data or not data.get("data"):
            break
        diff = data["data"].get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        if not diff:
            break
        for d in diff:
            name = str(d.get("f14") or "")
            code = str(d.get("f12") or "")
            if keyword in name and code.startswith("BK"):
                bk = code
                break
        if bk:
            break
    if not bk:
        return None, set()
    codes: set[str] = set()
    for pn in range(1, 40):
        cparams = {
            "pn": pn,
            "pz": 100,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f12",
            "fs": f"b:{bk}",
            "fields": "f12,f14",
        }
        data = fetch_json(s, url, cparams)
        time.sleep(0.12)
        if not data or not data.get("data"):
            break
        diff = data["data"].get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        if not diff:
            break
        for d in diff:
            c = str(d.get("f12") or "")
            if len(c) == 6:
                codes.add(c)
        if len(diff) < 100:
            break
    return bk, codes


def fetch_zt_pool(s: requests.Session, yyyymmdd: str) -> list[dict]:
    url = "https://push2ex.eastmoney.com/getTopicZTPool"
    params = {
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "dpt": "wz.ztzt",
        "Pageindex": 0,
        "pagesize": 500,
        "sort": "zdp:desc",
        "date": yyyymmdd,
    }
    data = fetch_json(s, url, params, timeout=25)
    if not data or not data.get("data"):
        return []
    pool = data["data"].get("pool") or []
    return pool


def parse_kline_row(line: str) -> dict | None:
    p = (line or "").split(",")
    if len(p) < 11:
        return None
    close = to_float(p[2])
    if close is None or close <= 0:
        return None
    return {
        "date": p[0],
        "open": to_float(p[1]),
        "close": close,
        "high": to_float(p[3]),
        "low": to_float(p[4]),
        "volume": to_float(p[5]),
        "amount": to_float(p[6]),
        "pct": to_float(p[8]),
        "turnover": to_float(p[10]),
    }


def fetch_kline(s: requests.Session, secid: str) -> list[dict]:
    hosts = [
        "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "https://92.push2his.eastmoney.com/api/qt/stock/kline/get",
    ]
    params = {
        "secid": secid,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": 101,
        "fqt": 0,
        "end": KLINE_END,
        "lmt": 80,
    }
    for attempt in range(4):
        host = hosts[attempt % len(hosts)]
        try:
            r = s.get(host, params=params, timeout=18)
            if r.status_code != 200:
                time.sleep(0.4 + attempt * 0.4)
                continue
            payload = r.json()
            klines = ((payload or {}).get("data") or {}).get("klines") or []
            rows = []
            for line in klines:
                row = parse_kline_row(line)
                if row:
                    rows.append(row)
            # keep bars up to asof
            rows = [x for x in rows if x["date"] <= PRICE_ASOF]
            return rows
        except Exception:
            time.sleep(0.5 + attempt * 0.5)
    return []


def metrics_from_bars(bars: list[dict]) -> dict:
    out = {
        "n_bars": len(bars),
        "k_asof": bars[-1]["date"] if bars else None,
        "k_close": bars[-1]["close"] if bars else None,
        "ret_5d": None,
        "ret_20d": None,
        "dev_ma20": None,
        "pctile_60d": None,
        "ma20": None,
        "max_1d_drop_5d": None,
        "max_1d_drop_20d": None,
        "pulse": None,
        "limit_up_5d": False,
        "avg_turnover_5d": None,
        "avg_amount_5d": None,
    }
    if len(bars) < 6:
        return out
    closes = [b["close"] for b in bars]
    pcts = [b.get("pct") for b in bars]
    c = closes[-1]

    def ret(n: int) -> float | None:
        if len(closes) > n and closes[-(n + 1)] > 0:
            return c / closes[-(n + 1)] - 1.0
        return None

    out["ret_5d"] = ret(5)
    out["ret_20d"] = ret(20)

    if len(closes) >= 20:
        ma20 = sum(closes[-20:]) / 20.0
        out["ma20"] = ma20
        if ma20 > 0:
            out["dev_ma20"] = c / ma20 - 1.0

    if len(closes) >= 60:
        window = closes[-60:]
        out["pctile_60d"] = sum(1 for x in window if x <= c) / len(window)
    elif len(closes) >= 20:
        window = closes
        out["pctile_60d"] = None  # 不足60日，不编造分位

    last5_pct = [p for p in pcts[-5:] if p is not None]
    last20_pct = [p for p in pcts[-20:] if p is not None]
    out["max_1d_drop_5d"] = min(last5_pct) / 100.0 if last5_pct else None
    out["max_1d_drop_20d"] = min(last20_pct) / 100.0 if last20_pct else None

    # 涨停：主板约10%，创业/科创约20%；用 9.8/19.6 容差
    for b in bars[-5:]:
        p = b.get("pct")
        code_guess_limit = 19.6 if True else 9.8  # refined later with board
        if p is not None and p >= 9.8:
            out["limit_up_5d"] = True

    tos = [b.get("turnover") for b in bars[-5:] if b.get("turnover") is not None]
    amts = [b.get("amount") for b in bars[-5:] if b.get("amount") is not None]
    out["avg_turnover_5d"] = (sum(tos) / len(tos)) if tos else None
    out["avg_amount_5d"] = (sum(amts) / len(amts)) if amts else None

    # 非脉冲：5日（或20日）跌幅若主要由单日贡献则判脉冲
    pulse = False
    r5 = out["ret_5d"]
    d5 = out["max_1d_drop_5d"]
    if r5 is not None and r5 <= -0.06 and d5 is not None and d5 < 0:
        if abs(d5) >= 0.70 * abs(r5):
            pulse = True
    r20 = out["ret_20d"]
    d20 = out["max_1d_drop_20d"]
    if r20 is not None and r20 <= -0.12 and d20 is not None and d20 < 0:
        if abs(d20) >= 0.80 * abs(r20):
            pulse = True
    out["pulse"] = pulse
    return out


def a_hits_of(m: dict) -> list[str]:
    hits = []
    r5, r20 = m.get("ret_5d"), m.get("ret_20d")
    if (r20 is not None and r20 <= -0.12) or (r5 is not None and r5 <= -0.06):
        hits.append("①")
    if m.get("dev_ma20") is not None and m["dev_ma20"] <= -0.06:
        hits.append("②")
    if m.get("pctile_60d") is not None and m["pctile_60d"] <= 0.40:
        hits.append("③")
    return hits


def fmt_pct(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "缺失"
    return f"{x * 100:.{digits}f}%"


def fmt_num(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "缺失"
    return f"{x:.{digits}f}"


def parse_sina_line(text: str, code: str) -> dict | None:
    m = re.search(r'="(.*)"', text)
    if not m:
        return None
    body = m.group(1)
    if not body:
        return None
    parts = body.split(",")
    if len(parts) < 32:
        return None
    return {
        "name": parts[0],
        "open": to_float(parts[1]),
        "prev_close": to_float(parts[2]),
        "close": to_float(parts[3]),
        "high": to_float(parts[4]),
        "low": to_float(parts[5]),
        "volume": to_float(parts[8]),
        "amount": to_float(parts[9]),
        "date": parts[30],
        "time": parts[31] if len(parts) > 31 else None,
        "src": "sina",
        "code": code,
    }


def parse_tencent_line(text: str, code: str) -> dict | None:
    m = re.search(r'="(.*)"', text)
    if not m:
        return None
    body = m.group(1)
    if not body:
        return None
    parts = body.split("~")
    if len(parts) < 50:
        return None
    return {
        "name": parts[1],
        "close": to_float(parts[3]),
        "prev_close": to_float(parts[4]),
        "open": to_float(parts[5]),
        "volume": to_float(parts[6]),
        "date": parts[30] if len(parts) > 30 else None,
        "pct": to_float(parts[32]) if len(parts) > 32 else None,
        "pe_ttm": to_float(parts[39]) if len(parts) > 39 else None,
        "pb": to_float(parts[46]) if len(parts) > 46 else None,
        "src": "tencent",
        "code": code,
    }


def fetch_sina_quotes(s: requests.Session, codes: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    s.headers["Referer"] = "https://finance.sina.com.cn/"
    for i in range(0, len(codes), 30):
        chunk = codes[i : i + 30]
        url = "https://hq.sinajs.cn/list=" + ",".join(sina_symbol(c) for c in chunk)
        try:
            r = s.get(url, timeout=15)
            r.encoding = "gbk"
            for line in r.text.splitlines():
                cm = re.search(r"hq_str_(?:sh|sz)(\d{6})", line)
                if not cm:
                    continue
                code = cm.group(1)
                parsed = parse_sina_line(line, code)
                if parsed:
                    out[code] = parsed
        except Exception:
            pass
        time.sleep(0.15)
    return out


def fetch_tencent_quotes(s: requests.Session, codes: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    s.headers["Referer"] = "https://qt.gtimg.cn/"
    for i in range(0, len(codes), 30):
        chunk = codes[i : i + 30]
        url = "https://qt.gtimg.cn/q=" + ",".join(sina_symbol(c) for c in chunk)
        try:
            r = s.get(url, timeout=15)
            r.encoding = "gbk"
            for line in r.text.split(";"):
                line = line.strip()
                if not line:
                    continue
                cm = re.search(r"v_(?:sh|sz)(\d{6})", line)
                if not cm:
                    continue
                code = cm.group(1)
                parsed = parse_tencent_line(line, code)
                if parsed:
                    out[code] = parsed
        except Exception:
            pass
        time.sleep(0.12)
    return out


def load_json(path: Path) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def collect(s: requests.Session) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clist_path = CACHE_DIR / "clist.json"
    extra_path = CACHE_DIR / "extra.json"
    kline_dir = CACHE_DIR / "klines"
    kline_dir.mkdir(exist_ok=True)

    clist_rows = load_json(clist_path)
    if not clist_rows:
        print("[1] fetching eastmoney clist ...", flush=True)
        clist_rows, clist_meta = fetch_clist_all(s)
        dump_json(clist_path, {"meta": clist_meta, "fetched_at": now_cn(), "rows": clist_rows})
        print(f"[1] clist rows={len(clist_rows)} meta={clist_meta}", flush=True)
    else:
        if isinstance(clist_rows, dict) and "rows" in clist_rows:
            print(f"[1] clist cache {len(clist_rows['rows'])}", flush=True)
            clist_rows = clist_rows["rows"]
        else:
            print(f"[1] clist cache {len(clist_rows)}", flush=True)

    extra = load_json(extra_path) or {}
    if extra.get("oil_codes") is None:
        print("[2] fetching 油运/光模块 concept + 涨停池 ...", flush=True)
        oil_bk, oil_codes = fetch_concept_codes(s, "航运")
        time.sleep(0.3)
        opt_bk, opt_codes = fetch_concept_codes(s, "光通信模块")
        zt_dates = ["20261106", "20261105", "20261104", "20261103", "20261102"]
        zt = {}
        for d in zt_dates:
            pool = fetch_zt_pool(s, d)
            zt[d] = [
                {
                    "c": str(x.get("c") or ""),
                    "n": x.get("n"),
                    "lbc": x.get("lbc"),
                    "zdp": x.get("zdp"),
                }
                for x in pool
            ]
            print(f"  zt {d}: {len(pool)}", flush=True)
            time.sleep(0.2)
        extra = {
            "fetched_at": now_cn(),
            "oil_bk": oil_bk,
            "oil_codes": sorted(oil_codes),
            "opt_bk": opt_bk,
            "opt_codes": sorted(opt_codes),
            "zt": zt,
        }
        dump_json(extra_path, extra)
        print(
            f"[2] oil_bk={oil_bk} n={len(oil_codes)} opt_bk={opt_bk} n={len(opt_codes)}",
            flush=True,
        )
    else:
        print(
            f"[2] extra cache oil={len(extra.get('oil_codes') or [])} opt={len(extra.get('opt_codes') or [])}",
            flush=True,
        )

    universe = []
    skipped_board = 0
    for d in clist_rows:
        code = str(d.get("f12") or "")
        name = str(d.get("f14") or "")
        if len(code) != 6:
            continue
        board = board_of(code)
        if not board:
            skipped_board += 1
            continue
        universe.append(
            {
                "code": code,
                "name": name,
                "board": board,
                "market": d.get("f13"),
                "close": to_float(d.get("f2")),
                "pct": to_float(d.get("f3")),
                "volume": to_float(d.get("f5")),
                "amount": to_float(d.get("f6")),
                "turnover": to_float(d.get("f8")),
                "pe": to_float(d.get("f9")),
                "pe_lyr": to_float(d.get("f114")),
                "pe_ttm": to_float(d.get("f115")),
                "pb": to_float(d.get("f23")),
                "prev_close": to_float(d.get("f18")),
                "mcap": to_float(d.get("f20")),
                "industry": d.get("f100") if d.get("f100") not in ("-", None) else None,
                "ret_5d_em": (to_float(d.get("f109")) or 0) / 100.0 if to_float(d.get("f109")) is not None else None,
                "ret_60d_em": (to_float(d.get("f24")) or 0) / 100.0 if to_float(d.get("f24")) is not None else None,
            }
        )
    print(f"[3] universe={len(universe)} skipped_non_hs_a={skipped_board}", flush=True)

    # klines
    need = []
    for u in universe:
        p = kline_dir / f"{u['code']}.json"
        if p.exists():
            u["bars"] = load_json(p)
        else:
            need.append(u)
    print(f"[4] klines cached={len(universe)-len(need)} need={len(need)}", flush=True)

    def worker(item: dict) -> tuple[str, list, str | None]:
        ls = session()
        secid = secid_of(item["code"], item.get("market"))
        bars = fetch_kline(ls, secid)
        err = None if bars else "empty"
        return item["code"], bars, err

    fail = 0
    if need:
        workers = 16
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(worker, u): u for u in need}
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    code, bars, err = fut.result()
                except Exception as e:
                    code, bars, err = u["code"], [], str(e)
                dump_json(kline_dir / f"{code}.json", bars)
                u["bars"] = bars
                done += 1
                if not bars:
                    fail += 1
                if done % 200 == 0 or done == len(need):
                    print(f"  kline {done}/{len(need)} fail={fail}", flush=True)
                # polite jitter already via network; extra pause every 400
                if done % 400 == 0:
                    time.sleep(0.4)

    # retry empties once, slower
    empties = [u for u in universe if not u.get("bars")]
    if empties:
        print(f"[4b] retry empty klines n={len(empties)}", flush=True)
        s2 = session()
        for i, u in enumerate(empties, 1):
            bars = fetch_kline(s2, secid_of(u["code"], u.get("market")))
            dump_json(kline_dir / f"{u['code']}.json", bars)
            u["bars"] = bars
            if i % 50 == 0:
                print(f"  retry {i}/{len(empties)}", flush=True)
            time.sleep(0.08)

    empty_final = sum(1 for u in universe if not u.get("bars"))
    print(f"[4] kline empty_final={empty_final}", flush=True)
    return {"universe": universe, "extra": extra, "empty_kline": empty_final}


def score_row(u: dict, extra: dict) -> dict:
    bars = u.get("bars") or []
    m = metrics_from_bars(bars)
    # refine limit-up using board
    limit_th = 19.6 if u["board"] in ("创业板", "科创板") else 9.8
    limit_up_5d = False
    near_board_5d = False
    for b in bars[-5:]:
        p = b.get("pct")
        if p is None:
            continue
        if p >= limit_th:
            limit_up_5d = True
        if p >= limit_th - 1.0:
            near_board_5d = True
    m["limit_up_5d"] = limit_up_5d
    m["near_board_5d"] = near_board_5d

    hits = a_hits_of(m)
    oil = set(extra.get("oil_codes") or []) | set(extra.get("ship_codes") or []) | OIL_SHIP_CODES
    opt = set(extra.get("opt_codes") or []) | OPTICAL_MODULE_CODES
    zt_codes = set()
    zt_lianban = set()
    for d, pool in (extra.get("zt") or {}).items():
        for x in pool:
            c = str(x.get("c") or "")
            if c:
                zt_codes.add(c)
                lbc = x.get("lbc") or 0
                try:
                    if int(lbc) >= 2:
                        zt_lianban.add(c)
                except Exception:
                    pass
            if d == "20261106" and c:
                zt_codes.add(c)

    # 现价：clist 缺价时回填日K asof 收盘，不编造
    if u.get("close") in (None, 0) and m.get("k_close"):
        u["close"] = m["k_close"]

    c_reasons = []
    name, ind, code = u["name"], u.get("industry"), u["code"]
    if is_st(name) or "退" in (name or ""):
        c_reasons.append("ST")
    if (name or "").startswith("退市") or (name or "").endswith("退"):
        c_reasons.append("退市无有效行情")
    live_px = u.get("close") or m.get("k_close")
    if live_px in (None, 0):
        c_reasons.append("停牌或无价")
    if is_power_stock(name, ind) or code in set(extra.get("power_codes") or []):
        c_reasons.append("电力")
    if code in oil:
        c_reasons.append("忌追袖·油运")
    if code in opt or any(k in (name or "") for k in OPTICAL_NAME_KEYS):
        c_reasons.append("忌追袖·光模块")
    if code in zt_lianban:
        c_reasons.append("连板")
    if m.get("limit_up_5d") and m.get("near_board_5d"):
        # 近5日触及涨停 = 连板/近板追杀反抽
        c_reasons.append("近5日涨停")
    # 无量僵尸：用日K近5日均额/换手，避免 clist 退市股 to=0 误杀仍有成交的票
    avg_amt = m.get("avg_amount_5d")
    avg_to = m.get("avg_turnover_5d")
    zombie = False
    if avg_amt is not None and avg_amt < 3_000_000 and (avg_to is None or avg_to < 0.40):
        zombie = True
    if (avg_to is not None and avg_to < 0.12) and (avg_amt is None or avg_amt < 12_000_000):
        zombie = True
    if zombie:
        c_reasons.append("无量僵尸")

    b_notes = []
    pe, pb = u.get("pe"), u.get("pb")
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
    if m.get("pulse"):
        b_notes.append("脉冲阴跌")
    else:
        b_notes.append("非脉冲")
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

    n_hits = len(hits)
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

    rank_score = n_hits * 100 + oversold + value_bonus - value_penalty
    if code in HELD:
        rank_score -= 200
    if code in CLEARED:
        rank_score -= 80
    if code in USER_NAMED_YI:
        rank_score -= 8  # 不强制塞回，轻微降权避免占新观察席

    return {
        **u,
        "metrics": m,
        "a_hits": hits,
        "c_reasons": c_reasons,
        "b_notes": b_notes,
        "rank_score": rank_score,
        "is_bank": is_bank(ind, name),
        "is_held": code in HELD,
        "is_cleared": code in CLEARED,
        "oil_sleeve": code in oil,
        "opt_sleeve": code in opt,
        "bars": None,  # drop heavy bars from scored copy
        "n_bars": m.get("n_bars"),
    }


def pick_shortlist(scored: list[dict]) -> tuple[list[dict], dict]:
    funnel = {
        "universe": len(scored),
        "by_board": {},
        "kline_ok": 0,
        "pass_A": 0,
        "pass_A_by_board": {},
        "pass_A2plus": 0,
        "after_C": 0,
        "after_B_quality": 0,
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
        # B 质量：畸高估值不进短名单候选；PE非正不进前列
        if pe is None or pe < 2 or pe > 40:
            continue
        if pb is None or pb < 0.30 or pb >= 4:
            continue
        if "退" in (x.get("name") or ""):
            continue
        if x["metrics"].get("pulse") and len(x["a_hits"]) < 3:
            continue
        if (x.get("name") or "").startswith("退市"):
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
        if x["code"] in USER_NAMED_YI:
            return False
        if len(x["a_hits"]) < min_hits:
            return False
        if x["is_bank"] and banks >= 1:
            return False
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

    # 满2优先、行业尽量分散；不够再放宽行业上限
    for min_hits, industry_cap in ((2, 1), (2, 2), (1, 2)):
        for x in candidates:
            if len(picked) >= 10:
                break
            if can_take(x, min_hits=min_hits, industry_cap=industry_cap):
                take(x)
        if len(picked) >= 5:
            break

    return picked[:10], funnel


def align_of(x: dict) -> str:
    if x["board"] == "科创板":
        return "观察·不对齐本账户开仓"
    if x["board"] == "创业板":
        return "可对齐"
    if x["is_bank"]:
        return "仅对照·勿堆第二银行强制席"
    return "主板"


def a_trigger_text(x: dict) -> str:
    m = x["metrics"]
    bits = []
    if "①" in x["a_hits"]:
        bits.append(f"①跌幅20d={fmt_pct(m.get('ret_20d'))}/5d={fmt_pct(m.get('ret_5d'))}")
    if "②" in x["a_hits"]:
        bits.append(f"②vsMA20={fmt_pct(m.get('dev_ma20'))}")
    if "③" in x["a_hits"]:
        p = m.get("pctile_60d")
        bits.append("③60d分位=" + (f"{p*100:.0f}%" if p is not None else "缺失"))
    # 即使未触发也在理由里有完整数字；表内只写触发项（与周五范例一致）
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
    if x["metrics"].get("pulse"):
        parts.append("脉冲阴跌")
    else:
        parts.append("非脉冲阴跌")
    if x["is_bank"]:
        parts.append("仅对照·勿堆第二银行强制席")
    return "；".join(parts)


def reason_sentence(x: dict) -> str:
    m = x["metrics"]
    p = m.get("pctile_60d")
    ptxt = f"{p*100:.0f}%" if p is not None else "缺失"
    return (
        f"满A{len(x['a_hits'])}；20d {fmt_pct(m.get('ret_20d'))} / vsMA20 {fmt_pct(m.get('dev_ma20'))} / "
        f"60d分位 {ptxt}；行业{x.get('industry') or '缺失'}；"
        f"PE={fmt_num(x.get('pe'),1)}/PB={fmt_num(x.get('pb'))}"
    )


def value_side_notes(scored: list[dict], short_codes: set[str]) -> dict[str, list[dict]]:
    """分板价值旁注：满2或深超跌但未进短名单的低估观察，每板≤5。不是破净五席表。"""
    out = {"主板": [], "创业板": [], "科创板": []}
    pool = [
        x
        for x in scored
        if x["code"] not in short_codes
        and not x["c_reasons"]
        and not x["is_held"]
        and not x["is_bank"]
        and "退" not in (x.get("name") or "")
        and x.get("pe") is not None
        and 2 <= x["pe"] <= 30
        and x.get("pb") is not None
        and 0.30 <= x["pb"] <= 3.0
        and len(x["a_hits"]) >= 2
    ]
    pool.sort(key=lambda z: (-len(z["a_hits"]), -z["rank_score"]))
    seen_ind: dict[str, int] = {}
    for x in pool:
        arr = out[x["board"]]
        if len(arr) >= 5:
            continue
        ind = x.get("industry") or "未知"
        if seen_ind.get(ind, 0) >= 1:
            continue
        seen_ind[ind] = seen_ind.get(ind, 0) + 1
        arr.append(x)
    return out


def build_outputs(
    scored: list[dict],
    picked: list[dict],
    funnel: dict,
    extra: dict,
    sina: dict,
    tencent: dict,
    fetch_meta: dict,
) -> tuple[str, dict]:
    fetched_at = now_cn()
    short_codes = {x["code"] for x in picked}
    side = value_side_notes(scored, short_codes)

    friday = {c: next((x for x in scored if x["code"] == c), None) for c in FRIDAY_SHORTLIST}
    keep, drop, new = [], [], []
    for c in FRIDAY_SHORTLIST:
        if c in short_codes:
            keep.append(c)
        else:
            drop.append(c)
    for x in picked:
        if x["code"] not in FRIDAY_SHORTLIST:
            new.append(x["code"])

    def quote_cell(x: dict) -> str:
        code = x["code"]
        sq = sina.get(code) or {}
        tq = tencent.get(code) or {}
        close = tq.get("close") or sq.get("close") or x.get("close")
        prev = tq.get("prev_close") or sq.get("prev_close") or x.get("prev_close")
        pct = None
        if close and prev:
            pct = (close / prev - 1.0) * 100
        elif x.get("pct") is not None:
            pct = x["pct"]
        s_c, t_c = sq.get("close"), tq.get("close")
        flag = ""
        if s_c and t_c and abs(s_c - t_c) > 0.02:
            flag = f"（核价差 新浪{s_c}/腾讯{t_c}）"
        if close is None:
            return "缺失"
        pct_s = f"{pct:+.2f}%" if pct is not None else "涨跌缺失"
        return f"{close} / {pct_s}{flag}"

    lines = []
    lines.append(f"# 轨A · 周一盘前全A价值超跌硬扫（口径 **t2052u / asof {PRICE_ASOF} 收盘**）")
    lines.append("")
    lines.append(
        f"> **窗口** {WINDOW_DATE} 周一盘前 Asia/Shanghai｜**price_asof** {PRICE_ASOF} 收盘｜"
        f"抓取 {fetched_at}｜价源：东财 clist+日K；短名单核价 新浪 `hq.sinajs.cn` + 腾讯 `qt.gtimg.cn`｜"
        "教育模拟｜**扫描 ≠ 买卖灯 ≠ 下单**｜超跌默认建议并 **乙**"
    )
    lines.append("")
    lines.append("## 口径")
    lines.append("")
    lines.append("- **A硬 ≥1**（满2优先）：①近20日≤−12% 或 近5日≤−6%；②相对MA20≤−6%；③近60日价格分位≤40%")
    lines.append("- **B软**：PE>0；破净/低PE优先；畸高PE/PB降权剔除出短名单；非脉冲阴跌；非ST")
    lines.append("- **C排除**：涨停/连板追高、忌追袖（油运续/光模块/连板近板）、无量僵尸、电力、已持不占新观察、已清不加回主推前列")
    lines.append("- 科创：**观察·不对齐本账户开仓**｜创业：**可对齐**｜银行≤1仅对照勿堆第二银行")
    lines.append(
        f"- 漏斗：扫描 {funnel['universe']}（主板 {funnel['by_board'].get('主板',0)} / "
        f"创业 {funnel['by_board'].get('创业板',0)} / 科创 {funnel['by_board'].get('科创板',0)}）→ "
        f"K线有效 {funnel['kline_ok']} → 过A {funnel['pass_A']} "
        f"（主板 {funnel['pass_A_by_board'].get('主板',0)} / 创业 {funnel['pass_A_by_board'].get('创业板',0)} / "
        f"科创 {funnel['pass_A_by_board'].get('科创板',0)}；满2 {funnel['pass_A2plus']}）→ "
        f"过C {funnel['after_C']} → 价值质量 {funnel['after_B_quality']} → 短名单 **{len(picked)}**"
    )
    lines.append("")
    lines.append("## 方法与盲点")
    lines.append("")
    empty_n = fetch_meta.get("empty_kline")
    empty_names = fetch_meta.get("empty_names") or []
    empty_txt = "、".join(f"`{c} {n}`" for c, n in empty_names) if empty_names else ""
    lines.append(
        f"- 名单：东财 `clist` fs=沪深A股（主板+创业+科创），reported_total={fetch_meta.get('clist_total')}，"
        f"入宇宙 {funnel['universe']}（另跳过非60/00/300/301/688 代码 {fetch_meta.get('skipped_non_hs_a', 2)}）；"
        f"K线空/失败 {empty_n} 只"
        + (f"：{empty_txt}" if empty_txt else "")
        + "，不编造补数。"
    )
    skipped_names = fetch_meta.get("skipped_names") or extra.get("skipped_names") or []
    if skipped_names:
        skip_txt = "、".join(f"`{c} {n}`" for c, n in skipped_names)
        lines[-1] = lines[-1].replace(
            f"另跳过非60/00/300/301/688 代码 {fetch_meta.get('skipped_non_hs_a', 2)}",
            f"另跳过非60/00/300/301/688 代码 {len(skipped_names)}：{skip_txt}",
        )
    lines.append(
        "- 指标：不复权日K，`ret_Nd=close[t]/close[t-N]-1`；`MA20=近20收盘均值`（含 asof）；"
        "`pctile_60d=近60收盘中 ≤ 现价的占比`。东财 f109 仅作 5 日交叉，20 日/MA20/分位一律用 K 线现算。"
        "A③单独过门面很宽（近60日分位≤40%常见），短名单只从**满2条A**且过 B/C、估值带得上的票里按分板/行业配额取 5–10。"
    )
    lines.append(
        f"- 忌追袖成分：油运BK={extra.get('oil_bk')} n={len(extra.get('oil_codes') or [])}；"
        f"光模块BK={extra.get('opt_bk')} n={len(extra.get('opt_codes') or [])}；"
        "另并代码兜底。涨停池东财 `getTopicZTPool` 11/02–11/06。"
    )
    lines.append(
        "- **未全量核验**：证监会立案/重大违法调查、停牌公告全文。ST 按简称过滤。缺 PE/PB/K 线字段标「缺失」，不填假数。"
    )
    lines.append(
        "- 现持只作纸面对照、不占新观察名额："
        + "；".join(f"`{c} {n}`" for c, n in HELD.items())
        + "。已清不加回："
        + "；".join(f"`{c} {n}`" for c, n in CLEARED.items())
        + "。"
    )
    if extra.get("zt_fail"):
        lines.append(f"- 涨停池失败：{extra.get('zt_fail')}")
    lines.append("")
    lines.append("## 超跌短名单（建议并乙｜5–10）")
    lines.append("")
    lines.append("| # | 代码+全称 | 板 | 昨收/相对前收 | A触发 | B软一句 | 一句理由 | 对齐 |")
    lines.append("|---|-----------|----|---------------|------|---------|----------|------|")
    for i, x in enumerate(picked, 1):
        lines.append(
            f"| {i} | `{x['code']} {x['name']}` | {x['board']} | {quote_cell(x)} | "
            f"{a_trigger_text(x)} | {b_sentence(x)} | {reason_sentence(x)} | {align_of(x)} |"
        )
    lines.append("")
    lines.append("### 分板")
    lines.append("")
    for b in ("主板", "创业板", "科创板"):
        n = sum(1 for x in picked if x["board"] == b)
        lines.append(f"- {b}：**{n}**")
    lines.append("")
    lines.append("## 相对周五 t2052u")
    lines.append("")

    def name_of(code: str) -> str:
        hit = next((x for x in scored if x["code"] == code), None)
        if hit:
            return f"`{code} {hit['name']}`"
        return f"`{code}`"

    def why_drop(code: str) -> str:
        x = friday.get(code)
        if x is None:
            return "本窗未入宇宙或K线失败"
        bits = []
        if not x["a_hits"]:
            m = x["metrics"]
            bits.append(
                f"A未过门(20d={fmt_pct(m.get('ret_20d'))},5d={fmt_pct(m.get('ret_5d'))},"
                f"MA20={fmt_pct(m.get('dev_ma20'))},60d分位={fmt_pct(m.get('pctile_60d'),0)})"
            )
        else:
            bits.append("A=" + "".join(x["a_hits"]))
        if x["c_reasons"]:
            bits.append("C=" + ",".join(x["c_reasons"]))
        if x["is_held"]:
            bits.append("现持不占新观察")
        if not bits:
            bits.append("仍过A，主板/行业配额或估值排序下未进前10，见旁注")
        elif "C=" not in "；".join(bits) and x["a_hits"]:
            bits.append("分板/行业配额或排序未进前10")
        return "；".join(bits)

    lines.append("- 保留：" + ("、".join(name_of(c) for c in keep) if keep else "无"))
    lines.append("- 换出：" + ("、".join(f"{name_of(c)}（{why_drop(c)}）" for c in drop) if drop else "无"))
    lines.append("- 新入：" + ("、".join(name_of(c) for c in new) if new else "无"))
    lines.append("- 用户点名已在乙、本窗不强制塞回：" + "、".join(f"`{c}`" for c in sorted(USER_NAMED_YI)))
    lines.append("")
    lines.append("## 分板价值旁注（不占超跌短名单名额，每板≤5）")
    lines.append("")
    lines.append("旁注是低估带观察，不是破净五席表，也不是买入清单。")
    lines.append("")
    for b in ("主板", "创业板", "科创板"):
        arr = side[b]
        if not arr:
            lines.append(f"- {b}：无（过门不足）")
            continue
        bits = []
        for x in arr:
            al = align_of(x)
            bits.append(
                f"`{x['code']} {x['name']}` PE={fmt_num(x.get('pe'),1)}/PB={fmt_num(x.get('pb'))} "
                f"A={''.join(x['a_hits'])} {al}"
            )
        lines.append(f"- {b}：" + "；".join(bits))
    lines.append("")
    lines.append("## 核价")
    lines.append("")
    lines.append("| 代码 | 东财收盘 | 新浪 | 腾讯 | asof |")
    lines.append("|------|----------|------|------|------|")
    for x in picked:
        code = x["code"]
        sq, tq = sina.get(code) or {}, tencent.get(code) or {}
        lines.append(
            f"| `{code}` | {fmt_num(x.get('close'))} | {fmt_num(sq.get('close'))} "
            f"| {fmt_num(tq.get('close'))} | {sq.get('date') or tq.get('date') or PRICE_ASOF} |"
        )
    lines.append("")
    lines.append("扫描≠买卖灯｜名单≠买卖灯｜建议默认进乙｜教育模拟，非投资建议。")
    lines.append("")

    json_rows = []
    for x in picked:
        m = x["metrics"]
        json_rows.append(
            {
                "code": x["code"],
                "name": x["name"],
                "board": x["board"],
                "close": x.get("close"),
                "prev_close": x.get("prev_close"),
                "pct": x.get("pct"),
                "ret_5d": m.get("ret_5d"),
                "ret_20d": m.get("ret_20d"),
                "dev_ma20": m.get("dev_ma20"),
                "pctile_60d": m.get("pctile_60d"),
                "ma20": m.get("ma20"),
                "a_hits": x["a_hits"],
                "pe": x.get("pe"),
                "pb": x.get("pb"),
                "pe_ttm": x.get("pe_ttm"),
                "industry": x.get("industry"),
                "turnover": x.get("turnover"),
                "note": reason_sentence(x),
                "b_soft": b_sentence(x),
                "align": align_of(x),
                "sina_close": (sina.get(x["code"]) or {}).get("close"),
                "tencent_close": (tencent.get(x["code"]) or {}).get("close"),
                "pulse": m.get("pulse"),
                "k_asof": m.get("k_asof"),
                "n_bars": m.get("n_bars"),
            }
        )

    payload = {
        "window": WINDOW_DATE,
        "price_asof": PRICE_ASOF,
        "fetched_at": fetched_at,
        "disclaimer": "扫描≠买卖灯｜教育模拟，非投资建议。不要把本名单写成买入指令。",
        "funnel": funnel,
        "fetch_meta": fetch_meta,
        "vs_friday_t2052u": {"keep": keep, "drop": drop, "new": new},
        "shortlist": json_rows,
        "side_notes": {
            b: [
                {
                    "code": x["code"],
                    "name": x["name"],
                    "pe": x.get("pe"),
                    "pb": x.get("pb"),
                    "a_hits": x["a_hits"],
                    "align": align_of(x),
                }
                for x in side[b]
            ]
            for b in ("主板", "创业板", "科创板")
        },
    }
    return "\n".join(lines), payload


def merge_sleeves(extra: dict) -> dict:
    extra = dict(extra or {})
    sleeves_path = CACHE_DIR / "sleeves.json"
    sleeves = load_json(sleeves_path) or {}
    ship = set(extra.get("ship_codes") or []) | set(sleeves.get("ship_codes") or []) | OIL_SHIP_CODES
    opt = set(extra.get("opt_codes") or []) | OPTICAL_MODULE_CODES
    for c, n in sleeves.get("opt") or sleeves.get("opt_names") or []:
        if any(k in str(n) for k in OPTICAL_NAME_KEYS):
            opt.add(str(c))
    extra["ship_codes"] = sorted(ship)
    extra["oil_codes"] = sorted(ship)
    extra["oil_bk"] = extra.get("oil_bk") or "BK1482"
    extra["opt_codes"] = sorted(opt)
    extra["opt_bk"] = extra.get("opt_bk") or "BK1136"
    extra["power_codes"] = sorted(set(extra.get("power_codes") or []) | set(sleeves.get("power_codes") or []))
    return extra


def universe_from_cache() -> tuple[list[dict], dict, int]:
    clist_blob = load_json(CACHE_DIR / "clist.json") or {}
    rows = clist_blob.get("rows") if isinstance(clist_blob, dict) else clist_blob
    extra = merge_sleeves(load_json(CACHE_DIR / "extra.json") or {})
    kline_dir = CACHE_DIR / "klines"
    universe = []
    empty = 0
    skipped = 0
    for d in rows or []:
        code = str(d.get("f12") or "")
        name = str(d.get("f14") or "")
        if len(code) != 6:
            continue
        board = board_of(code)
        if not board:
            skipped += 1
            extra.setdefault("skipped_names", []).append((code, name))
            continue
        bars = load_json(kline_dir / f"{code}.json") or []
        if not bars:
            empty += 1
        close = to_float(d.get("f2"))
        if close in (None, 0) and bars:
            close = bars[-1]["close"]
        universe.append(
            {
                "code": code,
                "name": name,
                "board": board,
                "market": d.get("f13"),
                "close": close,
                "pct": to_float(d.get("f3")),
                "volume": to_float(d.get("f5")),
                "amount": to_float(d.get("f6")),
                "turnover": to_float(d.get("f8")),
                "pe": to_float(d.get("f9")),
                "pe_lyr": to_float(d.get("f114")),
                "pe_ttm": to_float(d.get("f115")),
                "pb": to_float(d.get("f23")),
                "prev_close": to_float(d.get("f18")),
                "mcap": to_float(d.get("f20")),
                "industry": d.get("f100") if d.get("f100") not in ("-", None) else None,
                "bars": bars,
            }
        )
    extra["clist_total"] = (clist_blob.get("meta") or {}).get("total_reported") if isinstance(clist_blob, dict) else None
    extra["skipped_non_hs_a"] = skipped
    extra["skipped_names"] = extra.get("skipped_names") or []
    return universe, extra, empty


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=["all", "collect", "report", "rescore"])
    args = parser.parse_args()

    scored_path = CACHE_DIR / "scored.json"
    s = session()

    if args.stage in ("all", "collect"):
        bundle = collect(s)
        extra = merge_sleeves(bundle["extra"])
        print("[5] scoring ...", flush=True)
        scored = [score_row(u, extra) for u in bundle["universe"]]
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
                "clist_total": extra.get("clist_total"),
                "scored": slim,
            },
        )
        print(f"[5] scored={len(slim)} empty_kline={bundle['empty_kline']}", flush=True)

    if args.stage == "collect":
        return 0

    if args.stage in ("rescore", "report", "all"):
        if args.stage == "rescore" or not scored_path.exists() or args.stage == "report":
            if args.stage in ("rescore", "report"):
                print("[5b] rescore from kline cache ...", flush=True)
                universe, extra, empty = universe_from_cache()
                scored = [score_row(u, extra) for u in universe]
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
                        "clist_total": extra.get("clist_total"),
                        "scored": slim,
                    },
                )
                print(f"[5b] scored={len(slim)} empty_kline={empty} oil={len(extra.get('oil_codes') or [])} opt={len(extra.get('opt_codes') or [])}", flush=True)
                if args.stage == "rescore":
                    return 0

    blob = load_json(scored_path)
    if not blob:
        raise SystemExit("no scored cache; run collect first")
    scored = blob["scored"]
    extra = merge_sleeves(blob["extra"])
    picked, funnel = pick_shortlist(scored)
    print(f"[6] shortlist={len(picked)} funnel={funnel}", flush=True)
    for x in picked:
        print(
            "  ",
            x["code"],
            x["name"],
            x["board"],
            x["a_hits"],
            "pe",
            x.get("pe"),
            "pb",
            x.get("pb"),
            "score",
            round(x["rank_score"], 1),
            flush=True,
        )

    codes = [x["code"] for x in picked]
    print("[7] sina+tencent cross quotes ...", flush=True)
    sina = fetch_sina_quotes(session(), codes)
    tencent = fetch_tencent_quotes(session(), codes)
    empty_names = [
        (x["code"], x["name"]) for x in scored if not x.get("n_bars")
    ]
    fetch_meta = {
        "clist_total": blob.get("clist_total") or extra.get("clist_total"),
        "empty_kline": blob.get("empty_kline"),
        "empty_names": empty_names,
        "skipped_non_hs_a": extra.get("skipped_non_hs_a"),
        "skipped_names": extra.get("skipped_names") or [],
        "sina_ok": len(sina),
        "tencent_ok": len(tencent),
        "oil_bk": extra.get("oil_bk"),
        "opt_bk": extra.get("opt_bk"),
        "oil_n": len(extra.get("oil_codes") or []),
        "opt_n": len(extra.get("opt_codes") or []),
        "power_n": len(extra.get("power_codes") or []),
    }
    md, payload = build_outputs(scored, picked, funnel, extra, sina, tencent, fetch_meta)
    OUT_MD.write_text(md, encoding="utf-8")
    dump_json(OUT_JSON, payload)
    print(f"[8] wrote {OUT_MD} {OUT_JSON}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
