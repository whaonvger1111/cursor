"""Score and rank multi-signal scan results."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from a_share_monitor.markets import board_label
from a_share_monitor.signals import Signal

STRENGTH_SCORE = {"strong": 3, "medium": 2, "weak": 1}


@dataclass
class RankedStock:
    code: str
    name: str
    board: str
    price: float
    buy_score: int = 0
    sell_score: int = 0
    buy_signals: list[str] = field(default_factory=list)
    sell_signals: list[str] = field(default_factory=list)

    @property
    def net_score(self) -> int:
        return self.buy_score - self.sell_score


def rank_signals(signals: list[Signal], boards: dict[str, str] | None = None) -> list[RankedStock]:
    grouped: dict[str, RankedStock] = {}

    for signal in signals:
        if signal.code not in grouped:
            grouped[signal.code] = RankedStock(
                code=signal.code,
                name=signal.name,
                board=(boards or {}).get(signal.code, ""),
                price=signal.price,
            )
        row = grouped[signal.code]
        points = STRENGTH_SCORE.get(signal.strength, 1)
        label = f"{signal.signal_type}: {signal.detail}"
        if signal.direction == "BUY":
            row.buy_score += points
            row.buy_signals.append(label)
        else:
            row.sell_score += points
            row.sell_signals.append(label)

    ranked = sorted(grouped.values(), key=lambda r: (r.net_score, r.buy_score), reverse=True)
    return ranked


def format_ranked(row: RankedStock, index: int) -> str:
    board = board_label(row.board) if row.board else "未知板块"
    buys = "；".join(row.buy_signals) if row.buy_signals else "-"
    sells = "；".join(row.sell_signals) if row.sell_signals else "-"
    return (
        f"{index:>2}. {row.code} {row.name} [{board}] "
        f"price={row.price:.2f} net={row.net_score:+d} "
        f"(buy={row.buy_score}, sell={row.sell_score})\n"
        f"     BUY : {buys}\n"
        f"     SELL: {sells}"
    )
