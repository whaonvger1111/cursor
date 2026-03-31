#!/usr/bin/env bash
# 供 Cursor Cloud Agent / Automations 在仓库内一键运行交易提示脚本。
# 在 Cloud Agents 后台为仓库配置 OPENAI_API_KEY（及可选变量）后执行本脚本。
#
# 可选环境变量：
#   TRADING_SIGNAL_TICKERS   默认 600519.SS
#   TRADING_SIGNAL_OUTPUT_DIR 默认 <repo>/trading_signal_logs
#   TRADING_SIGNAL_TIMEZONE  默认 Asia/Shanghai
#   TRADINGAGENTS_VENDOR_DIR  TradingAgents 克隆目录，默认 <repo>/tradingagents_vendor/TradingAgents
#   TRADINGAGENTS_GIT_URL     默认 https://github.com/TauricResearch/TradingAgents.git

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
VENDOR_ROOT="${TRADINGAGENTS_VENDOR_DIR:-$REPO_ROOT/tradingagents_vendor/TradingAgents}"
GIT_URL="${TRADINGAGENTS_GIT_URL:-https://github.com/TauricResearch/TradingAgents.git}"
RUNNER="$REPO_ROOT/tools/auto_trading_signal_tradingagents.py"

if [[ ! -f "$RUNNER" ]]; then
  echo "找不到 $RUNNER" >&2
  exit 1
fi

if [[ ! -d "$VENDOR_ROOT/tradingagents" ]]; then
  mkdir -p "$(dirname "$VENDOR_ROOT")"
  echo "克隆 TradingAgents -> $VENDOR_ROOT"
  git clone --depth 1 "$GIT_URL" "$VENDOR_ROOT"
fi

echo "安装 TradingAgents 依赖..."
python3 -m pip install -q -e "$VENDOR_ROOT"
python3 -m pip install -q "python-dotenv>=1.0.0"

export TRADINGAGENTS_ROOT="$VENDOR_ROOT"
export TRADING_SIGNAL_TIMEZONE="${TRADING_SIGNAL_TIMEZONE:-Asia/Shanghai}"
export TRADING_SIGNAL_TICKERS="${TRADING_SIGNAL_TICKERS:-600519.SS}"
export TRADING_SIGNAL_OUTPUT_DIR="${TRADING_SIGNAL_OUTPUT_DIR:-$REPO_ROOT/trading_signal_logs}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "错误: 请在 Cloud Agents 环境变量中设置 OPENAI_API_KEY。" >&2
  exit 1
fi

echo "运行交易提示: tickers=$TRADING_SIGNAL_TICKERS"
python3 "$RUNNER" --once --output-language Chinese \
  --tickers "$TRADING_SIGNAL_TICKERS" \
  --output-dir "$TRADING_SIGNAL_OUTPUT_DIR"

echo "完成。日志目录: $TRADING_SIGNAL_OUTPUT_DIR"
