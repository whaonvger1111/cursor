@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title A股脚本 - 一键安装（venv + 依赖 + 可选定时任务）

set "ROOT=%~dp0.."
pushd "%ROOT%" || (echo 无法进入仓库目录: %ROOT% & pause & exit /b 1)

echo.
echo ========================================
echo  A 股辅助分析 - Windows 一键安装
echo  仓库: %ROOT%
echo ========================================
echo.

REM --- 查找 Python ---
set "PY=py -3"
where py >nul 2>&1
if errorlevel 1 (
  set "PY=python"
  where python >nul 2>&1
  if errorlevel 1 (
    echo [错误] 未找到 Python。请先安装 Python 3.10+ 并勾选 "Add to PATH"。
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
  )
)

echo [1/3] 使用解释器: %PY%
%PY% --version || (echo Python 执行失败 & pause & exit /b 1)

echo.
echo [2/3] 创建虚拟环境 venv 并安装 requirements.txt ...
if not exist "%ROOT%venv\Scripts\python.exe" (
  %PY% -m venv "%ROOT%venv" || (echo venv 创建失败 & pause & exit /b 1)
)

"%ROOT%venv\Scripts\python.exe" -m pip install --upgrade pip -q
"%ROOT%venv\Scripts\pip.exe" install -r "%ROOT%requirements.txt" || (
  echo pip 安装失败
  pause
  exit /b 1
)

echo.
echo 验证导入 akshare ...
"%ROOT%venv\Scripts\python.exe" -c "import akshare; print('akshare', akshare.__version__)" || (
  echo 验证失败
  pause
  exit /b 1
)

echo.
echo [3/3] 依赖安装完成。
echo.

REM --- 可选：注册任务计划（需本机支持 schtasks；多数用户无需管理员）---
if /i "%~1"=="schedule" goto DO_SCHEDULE
if /i "%~1"=="task" goto DO_SCHEDULE
if /i "%~1"=="--schedule" goto DO_SCHEDULE
goto NO_SCHEDULE

:DO_SCHEDULE
set "TASK_NAME=AShareDaily"
set "TASK_SCRIPT=%ROOT%scripts\run_a_share_daily.cmd"
echo 正在注册计划任务 "%TASK_NAME%"（每天 09:40 触发；周末由 Python 脚本 --skip-weekends 跳过）...
echo 若失败，可尝试右键本脚本「以管理员身份运行」并重试: install_a_share_windows.bat schedule

schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
REM /tr 用一对引号包住完整路径，路径含空格时也可行
schtasks /create /tn "%TASK_NAME%" /tr "\"%TASK_SCRIPT%\"" /sc daily /st 09:40 /f
if errorlevel 1 (
  echo [警告] schtasks 注册失败，请打开「任务计划程序」按 scripts\TASK_SCHEDULER_WINDOWS.md 手动添加。
) else (
  echo 已注册。查看: schtasks /query /tn "%TASK_NAME%"
  echo 删除: schtasks /delete /tn "%TASK_NAME%" /f
)
goto END

:NO_SCHEDULE
echo 未注册定时任务。若需要每天自动运行，请执行:
echo   scripts\install_a_share_windows.bat schedule
echo 或阅读 scripts\TASK_SCHEDULER_WINDOWS.md 手动添加。
echo.

:END
echo 手动测试（约 1～3 分钟，需联网）:
echo   "%ROOT%venv\Scripts\python.exe" "%ROOT%tools\a_share_daily_email.py" --dry-run
echo 日志目录: %ROOT%tools\reports\a_share\
echo.
popd
pause
exit /b 0
