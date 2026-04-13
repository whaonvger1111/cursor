#!/usr/bin/env python3
"""
A 股日线级「交易助手」脚本：基于公开行情做技术面筛选与信号说明。

重要：输出仅为基于历史与当日公开数据的规则化分析，不构成投资建议。
实盘买卖时点、仓位与合规要求请咨询持牌机构并自行决策。

定时示例（请在本机 crontab 中配置；机器时区建议为 Asia/Shanghai）::

    30 9 * * 1-5 cd /path/to/repo && python3 trading_agent/a_share_agent.py --pick 12 >> /tmp/a_share_agent.log 2>&1

盘中可改用 ``--watch --interval 600`` 在上海交易时段内循环运行（每次仍会拉全市场快照，耗时较长）。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError as e:  # pragma: no cover
    print("请先安装: pip install akshare", file=sys.stderr)
    raise SystemExit(1) from e

CN_TZ = ZoneInfo("Asia/Shanghai")


def _now_cn() -> datetime:
    return datetime.now(tz=CN_TZ)


def _is_cn_trading_hours(dt: datetime | None = None) -> bool:
    t = dt or _now_cn()
    if t.weekday() >= 5:
        return False
    hm = t.hour * 60 + t.minute
    morning = 9 * 60 + 30 <= hm <= 11 * 60 + 30
    afternoon = 13 * 60 <= hm <= 15 * 60
    return morning or afternoon


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


@dataclass
class SignalResult:
    code: str
    name: str
    action_hint: str
    reason: str
    extra: dict[str, Any]


def fetch_spot_universe() -> pd.DataFrame:
    df = ak.stock_zh_a_spot_em()
    # 统一列名便于处理
    rename = {
        "代码": "code",
        "名称": "name",
        "最新价": "last",
        "昨收": "prev_close",
        "涨跌幅": "pct_chg",
        "成交额": "amount",
        "量比": "vol_ratio",
        "换手率": "turnover",
        "流通市值": "float_mv",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    needed = ["code", "name", "last", "pct_chg", "amount", "vol_ratio", "turnover"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"行情表缺少列: {c}")
    for col in ["last", "pct_chg", "amount", "vol_ratio", "turnover"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "prev_close" in df.columns:
        df["prev_close"] = pd.to_numeric(df["prev_close"], errors="coerce")
        # 非交易时段常见：最新价/涨跌幅为空，但昨收仍可用，用昨收近似「参考价」
        fill_prev = df["last"].isna() & df["prev_close"].notna() & (df["prev_close"] > 0)
        df.loc[fill_prev, "last"] = df.loc[fill_prev, "prev_close"]
        need_pct = df["pct_chg"].isna() & df["last"].notna() & df["prev_close"].notna()
        need_pct &= df["prev_close"] > 0
        df.loc[need_pct, "pct_chg"] = (
            (df.loc[need_pct, "last"] - df.loc[need_pct, "prev_close"])
            / df.loc[need_pct, "prev_close"]
            * 100.0
        )
    df = df.dropna(subset=["last", "pct_chg"])
    df = df[df["last"] > 0]
    # 排除 ST / 退市等明显高风险名称
    mask_name = ~df["name"].astype(str).str.contains("ST", case=False, na=False)
    df = df[mask_name]
    # 避免追涨停与极端波动（可调）
    df = df[(df["pct_chg"] > -9.9) & (df["pct_chg"] < 9.9)]
    return df


def screen_candidates(df: pd.DataFrame, top_liquid: int = 400, pick: int = 15) -> pd.DataFrame:
    """先按成交额取流动性头部，再按量比排序取候选。"""
    liq = df.sort_values("amount", ascending=False).head(top_liquid).copy()
    liq["vol_ratio"] = pd.to_numeric(liq["vol_ratio"], errors="coerce")
    liq = liq.dropna(subset=["vol_ratio"])
    liq = liq[liq["vol_ratio"] > 0]
    scored = liq.sort_values(["vol_ratio", "amount"], ascending=[False, False])
    return scored.head(pick)


def analyze_daily(symbol: str, name: str) -> SignalResult:
    """
    日线信号（简化）：
    - 买入倾向：收盘站上 MA20 且 MA5>MA20，RSI 未严重超买
    - 卖出/减仓倾向：收盘跌破 MA5 或 RSI 严重超买后走弱
    """
    hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
    if hist is None or len(hist) < 30:
        return SignalResult(
            code=symbol,
            name=name,
            action_hint="数据不足",
            reason="历史 K 线过短或无法获取。",
            extra={},
        )
    hist = hist.rename(
        columns={
            "日期": "date",
            "收盘": "close",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
    )
    for c in ["close", "open", "high", "low", "volume"]:
        hist[c] = pd.to_numeric(hist[c], errors="coerce")
    hist = hist.dropna(subset=["close"])
    hist = hist.sort_values("date")
    close = hist["close"]
    ma5 = _sma(close, 5)
    ma20 = _sma(close, 20)
    rsi = _rsi(close, 14)
    last = close.iloc[-1]
    prev = close.iloc[-2] if len(close) > 1 else last
    m5, m20 = float(ma5.iloc[-1]), float(ma20.iloc[-1])
    r = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0

    reasons: list[str] = []
    score_buy = 0
    score_sell = 0

    if last > m20 and m5 > m20:
        score_buy += 2
        reasons.append("短期均线位于中期均线上方（多头结构）")
    if last < m20:
        score_sell += 1
        reasons.append("收盘低于 MA20（偏空）")
    if m5 < m20:
        score_sell += 1
        reasons.append("MA5 低于 MA20（趋势走弱）")
    if r < 35:
        score_buy += 1
        reasons.append(f"RSI={r:.1f} 偏低（超卖区附近）")
    if r > 70:
        score_sell += 2
        reasons.append(f"RSI={r:.1f} 偏高（超买风险）")

    if last < float(ma5.iloc[-1]) and last < prev:
        score_sell += 1
        reasons.append("收于 MA5 下方且弱于前一日")

    if score_buy >= 3 and score_sell <= 1:
        action = "偏多（规则化）"
        timing = (
            "若参与：可考虑在日线收盘确认仍站上 MA20 后分批；"
            "盘中仅作参考，勿单点押注。"
        )
    elif score_sell >= 3:
        action = "偏空或减仓（规则化）"
        timing = "若持仓：可结合跌破 MA5/MA20 与 RSI 高位回落执行纪律；具体时点以您策略为准。"
    else:
        action = "中性/观望（规则化）"
        timing = "信号冲突或不明朗，宜减少操作频率。"

    extra = {
        "last_close": float(last),
        "ma5": m5,
        "ma20": m20,
        "rsi14": r,
        "last_date": str(hist["date"].iloc[-1]),
    }
    return SignalResult(
        code=symbol,
        name=name,
        action_hint=action,
        reason="；".join(reasons) if reasons else "规则未触发强信号。",
        extra={"timing_hint": timing, **extra},
    )


def run_once(top_liquid: int, pick: int, out_json: Path | None) -> dict[str, Any]:
    t0 = time.time()
    universe = fetch_spot_universe()
    candidates = screen_candidates(universe, top_liquid=top_liquid, pick=pick)
    results: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        code = str(row["code"]).zfill(6)
        name = str(row["name"])
        time.sleep(0.15)  # 轻微间隔，降低源站压力
        sig = analyze_daily(code, name)
        results.append(
            {
                "code": sig.code,
                "name": sig.name,
                "spot_pct_chg": float(row["pct_chg"]),
                "spot_amount": float(row["amount"]) if pd.notna(row["amount"]) else None,
                "signal": sig.action_hint,
                "detail": sig.reason,
                **sig.extra,
            }
        )

    payload: dict[str, Any] = {
        "generated_at": _now_cn().isoformat(),
        "trading_hours_cn": _is_cn_trading_hours(),
        "disclaimer": "本输出为自动化规则与公开数据，不构成投资建议。",
        "candidates": results,
        "elapsed_sec": round(time.time() - t0, 2),
    }
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def print_report(payload: dict[str, Any]) -> None:
    print("=" * 72)
    print(f"生成时间（上海）：{payload['generated_at']}")
    print(f"A 股交易时段内：{'是' if payload['trading_hours_cn'] else '否'}")
    print(payload["disclaimer"])
    print("=" * 72)
    for item in payload["candidates"]:
        print(
            f"\n{item['code']} {item['name']} | 当日涨跌幅: {item['spot_pct_chg']:.2f}% "
            f"| 信号: {item['signal']}"
        )
        print(f"  说明: {item['detail']}")
        if "timing_hint" in item:
            print(f"  时点提示: {item['timing_hint']}")
        if "last_close" in item:
            print(
                f"  收盘参考: {item['last_close']:.3f} | MA5={item['ma5']:.3f} | "
                f"MA20={item['ma20']:.3f} | RSI14={item['rsi14']:.1f} | 数据日={item.get('last_date')}"
            )
    print("\n" + "=" * 72)
    print(f"耗时: {payload['elapsed_sec']}s")


def watch_loop(interval_sec: int, top_liquid: int, pick: int) -> None:
    """在交易时段内周期性重复分析（每次都会拉全市场快照，耗时较长）。"""
    print("监视模式：将在上海交易时段内每隔一段时间运行一次；Ctrl+C 退出。")
    while True:
        if not _is_cn_trading_hours():
            print(f"[{_now_cn().strftime('%H:%M:%S')}] 非交易时段，{interval_sec}s 后重试…")
            time.sleep(interval_sec)
            continue
        try:
            payload = run_once(top_liquid=top_liquid, pick=pick, out_json=None)
            print_report(payload)
        except Exception as e:  # pragma: no cover
            print(f"本轮失败: {e}", file=sys.stderr)
        time.sleep(interval_sec)


def main() -> None:
    p = argparse.ArgumentParser(description="A 股日线级规则化筛选与信号（非投资建议）")
    p.add_argument("--top-liquid", type=int, default=400, help="流动性预筛数量")
    p.add_argument("--pick", type=int, default=12, help="最终分析股票数量")
    p.add_argument("--out-json", type=str, default="", help="可选：写出 JSON 路径")
    p.add_argument("--watch", action="store_true", help="交易时段内循环运行")
    p.add_argument("--interval", type=int, default=600, help="监视模式间隔（秒）")
    args = p.parse_args()

    out_path = Path(args.out_json) if args.out_json else None

    if args.watch:
        watch_loop(interval_sec=args.interval, top_liquid=args.top_liquid, pick=args.pick)
    else:
        payload = run_once(top_liquid=args.top_liquid, pick=args.pick, out_json=out_path)
        print_report(payload)
        if out_path:
            print(f"\n已写入: {out_path.resolve()}")


if __name__ == "__main__":
    main()
