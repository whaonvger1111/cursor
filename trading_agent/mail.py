"""
通过 SMTP 发送纯文本邮件（QQ 邮箱等）。

需在环境中配置：
  A_SHARE_SMTP_HOST   默认 smtp.qq.com
  A_SHARE_SMTP_PORT   默认 465（SSL）
  A_SHARE_SMTP_USER   发件邮箱（与 QQ 账号一致）
  A_SHARE_SMTP_PASSWORD  QQ 邮箱「授权码」，非登录密码
  A_SHARE_SMTP_FROM   可选，默认与 USER 相同
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_text_email(
    subject: str,
    body: str,
    to_addrs: list[str],
) -> None:
    host = os.environ.get("A_SHARE_SMTP_HOST", "smtp.qq.com").strip()
    port = int(os.environ.get("A_SHARE_SMTP_PORT", "465"))
    user = os.environ.get("A_SHARE_SMTP_USER", "").strip()
    password = os.environ.get("A_SHARE_SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("A_SHARE_SMTP_FROM", user).strip()

    if not user or not password:
        raise ValueError(
            "未配置发件邮箱：请设置环境变量 A_SHARE_SMTP_USER 与 "
            "A_SHARE_SMTP_PASSWORD（QQ 邮箱请使用网页端生成的授权码）。"
        )
    if not to_addrs:
        raise ValueError("收件人列表为空。")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body, subtype="plain", charset="utf-8")

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
