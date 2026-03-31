@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ========== 请按本机情况修改 ==========
set "TRADINGAGENTS_ROOT=C:\Users\Administrator\Desktop\TradingAgents-main"
REM 本仓库 tools 目录的上一级为仓库根；脚本位于 tools\auto_trading_signal_tradingagents.py
for %%I in ("%~dp0..") do set "TOOLS_DIR=%%~fI"
set "RUNNER=%TOOLS_DIR%\auto_trading_signal_tradingagents.py"
set "PYTHON=py -3"
REM 若无 py 启动器，可改为: set "PYTHON=python"

REM 若已将 RUNNER 复制到 TradingAgents 根目录，可改为直接指向：
REM set "RUNNER=%TRADINGAGENTS_ROOT%\auto_trading_signal_tradingagents.py"

if not exist "%RUNNER%" (
  echo 未找到: %RUNNER%
  echo 请从本仓库复制 tools\auto_trading_signal_tradingagents.py，或修改本 bat 中的 RUNNER。
  exit /b 1
)

set "TRADING_SIGNAL_TIMEZONE=Asia/Shanghai"
set "TRADING_SIGNAL_TICKERS=600519.SS"
set "TRADING_SIGNAL_OUTPUT_DIR=%TRADINGAGENTS_ROOT%\trading_signal_logs"

set "TRADINGAGENTS_ROOT=%TRADINGAGENTS_ROOT%"
cd /d "%TRADINGAGENTS_ROOT%"

echo [%date% %time%] 开始运行交易提示...
%PYTHON% "%RUNNER%" --once --output-language Chinese --tickers "%TRADING_SIGNAL_TICKERS%" --output-dir "%TRADING_SIGNAL_OUTPUT_DIR%"
set EXITCODE=!ERRORLEVEL!
echo [%date% %time%] 结束，退出码=!EXITCODE!
exit /b !EXITCODE!
