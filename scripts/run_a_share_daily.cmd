@echo off
setlocal EnableExtensions
REM 每日 A 股辅助分析 — 供「任务计划程序」调用
REM 用法：在仓库根目录外也可双击/调度；日志默认 tools\reports\a_share\cron.log

set "ROOT=%~dp0.."
pushd "%ROOT%" >nul 2>&1 || (echo Cannot cd to repo root & exit /b 1)

set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py -3"

if exist "%ROOT%venv\Scripts\python.exe" set "PY=%ROOT%venv\Scripts\python.exe"

set "LOG_DIR=%ROOT%tools\reports\a_share"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\cron.log"

REM 可选：在 %USERPROFILE%\.config\a_share_env.bat 中写 set A_SHARE_SMTP_USER=...
if exist "%USERPROFILE%\.config\a_share_env.bat" (
  call "%USERPROFILE%\.config\a_share_env.bat"
)

echo ======== %date% %time% ========>>"%LOG_FILE%"

if defined A_SHARE_SMTP_USER if defined A_SHARE_SMTP_PASSWORD (
  "%PY%" "%ROOT%tools\a_share_daily_email.py" %* >>"%LOG_FILE%" 2>&1
) else (
  "%PY%" "%ROOT%tools\a_share_daily_email.py" --dry-run %* >>"%LOG_FILE%" 2>&1
)

set "EC=%ERRORLEVEL%"
popd >nul 2>&1
exit /b %EC%
