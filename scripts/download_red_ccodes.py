#!/usr/bin/env python3
"""
从 IDEAS 上 Review of Economic Dynamics — Computer Codes 系列批量下载复制包，
并保存对应期刊论文条目的元数据（DOI、标题等）。

说明：
- “代码/数据”来自各条目 Download 区列出的直链（多为 red-files-public.s3.amazonaws.com）。
- “论文”在 IDEAS 上多为期刊条目页；正式 PDF 常标注为出版商限制访问，本脚本不尝试绕过付费墙。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

SERIES_URL = "https://ideas.repec.org/s/red/ccodes.html"
UA = (
    "Mozilla/5.0 (compatible; academic-mirror/1.0; "
    "+https://github.com/repec-org; contact=local)"
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

ITEM_PATH_RE = re.compile(r"/c/red/ccodes/([0-9]+-[0-9]+)\.html", re.I)
FILE_URL_RE = re.compile(r'NAME="url"\s+VALUE="(https?://[^"]+)"', re.I)
ISSUED_ARTICLE_RE = re.compile(
    r'href="(https://ideas\.repec\.org/a/red/issued/[0-9]+-[0-9]+\.html)"', re.I
)
DOI_META_RE = re.compile(r'<META\s+NAME="DOI"\s+CONTENT="([^"]*)"', re.I)
TITLE_META_RE = re.compile(
    r'<META\s+NAME="citation_title"\s+content="([^"]*)"', re.I
)


def fetch_text(url: str, timeout: float = 60.0) -> str:
    r = SESSION.get(url, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def list_item_ids(series_html: str) -> list[str]:
    return sorted(set(ITEM_PATH_RE.findall(series_html)))


def parse_ccodes_item(html: str) -> tuple[list[str], str | None]:
    urls = FILE_URL_RE.findall(html)
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    m = ISSUED_ARTICLE_RE.search(html)
    return out, m.group(1) if m else None


def parse_article_meta(html: str) -> dict[str, Any]:
    doi_m = DOI_META_RE.search(html)
    title_m = TITLE_META_RE.search(html)
    return {
        "doi": doi_m.group(1).strip() if doi_m else None,
        "title": title_m.group(1).strip() if title_m else None,
    }


def safe_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = Path(path).name
    if not name or name == "/":
        name = "download.bin"
    return name


def s3_request_headers(url: str, dest: Path) -> dict[str, str]:
    if "red-files-public.s3.amazonaws.com" not in url:
        return {}
    item_id = dest.parent.name
    if re.fullmatch(r"[0-9]+-[0-9]+", item_id):
        return {"Referer": f"https://ideas.repec.org/c/red/ccodes/{item_id}.html"}
    return {}


def disk_free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def load_completed_ids(manifest_path: Path) -> set[str]:
    done: set[str] = set()
    if not manifest_path.exists():
        return done
    with manifest_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                iid = row.get("item_id")
                if isinstance(iid, str):
                    done.add(iid)
            except json.JSONDecodeError:
                continue
    return done


def file_should_skip(
    url: str, dest: Path, *, no_skip: bool, min_bytes_verify: int = 1
) -> tuple[bool, int | None]:
    """若已存在且大小与 Content-Length 一致（若可得），则跳过。"""
    if no_skip or not dest.exists():
        return False, None
    size = dest.stat().st_size
    if size < min_bytes_verify:
        return False, None
    try:
        h = SESSION.head(
            url,
            timeout=45,
            allow_redirects=True,
            headers=s3_request_headers(url, dest),
        )
        h.raise_for_status()
        cl = h.headers.get("Content-Length")
        if cl is not None and int(cl) == size:
            return True, int(cl)
    except (OSError, ValueError, requests.RequestException):
        pass
    # 无 Content-Length 时：若文件非空则跳过（断点续传场景）
    return True, None


def download_file(
    url: str,
    dest: Path,
    *,
    chunk: int = 1024 * 256,
    min_free_bytes: int = 0,
    no_skip: bool = False,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    skip, _ = file_should_skip(url, dest, no_skip=no_skip)
    if skip:
        return {
            "url": url,
            "path": str(dest),
            "bytes": dest.stat().st_size,
            "skipped": True,
        }

    if tmp.exists():
        tmp.unlink()

    if min_free_bytes > 0 and disk_free_bytes(dest.parent) < min_free_bytes:
        raise OSError(
            f"磁盘剩余空间不足（需至少 {min_free_bytes} 字节）：{dest.parent}"
        )

    req_headers = s3_request_headers(url, dest)

    expected = 0
    with SESSION.get(url, timeout=300, stream=True, headers=req_headers) as r:
        r.raise_for_status()
        expected = int(r.headers.get("Content-Length") or 0)
        if max_bytes is not None and expected and expected > max_bytes:
            raise ValueError(
                f"服务器声明文件大小 {expected} 字节，超过上限 {max_bytes} 字节；"
                "疑似元数据异常，已跳过。请改用浏览器自 IDEAS 下载页核对。"
            )
        if (
            min_free_bytes > 0
            and expected
            and expected <= (max_bytes or expected)
            and disk_free_bytes(dest.parent) < expected + min_free_bytes
        ):
            raise OSError(
                f"预计下载 {expected} 字节，但磁盘空间不足：{dest.parent}"
            )
        with tmp.open("wb") as f:
            for part in r.iter_content(chunk_size=chunk):
                if part:
                    f.write(part)
    tmp.replace(dest)
    return {
        "url": url,
        "path": str(dest),
        "bytes": dest.stat().st_size,
        "content_length": expected,
        "skipped": False,
    }


def append_manifest(manifest_path: Path, row: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as mf:
        mf.write(json.dumps(row, ensure_ascii=False) + "\n")
        mf.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("/workspace/red_ccodes_download"),
        help="输出根目录",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="每条目之间的请求间隔（秒）",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="仅处理前 N 条（0 表示全部）",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="跳过 manifest.jsonl 中已记录的 item_id",
    )
    ap.add_argument(
        "--no-skip-files",
        action="store_true",
        help="即使目标文件已存在也重新下载",
    )
    ap.add_argument(
        "--min-free-gb",
        type=float,
        default=2.0,
        help="若剩余磁盘空间低于该值（GB）则中止",
    )
    ap.add_argument(
        "--max-file-gb",
        type=float,
        default=40.0,
        help="若 HTTP Content-Length 超过该值（GB）则拒绝下载（防止异常元数据占满磁盘）",
    )
    ap.add_argument(
        "--only",
        type=str,
        default="",
        help="仅处理这些 item_id（逗号分隔），例如 21-102,22-226",
    )
    ap.add_argument(
        "--manifest",
        type=str,
        default="manifest.jsonl",
        help="清单文件名（位于输出目录下），重试时可改为 manifest_retry.jsonl 以免混淆",
    )
    args = ap.parse_args()

    base: Path = args.out
    base.mkdir(parents=True, exist_ok=True)
    manifest_path = base / args.manifest
    min_free = int(max(args.min_free_gb, 0.0) * 1024**3)

    print(f"获取系列页: {SERIES_URL}", file=sys.stderr)
    series_html = fetch_text(SERIES_URL)
    item_ids = list_item_ids(series_html)
    if args.limit and args.limit > 0:
        item_ids = item_ids[: args.limit]

    only_raw = {s.strip() for s in args.only.split(",") if s.strip()}
    if only_raw:
        missing = only_raw - set(item_ids)
        if missing:
            print(f"警告：以下 id 不在系列列表中，已忽略: {sorted(missing)}", file=sys.stderr)
        item_ids = [i for i in item_ids if i in only_raw]

    max_bytes: int | None = int(max(args.max_file_gb, 0.0) * 1024**3)
    if args.max_file_gb <= 0:
        max_bytes = None

    completed: set[str] = load_completed_ids(manifest_path) if args.resume else set()
    if args.resume:
        print(f"续传：已跳过 {len(completed)} 条（自 {manifest_path}）", file=sys.stderr)

    print(f"待处理 {len([i for i in item_ids if i not in completed])} / {len(item_ids)} 条条目", file=sys.stderr)

    no_skip = args.no_skip_files
    processed = 0

    for idx, item_id in enumerate(item_ids, start=1):
        if item_id in completed:
            continue

        if min_free > 0 and disk_free_bytes(base) < min_free:
            print(f"中止：磁盘剩余空间低于 {args.min_free_gb} GB", file=sys.stderr)
            return 1

        item_url = f"https://ideas.repec.org/c/red/ccodes/{item_id}.html"
        rec: dict[str, Any] = {
            "item_id": item_id,
            "ccodes_url": item_url,
            "files": [],
            "article_url": None,
            "article_meta": None,
            "errors": [],
        }
        try:
            html = fetch_text(item_url)
            file_urls, article_url = parse_ccodes_item(html)
            rec["article_url"] = article_url

            item_dir = base / "replication" / item_id
            for furl in file_urls:
                fname = safe_filename_from_url(furl)
                dest = item_dir / fname
                try:
                    info = download_file(
                        furl,
                        dest,
                        min_free_bytes=min_free,
                        no_skip=no_skip,
                        max_bytes=max_bytes,
                    )
                    rec["files"].append(info)
                except Exception as e:  # noqa: BLE001
                    rec["errors"].append({"file": furl, "error": str(e)})

            if article_url:
                paper_dir = base / "paper_metadata" / item_id
                meta_path = paper_dir / "metadata.json"
                html_path = paper_dir / "ideas_article.html"
                try:
                    need_meta = no_skip or not meta_path.exists() or not html_path.exists()
                    if need_meta:
                        paper_dir.mkdir(parents=True, exist_ok=True)
                        art_html = fetch_text(article_url)
                        html_path.write_text(art_html, encoding="utf-8", errors="replace")
                        meta = parse_article_meta(art_html)
                        rec["article_meta"] = meta
                        meta_path.write_text(
                            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
                    else:
                        rec["article_meta"] = json.loads(
                            meta_path.read_text(encoding="utf-8")
                        )
                except Exception as e:  # noqa: BLE001
                    rec["errors"].append({"article": article_url, "error": str(e)})
        except Exception as e:  # noqa: BLE001
            rec["errors"].append({"item": item_url, "error": str(e)})

        append_manifest(manifest_path, rec)
        processed += 1
        if processed % 10 == 0 or idx == len(item_ids):
            print(
                f"进度 已写入 {processed} 条（系列序号 {idx}/{len(item_ids)}） {item_id}",
                file=sys.stderr,
            )
        time.sleep(args.delay)

    print(f"完成。清单（追加写入）: {manifest_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
