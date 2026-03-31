# 向「任务计划程序」注册：周一至周五 09:00 运行 run_trading_signal_daily.bat
# 使用前请编辑 run_trading_signal_daily.bat 中的路径与股票代码。
# 在 PowerShell 中执行： .\register_task.ps1

$ErrorActionPreference = "Stop"
$bat = Join-Path $PSScriptRoot "run_trading_signal_daily.bat"
if (-not (Test-Path -LiteralPath $bat)) {
    Write-Error "找不到: $bat"
}

$taskName = "TradingAgents_DailySignal_0900"
$arg = "/c `"$bat`""
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $arg
# 每个工作日 09:00（系统本地时区；请将 Windows 时区设为中国或您所在交易时区）
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At (Get-Date -Hour 9 -Minute 0 -Second 0)

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force | Out-Null
Write-Host "已注册任务: $taskName （周一至周五 09:00，使用本机时区）"
Write-Host "请确认 Windows 时区与交易时区一致（中国用户建议设为中国标准时间）。"
Write-Host "查看: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "删除: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
