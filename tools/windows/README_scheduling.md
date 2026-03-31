TradingAgents 每个交易日早上 9:00 自动运行（Windows）

1. 编辑 run_trading_signal_daily.bat
   - TRADINGAGENTS_ROOT：您的 TradingAgents-main 路径
   - TRADING_SIGNAL_TICKERS：逗号分隔，A 股 Yahoo 格式如 600519.SS
   - PYTHON：本机 Python 命令（py -3 或 python）

2. 确保已 pip install TradingAgents 且 .env 中有 OPENAI_API_KEY 等。

3. 注册计划任务（任选其一）
   A) PowerShell（推荐）
      在 tools\windows 目录打开 PowerShell，执行：
      Set-ExecutionPolicy -Scope Process Bypass -Force
      .\register_task.ps1

   B) 手动
      打开「任务计划程序」→ 创建任务 → 触发器「每周」周一到周五 09:00 →
      操作「启动程序」→ 程序填 cmd.exe，参数 /c "完整路径\run_trading_signal_daily.bat"。

说明
- 「工作日」此处按周一至周五；春节等休市日仍会触发，需自行在任务计划程序中禁用当日或删除单次触发。
- 触发时间使用 Windows 本机时区；中国用户请将系统时区设为中国标准时间，使 09:00 为本地开盘前习惯时间。
- 脚本内 TRADING_SIGNAL_TIMEZONE=Asia/Shanghai，保证「今天」的日期按中国时区。
- 日志 JSON 默认在 %TRADINGAGENTS_ROOT%\trading_signal_logs
