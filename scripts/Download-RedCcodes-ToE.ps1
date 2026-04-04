#Requires -Version 5.0
<#
.SYNOPSIS
    将 IDEAS「RED Computer Codes」系列复制包与论文元数据下载到本机（默认 E:\red_ccodes_download）。

.DESCRIPTION
    依赖同目录下的 download_red_ccodes.py。请先安装 Python 3，并确保能执行 pip。
    若执行策略禁止运行脚本，可在 PowerShell（管理员）中执行：
      Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

.PARAMETER OutDir
    输出目录，默认 E:\red_ccodes_download

.PARAMETER Resume
    断点续传（跳过 manifest 中已记录的 item_id）

.EXAMPLE
    .\Download-RedCcodes-ToE.ps1
.EXAMPLE
    .\Download-RedCcodes-ToE.ps1 -OutDir "D:\data\red_ccodes" -Resume
#>
param(
    [string]$OutDir = "E:\red_ccodes_download",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

function Find-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ Exe = "python"; PrefixArgs = @() }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Exe = "py"; PrefixArgs = @("-3") }
    }
    return $null
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyFile = Join-Path $ScriptDir "download_red_ccodes.py"
if (-not (Test-Path -LiteralPath $PyFile)) {
    Write-Error "找不到 $PyFile。请在本仓库中运行本脚本（scripts 目录下应有 download_red_ccodes.py）。"
}

$py = Find-Python
if ($null -eq $py) {
    Write-Error "未找到 Python。请从 https://www.python.org/downloads/ 安装 Python 3，并勾选 Add Python to PATH。"
}

Write-Host "使用 Python: $($py.Exe) $($py.PrefixArgs -join ' ')" -ForegroundColor Cyan
Write-Host "输出目录: $OutDir" -ForegroundColor Cyan

# 确保 requests
$pipArgs = $py.PrefixArgs + @("-m", "pip", "install", "-q", "requests>=2.28")
& $py.Exe @pipArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install requests 失败。请手动执行: pip install requests"
}

$runArgs = $py.PrefixArgs + @($PyFile, "--out", $OutDir, "--delay", "0.25")
if ($Resume) {
    $runArgs += "--resume"
}

Write-Host "开始下载（耗时与网速、磁盘有关，整包可能为数十 GB）..." -ForegroundColor Yellow
& $py.Exe @runArgs
exit $LASTEXITCODE
