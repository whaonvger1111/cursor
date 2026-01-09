# GitHub 设置脚本
# 使用方法: .\setup_github.ps1 -RepoUrl "https://github.com/your-username/your-repo.git"

param(
    [Parameter(Mandatory=$false)]
    [string]$RepoUrl = ""
)

Write-Host "========================================"
Write-Host "GitHub 仓库设置脚本"
Write-Host "========================================"
Write-Host ""

# 切换到项目根目录
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# 检查是否已有远程仓库
$existingRemote = git remote -v 2>&1
if ($existingRemote -and $existingRemote -notmatch "fatal") {
    Write-Host "检测到已存在的远程仓库:"
    git remote -v
    Write-Host ""
    $remove = Read-Host "是否要移除现有远程仓库并添加新的? (y/n)"
    if ($remove -eq "y" -or $remove -eq "Y") {
        git remote remove origin
        Write-Host "已移除现有远程仓库"
    } else {
        Write-Host "保留现有远程仓库，退出"
        exit
    }
}

# 如果没有提供URL，提示用户输入
if ([string]::IsNullOrEmpty($RepoUrl)) {
    Write-Host "请提供GitHub仓库URL"
    Write-Host "格式示例: https://github.com/username/repo-name.git"
    Write-Host ""
    Write-Host "如果还没有创建仓库，请先:"
    Write-Host "1. 访问 https://github.com/new"
    Write-Host "2. 创建新仓库"
    Write-Host "3. 复制仓库URL"
    Write-Host ""
    $RepoUrl = Read-Host "请输入GitHub仓库URL"
}

if ([string]::IsNullOrEmpty($RepoUrl)) {
    Write-Host "错误: 未提供仓库URL"
    exit 1
}

# 添加远程仓库
Write-Host ""
Write-Host "正在添加远程仓库: $RepoUrl"
try {
    git remote add origin $RepoUrl
    Write-Host "✓ 远程仓库添加成功"
} catch {
    Write-Host "错误: 添加远程仓库失败"
    Write-Host $_.Exception.Message
    exit 1
}

# 验证远程仓库
Write-Host ""
Write-Host "当前远程仓库配置:"
git remote -v

# 检查当前分支
$currentBranch = git branch --show-current
Write-Host ""
Write-Host "当前分支: $currentBranch"

# 询问是否推送
Write-Host ""
$push = Read-Host "是否现在推送到GitHub? (y/n)"
if ($push -eq "y" -or $push -eq "Y") {
    Write-Host ""
    Write-Host "正在推送到GitHub..."
    Write-Host "注意: 如果这是第一次推送，可能需要输入GitHub用户名和Token"
    Write-Host ""
    
    try {
        git push -u origin $currentBranch
        Write-Host ""
        Write-Host "✓ 推送成功!"
        Write-Host ""
        Write-Host "您的代码现在在GitHub上:"
        $repoUrlWithoutGit = $RepoUrl -replace '\.git$', ''
        Write-Host $repoUrlWithoutGit
    } catch {
        Write-Host ""
        Write-Host "推送失败，可能的原因:"
        Write-Host "1. 需要GitHub认证（用户名和Personal Access Token）"
        Write-Host "2. 仓库不存在或没有权限"
        Write-Host "3. 网络问题"
        Write-Host ""
        Write-Host "您可以稍后手动运行: git push -u origin $currentBranch"
    }
} else {
    Write-Host ""
    Write-Host "远程仓库已配置，您可以稍后运行以下命令推送:"
    Write-Host "git push -u origin $currentBranch"
}

Write-Host ""
Write-Host "========================================"

