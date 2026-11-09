"""晚筛口径单元测试（不连网）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics import a_hits_of, board_of, is_gap_up_over, is_power_stock, metrics_from_bars
from screens import _sleeve_sets, pick_tech, pick_value_by_board, score_row


def _bars(closes: list[float], pcts: list[float] | None = None) -> list[dict]:
    out = []
    for i, c in enumerate(closes):
        prev = closes[i - 1] if i else c
        pct = pcts[i] if pcts else (c / prev - 1.0) * 100
        out.append(
            {
                "date": f"2026-08-{(i % 28) + 1:02d}",
                "open": c,
                "close": c,
                "high": c,
                "low": c,
                "volume": 1e6,
                "amount": 5e7,
                "pct": pct,
                "turnover": 1.0,
            }
        )
    return out


def test_board_of() -> None:
    assert board_of("601318") == "主板"
    assert board_of("000429") == "主板"
    assert board_of("300926") == "创业板"
    assert board_of("688275") == "科创板"
    assert board_of("689009") is None


def test_power_vs_equipment() -> None:
    assert is_power_stock("长江电力", "水力发电") is True
    assert is_power_stock("国电南瑞", "电网设备") is False
    assert is_power_stock("中国核电", "核力发电") is True


def test_gap_up_gate() -> None:
    assert is_gap_up_over(10.20, 10.00) is True
    assert is_gap_up_over(10.10, 10.00) is True
    assert is_gap_up_over(10.09, 10.00) is False
    assert is_gap_up_over(9.90, 10.00) is False


def test_a_hits_full_two() -> None:
    closes = [100.0] * 40 + [100.0 - i for i in range(1, 21)]  # 滑落到 80，低于 MA20
    m = metrics_from_bars(_bars(closes))
    hits = a_hits_of(m)
    assert "①" in hits
    assert "②" in hits


def test_value_main_requires_net_net() -> None:
    extra = {"oil_codes": [], "opt_codes": [], "ai_codes": [], "power_codes": [], "zt": {}}
    cheap = {
        "code": "600001",
        "name": "测试破净",
        "board": "主板",
        "industry": "钢铁",
        "pe": 8.0,
        "pb": 0.7,
        "close": 5.0,
        "open": 5.0,
        "prev_close": 5.0,
        "pct": 0.0,
        "mcap": 2e10,
        "bars": _bars([5.0] * 60),
    }
    rich = dict(cheap, code="600002", name="测试溢价", pb=1.2)
    scored = [score_row(cheap, extra), score_row(rich, extra)]
    med = {"主板": {"pe": 15.0, "pb": 1.4}, "创业板": {"pe": 30.0, "pb": 2.5}, "科创板": {"pe": 40.0, "pb": 3.0}}
    picked, funnel = pick_value_by_board(scored, med)
    codes = {x["code"] for x in picked["主板"]}
    assert "600001" in codes
    assert "600002" not in codes
    assert funnel["pass_gate"]["主板"] == 1


def test_tech_skips_value_and_held() -> None:
    extra = {"oil_codes": [], "opt_codes": [], "ai_codes": [], "power_codes": [], "zt": {}}
    # gently above MA20: last 20 avg ~10, last close 10.3
    closes = [9.7] * 40 + [10.0 + i * 0.01 for i in range(20)]
    row = {
        "code": "002001",
        "name": "测试均线",
        "board": "主板",
        "industry": "化工",
        "pe": 12.0,
        "pb": 1.2,
        "close": closes[-1],
        "open": closes[-1],
        "prev_close": closes[-2],
        "pct": 0.3,
        "mcap": 3e10,
        "bars": _bars(closes),
    }
    scored = [score_row(row, extra)]
    picked_overlap, funnel_overlap = pick_tech(scored, {"002001"})
    assert picked_overlap == []
    assert funnel_overlap["kicked_value_overlap"] == 1
    picked_ok, _ = pick_tech(scored, set())
    assert any(x["code"] == "002001" for x in picked_ok)


def test_optical_bk_not_bloated() -> None:
    oil, opt, ai, power = _sleeve_sets(
        {
            "oil_codes": ["601872"],
            "opt_codes": ["002475"] + [f"300{i:03d}" for i in range(50)],
            "ai_codes": ["000725"],
            "power_codes": ["600900"],
        }
    )
    assert "002475" not in opt  # 立讯不是光模块
    assert "300308" in opt  # 中际旭创代码兜底
    assert "601872" in oil
    assert "000725" in ai


if __name__ == "__main__":
    test_board_of()
    test_power_vs_equipment()
    test_gap_up_gate()
    test_a_hits_full_two()
    test_value_main_requires_net_net()
    test_tech_skips_value_and_held()
    test_optical_bk_not_bloated()
    print("ok")
