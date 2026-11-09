"""东财 clist / 日K / 概念 / 涨停池；新浪+腾讯核价。"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from .config import CACHE_DIR, KLINE_END, PRICE_ASOF, UA, now_cn
    from .metrics import board_of, parse_kline_row, to_float
    from .store import dump_json, load_json
except ImportError:
    from config import CACHE_DIR, KLINE_END, PRICE_ASOF, UA, now_cn
    from metrics import board_of, parse_kline_row, to_float
    from store import dump_json, load_json


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=32))
    s.headers.update({"User-Agent": UA, "Accept": "*/*", "Referer": "https://quote.eastmoney.com/"})
    return s


def fetch_json(s: requests.Session, url: str, params: dict | None = None, timeout: int = 20) -> dict | None:
    try:
        r = s.get(url, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def fetch_clist_all(s: requests.Session) -> tuple[list[dict], dict]:
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
            "f15",
            "f16",
            "f17",
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
    meta: dict[str, Any] = {"pages_ok": 0, "pages_fail": 0, "total_reported": None, "host": None}
    pn = 1
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
            time.sleep(0.35)
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
        time.sleep(0.1)
    return rows, meta


KNOWN_BKS = {
    "oil": ("BK1482", "航运"),
    "opt": ("BK1136", "光通信模块"),
    "ai": ("BK1128", "算力设备"),
    "power": ("BK0428", "电力"),
}


def fetch_bk_members(s: requests.Session, bk: str) -> set[str]:
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    codes: set[str] = set()
    for pn in range(1, 50):
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
        time.sleep(0.1)
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
    return codes


def fetch_concept_codes(s: requests.Session, keyword: str) -> tuple[str | None, set[str], str | None]:
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
    bk_name = None
    for pn in range(1, 16):
        params["pn"] = pn
        data = fetch_json(s, url, params)
        time.sleep(0.12)
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
                bk, bk_name = code, name
                break
        if bk:
            break
    if not bk:
        return None, set(), None
    codes: set[str] = set()
    for pn in range(1, 50):
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
        time.sleep(0.1)
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
    return bk, codes, bk_name


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
    return data["data"].get("pool") or []


def secid_of(code: str, market: int | None = None) -> str:
    if market in (0, 1):
        return f"{market}.{code}"
    if code.startswith(("6", "9")):
        return f"1.{code}"
    return f"0.{code}"


def sina_symbol(code: str) -> str:
    return ("sh" if code.startswith(("6", "9")) else "sz") + code


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
                time.sleep(0.35 + attempt * 0.35)
                continue
            payload = r.json()
            klines = ((payload or {}).get("data") or {}).get("klines") or []
            rows = []
            for line in klines:
                row = parse_kline_row(line)
                if row:
                    rows.append(row)
            return [x for x in rows if x["date"] <= PRICE_ASOF]
        except Exception:
            time.sleep(0.4 + attempt * 0.4)
    return []


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
    if len(parts) < 47:
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
                parsed = parse_sina_line(line, cm.group(1))
                if parsed:
                    out[cm.group(1)] = parsed
        except Exception:
            pass
        time.sleep(0.12)
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
                parsed = parse_tencent_line(line, cm.group(1))
                if parsed:
                    out[cm.group(1)] = parsed
        except Exception:
            pass
        time.sleep(0.1)
    return out


def clist_row_to_universe(d: dict) -> dict | None:
    code = str(d.get("f12") or "")
    name = str(d.get("f14") or "")
    if len(code) != 6:
        return None
    board = board_of(code)
    if not board:
        return None
    return {
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
        "vol_ratio": to_float(d.get("f10")),
        "high": to_float(d.get("f15")),
        "low": to_float(d.get("f16")),
        "open": to_float(d.get("f17")),
        "prev_close": to_float(d.get("f18")),
        "mcap": to_float(d.get("f20")),
        "pb": to_float(d.get("f23")),
        "pe_lyr": to_float(d.get("f114")),
        "pe_ttm": to_float(d.get("f115")),
        "industry": d.get("f100") if d.get("f100") not in ("-", None) else None,
        "ret_5d_em": (to_float(d.get("f109")) or 0) / 100.0 if to_float(d.get("f109")) is not None else None,
    }


def fill_sleeves(s: requests.Session, extra: dict) -> dict:
    """Keyword 搜概念失败时，用已知 BK 兜底补忌追袖/电力成分。"""
    extra = dict(extra or {})
    mapping = [
        ("oil", "oil_bk", "oil_bk_name", "oil_codes", "航运"),
        ("opt", "opt_bk", "opt_bk_name", "opt_codes", "光通信模块"),
        ("ai", "ai_bk", "ai_bk_name", "ai_codes", "算力设备"),
        ("power", "power_bk", "power_bk_name", "power_codes", "火力发电"),
    ]
    for key, bk_f, name_f, codes_f, keyword in mapping:
        if extra.get(codes_f):
            continue
        bk, codes, name = fetch_concept_codes(s, keyword)
        if not bk:
            bk, name = KNOWN_BKS[key]
            codes = fetch_bk_members(s, bk)
        extra[bk_f] = bk
        extra[name_f] = name
        extra[codes_f] = sorted(codes)
        print(f"[sleeve] {key} {bk}/{name} n={len(codes)}", flush=True)
        time.sleep(0.15)
    return extra


def collect(s: requests.Session) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clist_path = CACHE_DIR / "clist.json"
    extra_path = CACHE_DIR / "extra.json"
    kline_dir = CACHE_DIR / "klines"
    kline_dir.mkdir(exist_ok=True)

    clist_blob = load_json(clist_path)
    if not clist_blob:
        print("[1] fetching eastmoney clist ...", flush=True)
        clist_rows, clist_meta = fetch_clist_all(s)
        dump_json(clist_path, {"meta": clist_meta, "fetched_at": now_cn(), "rows": clist_rows})
        print(f"[1] clist rows={len(clist_rows)} meta={clist_meta}", flush=True)
    else:
        clist_rows = clist_blob["rows"] if isinstance(clist_blob, dict) else clist_blob
        print(f"[1] clist cache {len(clist_rows)}", flush=True)

    extra = load_json(extra_path) or {}
    if extra.get("oil_codes") is None or extra.get("need_sleeve_repair"):
        print("[2] fetching sleeves + zt pool ...", flush=True)
        oil_bk, oil_codes, oil_name = fetch_concept_codes(s, "航运")
        if not oil_bk:
            oil_bk, oil_name = KNOWN_BKS["oil"]
            oil_codes = fetch_bk_members(s, oil_bk)
        time.sleep(0.2)
        opt_bk, opt_codes, opt_name = fetch_concept_codes(s, "光通信模块")
        if not opt_bk:
            opt_bk, opt_name = KNOWN_BKS["opt"]
            opt_codes = fetch_bk_members(s, opt_bk)
        time.sleep(0.2)
        ai_bk, ai_codes, ai_name = fetch_concept_codes(s, "算力设备")
        if not ai_bk:
            ai_bk, ai_name = KNOWN_BKS["ai"]
            ai_codes = fetch_bk_members(s, ai_bk)
        time.sleep(0.2)
        pwr_bk, pwr_codes, pwr_name = fetch_concept_codes(s, "火力发电")
        if not pwr_bk:
            pwr_bk, pwr_name = KNOWN_BKS["power"]
            pwr_codes = fetch_bk_members(s, pwr_bk)
        zt_dates = ["20261109", "20261106", "20261105", "20261104", "20261103"]
        zt = {}
        for d in zt_dates:
            pool = fetch_zt_pool(s, d)
            zt[d] = [
                {"c": str(x.get("c") or ""), "n": x.get("n"), "lbc": x.get("lbc"), "zdp": x.get("zdp")}
                for x in pool
            ]
            print(f"  zt {d}: {len(pool)}", flush=True)
            time.sleep(0.15)
        extra = {
            "fetched_at": now_cn(),
            "oil_bk": oil_bk,
            "oil_bk_name": oil_name,
            "oil_codes": sorted(oil_codes),
            "opt_bk": opt_bk,
            "opt_bk_name": opt_name,
            "opt_codes": sorted(opt_codes),
            "ai_bk": ai_bk,
            "ai_bk_name": ai_name,
            "ai_codes": sorted(ai_codes),
            "power_bk": pwr_bk,
            "power_bk_name": pwr_name,
            "power_codes": sorted(pwr_codes),
            "zt": zt,
        }
        dump_json(extra_path, extra)
        print(
            f"[2] oil={oil_bk}/{len(oil_codes)} opt={opt_bk}/{len(opt_codes)} "
            f"ai={ai_bk}/{len(ai_codes)} pwr={pwr_bk}/{len(pwr_codes)}",
            flush=True,
        )
    else:
        print(f"[2] extra cache oil={len(extra.get('oil_codes') or [])}", flush=True)

    universe = []
    skipped = []
    for d in clist_rows:
        code = str(d.get("f12") or "")
        name = str(d.get("f14") or "")
        row = clist_row_to_universe(d)
        if row is None:
            if len(code) == 6:
                skipped.append((code, name))
            continue
        universe.append(row)
    extra["skipped_names"] = skipped
    extra["skipped_non_hs_a"] = len(skipped)
    print(f"[3] universe={len(universe)} skipped_non_hs_a={len(skipped)}", flush=True)

    need = []
    for u in universe:
        p = kline_dir / f"{u['code']}.json"
        cached = load_json(p)
        if cached:
            u["bars"] = cached
        else:
            need.append(u)
    print(f"[4] klines cached={len(universe) - len(need)} need={len(need)}", flush=True)

    def worker(item: dict) -> tuple[str, list, str | None]:
        ls = session()
        bars = fetch_kline(ls, secid_of(item["code"], item.get("market")))
        return item["code"], bars, None if bars else "empty"

    fail = 0
    if need:
        done = 0
        with ThreadPoolExecutor(max_workers=20) as ex:
            futs = {ex.submit(worker, u): u for u in need}
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    code, bars, _err = fut.result()
                except Exception as e:
                    code, bars = u["code"], []
                    print(f"  kline err {code}: {e}", flush=True)
                dump_json(kline_dir / f"{code}.json", bars)
                u["bars"] = bars
                done += 1
                if not bars:
                    fail += 1
                if done % 250 == 0 or done == len(need):
                    print(f"  kline {done}/{len(need)} fail={fail}", flush=True)

    empties = [u for u in universe if not u.get("bars")]
    if empties:
        print(f"[4b] retry empty klines n={len(empties)}", flush=True)
        s2 = session()
        for i, u in enumerate(empties, 1):
            bars = fetch_kline(s2, secid_of(u["code"], u.get("market")))
            dump_json(kline_dir / f"{u['code']}.json", bars)
            u["bars"] = bars
            if i % 40 == 0:
                print(f"  retry {i}/{len(empties)}", flush=True)
            time.sleep(0.06)

    empty_final = sum(1 for u in universe if not u.get("bars"))
    print(f"[4] kline empty_final={empty_final}", flush=True)
    return {"universe": universe, "extra": extra, "empty_kline": empty_final, "skipped_names": skipped}


def universe_from_cache() -> tuple[list[dict], dict, int]:
    clist_blob = load_json(CACHE_DIR / "clist.json") or {}
    rows = clist_blob.get("rows") if isinstance(clist_blob, dict) else clist_blob
    extra = load_json(CACHE_DIR / "extra.json") or {}
    extra["clist_total"] = (clist_blob.get("meta") or {}).get("total_reported") if isinstance(clist_blob, dict) else None
    kline_dir = CACHE_DIR / "klines"
    universe = []
    empty = 0
    skipped = []
    for d in rows or []:
        row = clist_row_to_universe(d)
        if row is None:
            code = str(d.get("f12") or "")
            name = str(d.get("f14") or "")
            if len(code) == 6:
                skipped.append((code, name))
            continue
        bars = load_json(kline_dir / f"{row['code']}.json") or []
        if not bars:
            empty += 1
        if row.get("close") in (None, 0) and bars:
            row["close"] = bars[-1]["close"]
        row["bars"] = bars
        universe.append(row)
    extra["skipped_names"] = skipped
    extra["skipped_non_hs_a"] = len(skipped)
    return universe, extra, empty
