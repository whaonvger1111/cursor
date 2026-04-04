"""
中文财经门户数据（可选）：通过 AkShare 聚合东方财富、财新主站头条、央视网要闻等公开接口。

需安装: pip install akshare
接口随数据源变更可能波动；仅供研究，不构成投资建议。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd


def _import_akshare():
    try:
        import akshare as ak  # noqa: F401

        return __import__("akshare", fromlist=["akshare"])
    except ImportError:
        return None


def _normalize_code(ticker: str) -> str:
    t = ticker.strip().upper()
    if "." in t:
        return t.split(".", 1)[0]
    return t


def _parse_cn_time(s) -> Optional[pd.Timestamp]:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    try:
        return pd.to_datetime(str(s), errors="coerce")
    except Exception:
        return None


def format_eastmoney_stock_news(
    symbol_code: str,
    start_date: str,
    end_date: str,
    limit: int = 25,
) -> str:
    """东方财富 个股新闻（stock_news_em），按时间窗口过滤。"""
    ak = _import_akshare()
    if ak is None:
        return "（未安装 akshare，无法拉取东方财富新闻。请: pip install akshare）"

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    try:
        df = ak.stock_news_em(symbol=symbol_code)
    except Exception as e:
        return f"东方财富个股新闻获取失败: {type(e).__name__}: {e}"

    if df is None or df.empty:
        return f"东方财富：未返回 `{symbol_code}` 的新闻数据。"

    time_col = "发布时间" if "发布时间" in df.columns else df.columns[3]
    title_col = "新闻标题" if "新闻标题" in df.columns else df.columns[1]
    body_col = "新闻内容" if "新闻内容" in df.columns else df.columns[2]
    src_col = "文章来源" if "文章来源" in df.columns else df.columns[4]
    link_col = "新闻链接" if "新闻链接" in df.columns else df.columns[5]

    rows: list[str] = [
        f"## 东方财富 — 个股新闻摘要（代码 {symbol_code}）",
        f"_窗口: {start_date} ~ {end_date}_\n",
    ]
    n = 0
    for _, r in df.iterrows():
        ts = _parse_cn_time(r.get(time_col))
        if ts is not None and pd.notna(ts):
            if ts < start or ts >= end:
                continue
        title = str(r.get(title_col, "")).strip()
        if not title:
            continue
        body = str(r.get(body_col, "")).strip()[:500]
        src = str(r.get(src_col, "")).strip()
        link = str(r.get(link_col, "")).strip()
        tss = str(r.get(time_col, "")).strip()
        block = f"### {title}\n"
        if tss:
            block += f"_时间_: {tss}  _来源_: {src}\n"
        if body:
            block += f"{body}\n"
        if link:
            block += f"链接: {link}\n"
        block += "\n"
        rows.append(block)
        n += 1
        if n >= limit:
            break

    if n == 0:
        return (
            f"## 东方财富 — 个股新闻（{symbol_code}）\n\n"
            f"在 {start_date}~{end_date} 窗口内无条目（或时间字段无法解析）。"
        )
    return "".join(rows)


def format_eastmoney_sentiment_metrics(symbol_code: str, days: int = 30) -> str:
    """东方财富衍生情绪/关注度：用户关注指数、综合评分（日线序列末值）。"""
    ak = _import_akshare()
    if ak is None:
        return "（未安装 akshare，无法拉取东财情绪指标。请: pip install akshare）"

    parts: list[str] = [f"## 东方财富 — 情绪与关注度指标（{symbol_code}）\n"]

    try:
        df_focus = ak.stock_comment_detail_scrd_focus_em(symbol=symbol_code)
        if df_focus is not None and not df_focus.empty and len(df_focus) >= 2:
            tail = df_focus.tail(min(days, len(df_focus)))
            c_date = "交易日" if "交易日" in tail.columns else tail.columns[0]
            c_val = "用户关注指数" if "用户关注指数" in tail.columns else tail.columns[1]
            last = tail.iloc[-1]
            prev = tail.iloc[-2]
            parts.append(
                f"- **用户关注指数**（近日）: 最新 {last[c_val]}（{last[c_date]}），"
                f"前一日 {prev[c_val]}（{prev[c_date]}）\n"
            )
    except Exception as e:
        parts.append(f"- 用户关注指数: 获取失败 ({type(e).__name__}: {e})\n")

    try:
        df_score = ak.stock_comment_detail_zhpj_lspf_em(symbol=symbol_code)
        if df_score is not None and not df_score.empty and len(df_score) >= 1:
            tail = df_score.tail(min(days, len(df_score)))
            c_date = "交易日" if "交易日" in tail.columns else tail.columns[0]
            c_val = "评分" if "评分" in tail.columns else tail.columns[1]
            last = tail.iloc[-1]
            parts.append(
                f"- **市场综合评分**（东财衍生）: 最新 {last[c_val]:.4f}（{last[c_date]}）\n"
            )
    except Exception as e:
        parts.append(f"- 综合评分: 获取失败 ({type(e).__name__}: {e})\n")

    parts.append(
        "\n_说明：以上为数据源聚合指标，非订单流；请结合公告与基本面解读。_\n"
    )
    return "".join(parts)


def format_cctv_news_brief(curr_date: str, limit: int = 8) -> str:
    """央视网 `news_cctv` 当日要闻（偏政策/宏观语境）。"""
    ak = _import_akshare()
    if ak is None:
        return "（未安装 akshare）"

    try:
        d = datetime.strptime(curr_date, "%Y-%m-%d").strftime("%Y%m%d")
        df = ak.news_cctv(date=d)
    except Exception as e:
        return f"央视网要闻获取失败: {type(e).__name__}: {e}"

    if df is None or df.empty:
        return f"央视网：{curr_date} 无要闻数据。"

    lines = [f"## 央视网 — 要闻摘要（{curr_date}）\n"]
    col_title = "title" if "title" in df.columns else df.columns[1]
    col_content = "content" if "content" in df.columns else df.columns[2]
    for _, r in df.head(limit).iterrows():
        t = str(r.get(col_title, "")).strip()
        c = str(r.get(col_content, "")).strip()[:400]
        if t:
            lines.append(f"### {t}\n{c}\n\n")
    return "".join(lines)


def format_caixin_main_headlines(limit: int = 10) -> str:
    """财新主站 `stock_news_main_cx` 头条类摘要（宏观与市场话题）。"""
    ak = _import_akshare()
    if ak is None:
        return "（未安装 akshare）"

    try:
        df = ak.stock_news_main_cx()
    except Exception as e:
        return f"财新主站头条获取失败: {type(e).__name__}: {e}"

    if df is None or df.empty:
        return "财新主站：暂无头条数据。"

    lines = ["## 财新 — 主站头条/摘要（AkShare）\n"]
    for _, r in df.head(limit).iterrows():
        tag = str(r.get("tag", "")).strip()
        summary = str(r.get("summary", "")).strip()
        url = str(r.get("url", "")).strip()
        head = tag or "条目"
        lines.append(f"### {head}\n")
        if summary:
            lines.append(f"{summary}\n")
        if url:
            lines.append(f"链接: {url}\n")
        lines.append("\n")
    return "".join(lines)


def get_a_share_portal_macro_digest_akshare(curr_date: str, limit_cctv: int = 8, limit_cx: int = 8) -> str:
    """宏观向：央视当日 + 财新头条（中文门户）。"""
    a = format_cctv_news_brief(curr_date, limit=limit_cctv)
    b = format_caixin_main_headlines(limit=limit_cx)
    return a + "\n\n" + b


def get_a_share_portal_company_digest_akshare(
    ticker: str,
    start_date: str,
    end_date: str,
    news_limit: int = 20,
) -> str:
    """个股向：东财新闻 + 东财情绪指标。"""
    code = _normalize_code(ticker)
    a = format_eastmoney_stock_news(code, start_date, end_date, limit=news_limit)
    b = format_eastmoney_sentiment_metrics(code, days=30)
    return a + "\n\n" + b
