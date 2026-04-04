"""A-share oriented news/sentiment helpers via yfinance Search (Chinese queries)."""

from __future__ import annotations

from datetime import datetime

import yfinance as yf
from dateutil.relativedelta import relativedelta

from .stockstats_utils import yf_retry
from .yfinance_news import _extract_article_data
from .config import get_config


def _normalize_ticker_code(ticker: str) -> str:
    """600519.SS -> 600519"""
    t = ticker.strip().upper()
    if "." in t:
        return t.split(".", 1)[0]
    return t


def get_company_display_name(ticker: str) -> str:
    """Best-effort Chinese/English name from yfinance info."""
    try:
        info = yf_retry(lambda: yf.Ticker(ticker).info) or {}
    except Exception:
        return ""
    for key in ("longName", "shortName", "symbol"):
        v = info.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def search_news_digest(
    queries: list[str],
    curr_date: str,
    look_back_days: int,
    limit: int,
    header: str,
) -> str:
    """Run yfinance Search for multiple queries, dedupe, filter by date."""
    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")

    all_news: list[dict] = []
    seen: set[str] = set()

    try:
        for query in queries:
            if len(all_news) >= limit:
                break
            search = yf_retry(
                lambda q=query: yf.Search(
                    query=q,
                    news_count=min(15, limit),
                    enable_fuzzy_query=True,
                )
            )
            if not search.news:
                continue
            for article in search.news:
                if "content" in article:
                    data = _extract_article_data(article)
                    title = data["title"]
                else:
                    title = article.get("title", "") or ""

                if not title or title in seen:
                    continue

                if "content" in article:
                    data = _extract_article_data(article)
                    if data.get("pub_date"):
                        pub = data["pub_date"]
                        pub_naive = pub.replace(tzinfo=None) if hasattr(pub, "replace") else pub
                        if pub_naive > curr_dt + relativedelta(days=1):
                            continue
                seen.add(title)
                all_news.append(article)

        if not all_news:
            return f"{header}\n\n（未检索到相关条目，可能为数据源暂时为空或关键词无匹配。）"

        lines: list[str] = [
            header + "\n",
            f"_检索窗口: {start_date} ~ {curr_date}（尽力按发布时间过滤）_\n\n",
        ]
        for article in all_news[:limit]:
            if "content" in article:
                data = _extract_article_data(article)
                title = data["title"]
                publisher = data["publisher"]
                link = data["link"]
                summary = data["summary"]
            else:
                title = article.get("title", "No title")
                publisher = article.get("publisher", "Unknown")
                link = article.get("link", "")
                summary = article.get("summary", "")

            lines.append(f"### {title}（来源: {publisher}）\n")
            if summary:
                lines.append(f"{summary}\n")
            if link:
                lines.append(f"链接: {link}\n")
            lines.append("\n")

        return "".join(lines)

    except Exception as e:
        return f"{header}\n\n检索出错: {type(e).__name__}: {e}"


def get_a_share_macro_news_yfinance(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 12,
) -> str:
    """
    面向 A 股的宏观与政策类新闻检索（中文关键词 + 少量英文补充）。
    """
    queries = [
        "A股 市场 政策",
        "中国证监会 交易所",
        "中国人民银行 降准 降息",
        "沪深300 北向资金",
        "China stock market policy",
    ]
    header = "## A股/中国资本市场 — 宏观与政策舆情摘要（yfinance 检索）"
    return search_news_digest(queries, curr_date, look_back_days, limit, header)


def get_a_share_company_social_digest_yfinance(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 15,
) -> str:
    """
    个股在中文语境下的讨论与新闻摘要（公司名 + 代码 + 舆情关键词）。
    说明：来自公开网页摘要，非实时股吧帖子全文；可作情绪与话题线索。
    """
    code = _normalize_ticker_code(ticker)
    name = get_company_display_name(ticker) or code

    queries = [
        f"{name} 股票 最新消息",
        f"{code} A股 股吧",
        f"{name} 业绩 公告",
        f"{name} 雪球",
        f"{name} 东方财富",
    ]

    curr_date = end_date
    header = f"## A股个股舆情与媒体报道摘要 — `{ticker}`（{name} / {code}）"
    return search_news_digest(queries, curr_date, 7, limit, header)


def get_a_share_macro_news_combined(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 12,
) -> str:
    """yfinance 宏观检索 + 可选 AkShare（央视/财新等）。"""
    parts: list[str] = [get_a_share_macro_news_yfinance(curr_date, look_back_days, limit)]
    cfg = get_config()
    if cfg.get("a_share_use_akshare"):
        try:
            from .a_share_akshare import get_a_share_portal_macro_digest_akshare

            parts.append(get_a_share_portal_macro_digest_akshare(curr_date))
        except Exception as e:
            parts.append(f"\n\n（中文门户宏观摘要拉取失败: {type(e).__name__}: {e}）")
    return "\n\n---\n\n".join(parts)


def get_a_share_company_social_combined(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 15,
) -> str:
    """yfinance 检索 + 可选 AkShare（东财个股新闻与情绪指标）。"""
    parts: list[str] = [
        get_a_share_company_social_digest_yfinance(ticker, start_date, end_date, limit)
    ]
    cfg = get_config()
    if cfg.get("a_share_use_akshare"):
        try:
            from .a_share_akshare import get_a_share_portal_company_digest_akshare

            parts.append(
                get_a_share_portal_company_digest_akshare(
                    ticker, start_date, end_date, news_limit=max(limit, 20)
                )
            )
        except Exception as e:
            parts.append(f"\n\n（中文门户个股摘要拉取失败: {type(e).__name__}: {e}）")
    return "\n\n---\n\n".join(parts)
