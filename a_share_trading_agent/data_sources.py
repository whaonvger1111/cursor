"""行情与历史数据获取（东方财富 HTTP + Baostock）。"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import pandas as pd

try:
    import baostock as bs
except ImportError:  # pragma: no cover
    bs = None  # type: ignore


EM_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
EM_REFERER = "https://quote.eastmoney.com/"


def _em_request(url: str, timeout: float = 45.0, retries: int = 4) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": EM_UA, "Referer": EM_REFERER},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            time.sleep(2**attempt)
    raise last_err  # type: ignore[misc]


@dataclass
class SpotRow:
    code: str
    name: str
    market: int
    last: float | None
    pct_chg: float | None
    turnover: float | None
    volume: float | None
    amt: float | None
    high: float | None
    low: float | None
    open_: float | None
    pre_close: float | None


def eastmoney_code_to_baostock(code: str, market: int | None = None) -> str:
    """将东方财富 f12/f13 转为 Baostock 代码，如 sh.600519 / sz.000001。"""
    c = str(code).strip()
    if c.startswith("6") or c.startswith("688") or c.startswith("689"):
        return f"sh.{c}"
    if c.startswith(("0", "1", "2", "3")):
        return f"sz.{c}"
    if market == 1:
        return f"sh.{c}"
    return f"sz.{c}"


def fetch_eastmoney_spot_page(
    page: int = 1,
    page_size: int = 100,
    sort_field: str = "f6",
    sort_order: int = 1,
) -> list[SpotRow]:
    """
    拉取 A 股实时列表一页（按成交额等排序，便于筛流动性）。
    sort_field: f3 涨跌幅, f5 成交量, f6 成交额, f8 换手率
    """
    qs = urllib.parse.urlencode(
        {
            "pn": page,
            "pz": page_size,
            "po": sort_order,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": sort_field,
            "fs": "m:0+t:6,m:0+t:80",
        }
    )
    url = f"https://push2.eastmoney.com/api/qt/clist/get?{qs}"
    raw = _em_request(url)
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    diff = (payload.get("data") or {}).get("diff") or []
    out: list[SpotRow] = []
    for row in diff:
        out.append(
            SpotRow(
                code=str(row.get("f12", "")),
                name=str(row.get("f14", "")),
                market=int(row.get("f13", 0) or 0),
                last=_f(row.get("f2")),
                pct_chg=_f(row.get("f3")),
                turnover=_f(row.get("f8")),
                volume=_f(row.get("f5")),
                amt=_f(row.get("f6")),
                high=_f(row.get("f15")),
                low=_f(row.get("f16")),
                open_=_f(row.get("f17")),
                pre_close=_f(row.get("f18")),
            )
        )
    return out


def _f(x: Any) -> float | None:
    if x is None or x == "-" or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


@contextmanager
def baostock_session() -> Iterator[None]:
    """单次登录，批量查询后退出。"""
    if bs is None:
        raise RuntimeError("需要安装 baostock: pip install baostock")
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock 登录失败: {lg.error_msg}")
    try:
        yield
    finally:
        bs.logout()


def _baostock_daily_impl(
    bs_code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,volume,amount",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2",
    )
    rows: list[list[str]] = []
    while rs.error_code == "0" and rs.next():
        rows.append(rs.get_row_data())
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        rows,
        columns=["date", "open", "high", "low", "close", "volume", "amount"],
    )
    for col in ("open", "high", "low", "close", "volume", "amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def query_baostock_daily(
    bs_code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """在 `baostock_session()` 内调用，避免重复登录。"""
    return _baostock_daily_impl(bs_code, start_date, end_date)


def fetch_baostock_daily(
    bs_code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """日线前复权（Baostock adjustflag=2 为前复权），独立会话。"""
    with baostock_session():
        return _baostock_daily_impl(bs_code, start_date, end_date)
