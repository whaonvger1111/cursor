#!/usr/bin/env bash
# 每日 A 股辅助分析（供 crontab / 任务计划调用）
# 用法：在项目外也可执行；自动定位仓库根目录。
# 可选：export A_SHARE_ENV_FILE=/path/to/env 指向含 SMTP 变量的文件（chmod 600）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export TZ="${TZ:-Asia/Shanghai}"

PY="${PYTHON:-python3}"
if [[ -x "$ROOT/venv/bin/python3" ]]; then
  PY="$ROOT/venv/bin/python3"
fi
LOG_DIR="$ROOT/tools/reports/a_share"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_FILE:-$LOG_DIR/cron.log}"

ENV_FILE="${A_SHARE_ENV_FILE:-$HOME/.config/a_share_env}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

{
  echo "======== $(date '+%Y-%m-%d %H:%M:%S %z') ========"
  if [[ -n "${A_SHARE_SMTP_USER:-}" && -n "${A_SHARE_SMTP_PASSWORD:-}" ]]; then
    "$PY" "$ROOT/tools/a_share_daily_email.py" "$@"
  else
    # 未配置发信：仍保存 JSON 并写入日志（与 --dry-run 一致）
    "$PY" "$ROOT/tools/a_share_daily_email.py" --dry-run "$@"
  fi
} >>"$LOG_FILE" 2>&1
