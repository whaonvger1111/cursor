#!/usr/bin/env python3
"""
Fetch IDEAS/RePEc RED 'Computer Codes' series, parse metadata, filter macro-related
entries, write JSONL + summary. Respects RePEc guidance: modest delay between requests.

Does NOT bulk-download replication zips by default (use download_red_ccodes.py).
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

BASE = "https://ideas.repec.org"
LIST_PAGES = [
    f"{BASE}/s/red/ccodes.html",
    f"{BASE}/s/red/ccodes2.html",
    f"{BASE}/s/red/ccodes3.html",
    f"{BASE}/s/red/ccodes4.html",
]
DELAY_SEC = 0.35

# Quantitative / aggregate macro: JEL chapter E (macro) + common open-economy macro F4*
MACRO_JEL_PREFIXES = tuple(f"E{i}" for i in range(10)) + ("F4", "F3", "F2")


@dataclass
class CodeItem:
    id: str
    handle: str
    ideas_code_url: str
    title: str
    programming_language: str
    jel_codes: list[str]
    jel_labels: list[str]
    paper_url: str | None
    paper_title_guess: str | None
    file_urls: list[str]
    abstract: str | None
    macro_related: bool
    macro_reason: str


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "repec-red-index/1.0 (research; contact: local)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_list_page(html: str) -> list[tuple[str, str]]:
    """Return list of (id, title) e.g. ('23-118', 'Monetary policy...')."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(
        r'href="/c/red/ccodes/([^"/]+)\.html">Code and data files for &quot;([^&]+)&quot;',
        html,
        re.I,
    ):
        cid, title = m.group(1), html_unescape(m.group(2))
        out.append((cid, title))
    return out


