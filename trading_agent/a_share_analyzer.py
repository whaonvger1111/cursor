"""
中国 A 股：基于公开行情的技术面扫描与买卖时机提示。

重要：输出为算法生成的技术分析参考，不构成投资建议。
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError as e:  # pragma: no cover
    raise ImportError("请安装 akshare：pip install akshare") from e

from trading_agent import signals as sig


T = TypeVar("T")


def _retry_call(
    fn: Callable[[], T],
    attempts: int = 5,
    base_sleep: float = 0.4,
    max_sleep: float = 6.0,
) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i < attempts - 1:
                delay = min(base_sleep * (2**i), max_sleep)
                time.sleep(delay)
    assert last is not None
    raise last


DISCLAIMER_CN = (
    "【免责声明】本工具仅根据公开行情做技术指标演算，不构成证券投资建议；"
    "买卖决策请自行判断并承担风险。"
)


@dataclass
class SymbolInsight:
    code: str
    name: str
    last_price: float | None
    pct_change_day: float | None
    rsi14: float | None
    sma20: float | None
    sma60: float | None
    macd_hist: float | None
    ret_20d_pct: float | None
    ret_60d_pct: float | None
    signal_score: float
    verdict: str
    buy_timing_hint: str
    sell_timing_hint: str


def _read_watchlist(path: Path) -> list[str]:
    if not path.is_file():
        return []
    codes: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        codes.append(line.split()[0].strip())
    return codes


def _default_watchlist() -> list[str]:
    """示例股票（沪深主板/常见标的），可按需替换。"""
    return ["600519", "000858", "601318", "600036"]


def _normalize_spot(df: pd.DataFrame) -> pd.DataFrame:
    """统一东方财富实时行情列名。"""
    col_map = {
        "代码": "code",
        "名称": "name",
        "最新价": "last",
        "涨跌幅": "pct",
        "成交额": "amount",
        "成交量": "vol",
    }
    out = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return out


def _boards_for_code(code: str) -> list[str]:
    """按代码前缀判断可能所在的东方财富行情分表，减少全市场拉取。"""
    c = code.strip()
    if not c.isdigit() or len(c) != 6:
        return ["sh", "sz", "cy", "kc", "bj"]
    if c.startswith("688"):
        return ["kc", "sh"]
    if c.startswith("60"):
        return ["sh"]
    if c.startswith(("000", "001", "002", "003")):
        return ["sz"]
    if c.startswith(("300", "301")):
        return ["cy", "sz"]
    if c.startswith(("43", "83", "87", "88", "92")):
        return ["bj"]
    return ["sh", "sz", "cy", "kc", "bj"]


def _merge_spot_maps(parts: list[pd.DataFrame]) -> dict[str, pd.Series]:
    out: dict[str, pd.Series] = {}
    for raw in parts:
        if raw is None or raw.empty:
            continue
        nd = _normalize_spot(raw)
        if "code" not in nd.columns:
            continue
        for _, row in nd.iterrows():
            code = str(row["code"]).strip()
            out[code] = row
    return out


def fetch_spot_for_codes(codes: list[str]) -> dict[str, pd.Series]:
    """仅拉取自选可能所在分市场的快照，避免 stock_zh_a_spot_em 全表耗时。"""
    boards: set[str] = set()
    for c in codes:
        boards.update(_boards_for_code(c))
    fn_map = {
        "bj": ak.stock_bj_a_spot_em,
        "cy": ak.stock_cy_a_spot_em,
        "kc": ak.stock_kc_a_spot_em,
        "sh": ak.stock_sh_a_spot_em,
        "sz": ak.stock_sz_a_spot_em,
    }
    parts: list[pd.DataFrame] = []
    for key in ("bj", "kc", "cy", "sh", "sz"):
        if key not in boards:
            continue
        try:
            parts.append(_retry_call(fn_map[key]))
        except Exception:
            continue
    return _merge_spot_maps(parts)


def _stock_name_em(symbol: str) -> str | None:
    try:
        df = _retry_call(
            lambda: ak.stock_individual_info_em(symbol=symbol),
            attempts=4,
            base_sleep=0.3,
            max_sleep=4.0,
        )
        row = df[df["item"] == "股票简称"]
        if not row.empty:
            return str(row["value"].iloc[0]).strip().replace(" ", "")
    except Exception:
        return None
    return None


def _fetch_hist_daily(symbol: str, lookback_days: int = 400) -> pd.DataFrame:
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - pd.Timedelta(days=lookback_days)).strftime("%Y%m%d")
    try:
        df = _retry_call(
            lambda: ak.stock_zh_a_hist(
                symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq"
            ),
            attempts=5,
            base_sleep=0.5,
            max_sleep=6.0,
        )
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    rename = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "pct",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    for c in ("open", "close", "high", "low"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    return df


def _verdict_and_hints(
    close: float,
    rsi_v: float | None,
    sma20_v: float | None,
    sma60_v: float | None,
    macd_line: float | None,
    macd_sig: float | None,
    macd_hist: float | None,
    ret20: float | None,
    ret60: float | None,
) -> tuple[float, str, str, str]:
    """
    简单打分与文字提示（规则透明，便于自行调整）。
    score 约落在 [-2, 2]，越大越偏多。
    """
    score = 0.0
    if ret20 is not None:
        score += float(np.clip(ret20 / 30.0, -0.5, 0.5))
    if ret60 is not None:
        score += float(np.clip(ret60 / 40.0, -0.5, 0.5))
    if rsi_v is not None:
        if rsi_v < 35:
            score += 0.6
        elif rsi_v > 70:
            score -= 0.7
        elif 45 <= rsi_v <= 60:
            score += 0.15
    if sma20_v is not None and sma60_v is not None and sma20_v > sma60_v:
        score += 0.35
    elif sma20_v is not None and sma60_v is not None and sma20_v < sma60_v:
        score -= 0.35
    if close and sma20_v:
        if close > sma20_v:
            score += 0.2
        else:
            score -= 0.2
    if macd_line is not None and macd_sig is not None:
        if macd_line > macd_sig and (macd_hist or 0) > 0:
            score += 0.25
        elif macd_line < macd_sig:
            score -= 0.25

    if score >= 0.75:
        verdict = "偏多（观察）"
    elif score <= -0.75:
        verdict = "偏空（谨慎）"
    else:
        verdict = "中性"

    buy_parts: list[str] = []
    if rsi_v is not None and rsi_v < 40:
        buy_parts.append("RSI 处于相对低位，可关注是否出现企稳或放量反弹")
    if sma20_v is not None:
        buy_parts.append(
            f"若盘中回踩 MA20（约 {sma20_v:.2f}）附近缩量企稳，可作为分批介入的参考窗口（非保证）"
        )
    if macd_line is not None and macd_sig is not None and macd_line > macd_sig:
        buy_parts.append("MACD 线在信号线上方，短线动能偏多时可考虑顺势；勿追高")
    if not buy_parts:
        buy_parts.append("无强烈超卖信号：若参与请控制仓位并设止损")

    sell_parts: list[str] = []
    if rsi_v is not None and rsi_v > 68:
        sell_parts.append("RSI 偏高，可考虑分批止盈或收紧止损")
    if sma20_v is not None:
        sell_parts.append(f"若收盘价连续跌破 MA20（约 {sma20_v:.2f}），可作为减仓或止损参考")
    if macd_line is not None and macd_sig is not None and macd_line < macd_sig:
        sell_parts.append("MACD 死叉区域，注意回调风险")
    if not sell_parts:
        sell_parts.append("暂无强烈超买/破位信号：持仓者可移动止盈跟踪趋势")

    return (
        float(np.clip(score, -2.0, 2.0)),
        verdict,
        "；".join(buy_parts[:3]),
        "；".join(sell_parts[:3]),
    )


def analyze_symbol(
    code: str,
    spot_row: pd.Series | None,
    name_fallback: str | None = None,
) -> SymbolInsight | None:
    hist = _fetch_hist_daily(code)
    if hist.empty or "close" not in hist.columns:
        return None
    close_s = hist["close"]
    rsi_s = sig.rsi(close_s, 14)
    sma20_s = sig.sma(close_s, 20)
    sma60_s = sig.sma(close_s, 60)
    macd_line, macd_sig, macd_hist = sig.macd(close_s)

    last_close = float(close_s.iloc[-1])
    rsi_v = sig.last_valid(rsi_s)
    sma20_v = sig.last_valid(sma20_s)
    sma60_v = sig.last_valid(sma60_s)
    ml = sig.last_valid(macd_line)
    ms = sig.last_valid(macd_sig)
    mh = sig.last_valid(macd_hist)

    if len(close_s) >= 21:
        ret20 = (last_close / float(close_s.iloc[-21]) - 1.0) * 100
    else:
        ret20 = None
    if len(close_s) >= 61:
        ret60 = (last_close / float(close_s.iloc[-61]) - 1.0) * 100
    else:
        ret60 = None

    if spot_row is not None and "name" in spot_row and pd.notna(spot_row["name"]):
        name = str(spot_row["name"]).strip()
    elif name_fallback:
        name = name_fallback
    else:
        name = code
    last_price = None
    pct_day = None
    if spot_row is not None:
        if "last" in spot_row and pd.notna(spot_row["last"]):
            last_price = float(spot_row["last"])
        if "pct" in spot_row and pd.notna(spot_row["pct"]):
            pct_day = float(spot_row["pct"])

    sc, verdict, buy_h, sell_h = _verdict_and_hints(
        last_close, rsi_v, sma20_v, sma60_v, ml, ms, mh, ret20, ret60
    )

    return SymbolInsight(
        code=code,
        name=name,
        last_price=last_price,
        pct_change_day=pct_day,
        rsi14=rsi_v,
        sma20=sma20_v,
        sma60=sma60_v,
        macd_hist=mh,
        ret_20d_pct=ret20,
        ret_60d_pct=ret60,
        signal_score=sc,
        verdict=verdict,
        buy_timing_hint=buy_h,
        sell_timing_hint=sell_h,
    )


def run_analysis(
    watchlist_path: str | None = None,
    top_n: int = 8,
    json_out: str | None = None,
    use_spot: bool = True,
    fetch_names: bool = True,
) -> list[dict[str, Any]]:
    wl_path = Path(watchlist_path) if watchlist_path else Path(__file__).resolve().parent.parent / "data" / "a_share_watchlist.txt"
    codes = _read_watchlist(wl_path)
    if not codes:
        codes = _default_watchlist()

    print(DISCLAIMER_CN)
    print(f"分析时间（服务器本地）: {datetime.now().isoformat(timespec='seconds')}")
    print(f"标的数量: {len(codes)}（来自 {wl_path} 或内置示例）\n")

    spot_by_code: dict[str, pd.Series] = {}
    if use_spot:
        try:
            spot_by_code = fetch_spot_for_codes(codes)
            if not spot_by_code:
                print("[警告] 分市场快照为空，将尝试不依赖盘中价继续分析。\n")
        except Exception as ex:  # pragma: no cover
            print(f"[警告] 未能获取实时行情: {ex}\n")
    else:
        if fetch_names:
            print("[信息] 已跳过实时快照（--no-spot），仅用日线收盘价；名称将从个股信息接口补充。\n")
        else:
            print("[信息] 已跳过实时快照（--no-spot），且未请求简称（--no-names）。\n")

    name_cache: dict[str, str] = {}
    if fetch_names:
        for code in codes:
            r = spot_by_code.get(code)
            has_name = r is not None and "name" in r and pd.notna(r.get("name"))
            if not has_name:
                nm = _stock_name_em(code)
                if nm:
                    name_cache[code] = nm

    insights: list[SymbolInsight] = []
    for code in codes:
        row = spot_by_code.get(code)
        ins = analyze_symbol(code, row, name_fallback=name_cache.get(code))
        if ins:
            insights.append(ins)
        else:
            print(f"[跳过] {code}：日线数据暂不可用（网络或数据源异常）\n")

    insights.sort(key=lambda x: x.signal_score, reverse=True)
    picks = insights[: max(1, top_n)]

    for i, ins in enumerate(picks, 1):
        print(f"--- [{i}] {ins.code} {ins.name} ---")
        if ins.last_price is not None:
            print(f"  现价(盘中): {ins.last_price:.2f}", end="")
            if ins.pct_change_day is not None:
                print(f"  当日涨跌: {ins.pct_change_day:.2f}%", end="")
            print()
        print(
            f"  日线收盘参考 | RSI14: {ins.rsi14 if ins.rsi14 is not None else '—'} | "
            f"MA20: {ins.sma20 if ins.sma20 is not None else '—'} | "
            f"MA60: {ins.sma60 if ins.sma60 is not None else '—'}"
        )
        if ins.ret_20d_pct is not None:
            print(f"  近20日涨跌: {ins.ret_20d_pct:.2f}%", end="")
        if ins.ret_60d_pct is not None:
            print(f"  | 近60日: {ins.ret_60d_pct:.2f}%", end="")
        print()
        print(f"  综合倾向: {ins.verdict}（score={ins.signal_score:.2f}）")
        print(f"  买入时机参考: {ins.buy_timing_hint}")
        print(f"  卖出时机参考: {ins.sell_timing_hint}")
        print()

    print("【交易时段说明】中国 A 股连续竞价通常为交易日 9:30–11:30、13:00–15:00；")
    print("可在开盘前准备标的，9:30 后结合盘口与分时再执行计划。\n")

    out_list = [asdict(x) for x in picks]
    if json_out:
        outp = Path(json_out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(out_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写入 JSON: {outp}")

    return out_list


def main() -> None:
    p = argparse.ArgumentParser(description="中国 A 股技术面日度分析（akshare）")
    p.add_argument("--watchlist", type=str, default=None, help="自选列表文件路径")
    p.add_argument("--top", type=int, default=8, help="推荐展示数量")
    p.add_argument("--json", type=str, default=None, help="结果 JSON 输出路径")
    p.add_argument(
        "--no-spot",
        action="store_true",
        help="不拉取分市场快照，仅用日线数据",
    )
    p.add_argument(
        "--no-names",
        action="store_true",
        help="不调用个股信息接口补全简称（可加快运行）",
    )
    args = p.parse_args()
    run_analysis(
        watchlist_path=args.watchlist,
        top_n=args.top,
        json_out=args.json,
        use_spot=not args.no_spot,
        fetch_names=not args.no_names,
    )


if __name__ == "__main__":
    main()
