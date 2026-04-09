#!/usr/bin/env python3
"""
每日运行 A 股辅助分析，将结果保存到本地并可选通过 QQ 邮箱 SMTP 发送。

敏感信息（SMTP 授权码）必须通过环境变量提供，勿写入代码或提交到 git。
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
import sys
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TZ_SH = ZoneInfo("Asia/Shanghai")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_REPORT_DIR = REPO_ROOT / "tools" / "reports" / "a_share"


def _today_cst() -> date:
    return datetime.now(TZ_SH).date()


def _is_weekday(d: date) -> bool:
    return d.weekday() < 5


def load_previous_payload(report_dir: Path, today: date) -> dict[str, Any] | None:
    """加载「上一交易日」已保存的报告（按文件名 YYYY-MM-DD.json）。"""
    if not report_dir.is_dir():
        return None
    files = sorted(report_dir.glob("*.json"))
    if not files:
        return None
    # 取今天之前最近一份
    prev: Path | None = None
    for p in reversed(files):
        stem = p.stem
        try:
            d = date.fromisoformat(stem)
        except ValueError:
            continue
        if d < today:
            prev = p
            break
    if prev is None:
        return None
    try:
        return json.loads(prev.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def diff_candidates(
    prev: dict[str, Any] | None, curr: dict[str, Any]
) -> str:
    if not prev:
        return "（无上一交易日保存的报告，无法对比；自明天起会自动对比。）"
    prev_set = {
        (str(c.get("symbol")), str(c.get("name")))
        for c in (prev.get("candidates") or [])
    }
    curr_list = curr.get("candidates") or []
    curr_set = {(str(c.get("symbol")), str(c.get("name"))) for c in curr_list}

    added = curr_set - prev_set
    removed = prev_set - curr_set
    lines = []
    if added:
        lines.append("较上一保存日 新增关注: " + ", ".join(f"{s} {n}" for s, n in sorted(added)))
    else:
        lines.append("较上一保存日 新增关注: 无")
    if removed:
        lines.append("较上一保存日 不再在列表中: " + ", ".join(f"{s} {n}" for s, n in sorted(removed)))
    else:
        lines.append("较上一保存日 不再在列表中: 无")
    return "\n".join(lines)


def save_report(report_dir: Path, today: date, payload: dict[str, Any]) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / f"{today.isoformat()}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def send_qq_email(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    to_addrs: list[str],
    subject: str,
    body: str,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=60) as server:
        server.login(user, password)
        server.send_message(msg)


def main() -> int:
    p = argparse.ArgumentParser(description="A 股日度分析 + 邮件发送")
    p.add_argument("--hot-top", type=int, default=25)
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--symbols", type=str, default="", help="自选代码，逗号分隔；非空则不用热度榜")
    p.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="JSON 报告保存目录",
    )
    p.add_argument(
        "--skip-weekends",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="周末不拉行情、不发送（默认开启）",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成报告并打印，不发送邮件",
    )
    args = p.parse_args()

    today = _today_cst()
    if args.skip_weekends and not _is_weekday(today):
        print(f"今日 {today} 非工作日，已跳过（--skip-weekends）。")
        return 0

    # 延迟导入，避免仅查看 --help 时拉 akshare
    from tools.a_share_trading_agent import report_text_from_payload, run_analysis

    prev_payload = load_previous_payload(args.report_dir, today)
    payload = run_analysis(args.hot_top, args.top_k, args.symbols)
    diff_block = diff_candidates(prev_payload, payload)
    out_path = save_report(args.report_dir, today, payload)

    body_text = report_text_from_payload(payload, args.top_k)
    full_body = (
        body_text
        + "\n\n"
        + "-" * 60
        + "\n与上一保存日对比\n"
        + diff_block
        + "\n\n"
        + f"JSON 已保存: {out_path}"
    )

    if args.dry_run:
        print(full_body)
        return 0

    smtp_host = os.environ.get("A_SHARE_SMTP_HOST", "smtp.qq.com")
    smtp_port = int(os.environ.get("A_SHARE_SMTP_PORT", "465"))
    smtp_user = os.environ.get("A_SHARE_SMTP_USER", "").strip()
    smtp_pass = os.environ.get("A_SHARE_SMTP_PASSWORD", "").strip()
    mail_to = os.environ.get("A_SHARE_MAIL_TO", "36269216@qq.com").strip()

    if not smtp_user or not smtp_pass:
        print(
            "错误: 未设置邮箱发送凭据。请设置环境变量:\n"
            "  A_SHARE_SMTP_USER=你的QQ邮箱@qq.com\n"
            "  A_SHARE_SMTP_PASSWORD=QQ邮箱SMTP授权码（非登录密码）\n"
            "可选: A_SHARE_SMTP_HOST / A_SHARE_SMTP_PORT / A_SHARE_MAIL_TO",
            file=sys.stderr,
        )
        print(full_body)
        return 2

    to_list = [x.strip() for x in mail_to.replace(";", ",").split(",") if x.strip()]
    subject = f"A股日度辅助分析 {today.isoformat()}（非投资建议）"
    send_qq_email(
        host=smtp_host,
        port=smtp_port,
        user=smtp_user,
        password=smtp_pass,
        to_addrs=to_list,
        subject=subject,
        body=full_body,
    )
    print(f"已发送邮件至: {', '.join(to_list)}")
    print(f"报告已保存: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