def html_unescape(s: str) -> str:
    return (
        s.replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


def parse_code_page(html: str, cid: str) -> dict[str, Any]:
    handle_m = re.search(
        r"Handle:\s*<i[^>]*>(RePEc:red:ccodes:[^<]+)</i>", html, re.I
    )
    handle = handle_m.group(1).strip() if handle_m else f"RePEc:red:ccodes:{cid}"

    # Programming language: buttons right after Programming Language h2
    pl_block = re.search(
        r"Programming Language</h2>(.*?)<h2 style=\"clear:left\">Abstract</h2>",
        html,
        re.S,
    )
    langs: list[str] = []
    if pl_block:
        for bm in re.finditer(r'class="link-button">([^<]+)</button>', pl_block.group(1)):
            t = bm.group(1).strip()
            if t and t not in langs:
                langs.append(t)
    programming_language = "; ".join(langs) if langs else ""

    abs_m = re.search(
        r'<div id="abstract-body">(.*?)</div>', html, re.S
    )
    abstract = re.sub(r"<[^>]+>", "", abs_m.group(1)).strip() if abs_m else None

    jel_codes: list[str] = []
    jel_labels: list[str] = []
    for jm in re.finditer(
        r'<A HREF="/j/([A-Z][0-9]+)\.html"><B>([^<]+)</B></A>\s*-\s*([^<]+)</LI>',
        html,
        re.I,
    ):
        jel_codes.append(jm.group(2))
        jel_labels.append(jm.group(3).strip())

    paper_url = None
    paper_title = None
    pm = re.search(
        r'<B><A\s+HREF="(https://ideas\.repec\.org/a/red/issued/[^"]+)">([^<]+)</A></B>',
        html,
        re.I,
    )
    if pm:
        paper_url = pm.group(1)
        paper_title = html_unescape(pm.group(2).strip())

    file_urls: list[str] = []
    for fm in re.finditer(
        r'<INPUT\s+TYPE="?radio"?\s+NAME="url"\s+VALUE="(https://[^"]+)"',
        html,
        re.I,
    ):
        u = fm.group(1)
        if u not in file_urls:
            file_urls.append(u)

    return {
        "handle": handle,
        "programming_language": programming_language,
        "jel_codes": jel_codes,
        "jel_labels": jel_labels,
        "paper_url": paper_url,
        "paper_title_guess": paper_title,
        "file_urls": file_urls,
        "abstract": abstract,
    }


def is_macro_related(jel_codes: list[str]) -> tuple[bool, str]:
    if not jel_codes:
        return True, "no_jel_assumed_macro_red_series"
    reasons: list[str] = []
    for jc in jel_codes:
        letter = jc[0] if jc else ""
        if letter == "E":
            reasons.append(jc)
            return True, "jel_E_macro"
        if jc.startswith("F2") or jc.startswith("F3") or jc.startswith("F4"):
            reasons.append(jc)
            return True, "jel_open_macro"
        if jc.startswith("Q5"):
            return True, "jel_Q5_env_macro_link"
    return False, "non_macro_jel_only"


def main() -> None:
    # .../workspace/tools/repec_red_ccodes/build_*.py -> workspace root is parents[2]
    root = Path(__file__).resolve().parents[2] / "data" / "red_ccodes"
    root.mkdir(parents=True, exist_ok=True)

    seen: dict[str, str] = {}
    for page_url in LIST_PAGES:
        time.sleep(DELAY_SEC)
        html = fetch(page_url)
        for cid, title in parse_list_page(html):
            seen[cid] = title

    items: list[CodeItem] = []
    ids_sorted = sorted(seen.keys(), key=lambda x: (len(x.split("-")[0]), x))

    for i, cid in enumerate(ids_sorted):
        url = f"{BASE}/c/red/ccodes/{cid}.html"
        time.sleep(DELAY_SEC)
        try:
            page = fetch(url)
        except Exception as e:
            items.append(
                CodeItem(
                    id=cid,
                    handle=f"RePEc:red:ccodes:{cid}",
                    ideas_code_url=url,
                    title=seen[cid],
                    programming_language="",
                    jel_codes=[],
                    jel_labels=[],
                    paper_url=None,
                    paper_title_guess=None,
                    file_urls=[],
                    abstract=None,
                    macro_related=False,
                    macro_reason=f"fetch_error:{e}",
                )
            )
            continue

        p = parse_code_page(page, cid)
        macro_ok, macro_reason = is_macro_related(p["jel_codes"])
        items.append(
            CodeItem(
                id=cid,
                handle=p["handle"],
                ideas_code_url=url,
                title=seen[cid],
                programming_language=p["programming_language"],
                jel_codes=p["jel_codes"],
                jel_labels=p["jel_labels"],
                paper_url=p["paper_url"],
                paper_title_guess=p["paper_title_guess"],
                file_urls=p["file_urls"],
                abstract=p["abstract"],
                macro_related=macro_ok,
                macro_reason=macro_reason,
            )
        )
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(ids_sorted)}", flush=True)

    all_path = root / "index_all.jsonl"
    macro_path = root / "index_macro.jsonl"
    with all_path.open("w", encoding="utf-8") as fa, macro_path.open(
        "w", encoding="utf-8"
    ) as fm:
        for it in items:
            line = json.dumps(asdict(it), ensure_ascii=False) + "\n"
            fa.write(line)
            if it.macro_related:
                fm.write(line)

    # Simple aggregates
    n_total = len(items)
    n_macro = sum(1 for it in items if it.macro_related)
    lang_counts: dict[str, int] = {}
    for it in items:
        if not it.macro_related:
            continue
        key = it.programming_language or "unknown"
        lang_counts[key] = lang_counts.get(key, 0) + 1

    summary = root / "SUMMARY.md"
    summary.write_text(
        "\n".join(
            [
                "# RED Computer Codes — 抓取摘要",
                "",
                f"- 系列页面: [RED Computer Codes](https://ideas.repec.org/s/red/ccodes.html)",
                f"- 列表条目数（去重）: **{n_total}**",
                f"- 按 JEL 筛为「宏观相关」: **{n_macro}**（无 JEL 时默认归入宏观，因该系列以动态宏观为主）",
                f"- 非宏观条目: **{n_total - n_macro}**（见 `index_all.jsonl` 中 `macro_related: false`）",
                "",
                "## 编程语言 / 环境（宏观子集，粗计数）",
                "",
                "\n".join(f"- `{k}`: {v}" for k, v in sorted(lang_counts.items(), key=lambda x: -x[1])[:25]),
                "",
                "## 数据文件",
                "",
                "- `index_all.jsonl` — 全部条目",
                "- `index_macro.jsonl` — 宏观相关条目",
                "",
                "## 说明",
                "",
                "本索引**不能**代表「全部数量宏观文献」：RePEc 中宏观论文远多于 RED 代码包；",
                "大量代码在作者主页、GitHub、Zenodo 等，未必录入 IDEAS。",
                "",
                "批量下载压缩包请使用 `tools/repec_red_ccodes/download_red_ccodes.py`（限流，慎用）。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote {all_path} ({n_total} lines)")
    print(f"Wrote {macro_path} ({n_macro} lines)")
    print(f"Wrote {summary}")


if __name__ == "__main__":
    main()
