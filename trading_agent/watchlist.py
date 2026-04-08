"""自选池：每行一个代码，可含 # 注释与空行。"""

from __future__ import annotations

from pathlib import Path


def load_watchlist(path: Path) -> list[str]:
    if not path.is_file():
        return []
    codes: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split()[0].strip()
        if token.isdigit() or (len(token) == 6 and token.isalnum()):
            codes.append(token.zfill(6))
    return codes
