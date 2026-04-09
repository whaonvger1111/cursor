# Windows 任务计划程序 — 每日运行 A 股辅助分析

## 0. 一键安装（推荐）

在资源管理器中进入仓库的 `scripts` 文件夹，**双击** `install_a_share_windows.bat`（或在 cmd 里执行 `scripts\install_a_share_windows.bat`）。

脚本会自动：创建 `venv`、安装 `requirements.txt`、验证 `akshare`。

- 若还要**自动注册每天 09:40 的任务**：在同一目录打开 cmd，执行  
  `install_a_share_windows.bat schedule`  
  （失败时可右键「以管理员身份运行」再试，或按下文手动添加任务。）

仍需本机已安装 **Python 3**（安装时勾选 Add to PATH）。脚本无法替你下载 Python。

## 1. 环境（手动）

- 安装 **Python 3**，在仓库目录执行：`pip install -r requirements.txt`  
- （可选）`python -m venv venv`，之后 `run_a_share_daily.cmd` 会优先使用 `venv\Scripts\python.exe`

## 2. 发邮件（可选）

复制 `scripts\a_share_env.example.bat` 为：

`%USERPROFILE%\.config\a_share_env.bat`

用记事本填入 QQ 邮箱与 **SMTP 授权码**，保存。

不配发信时，任务仍会运行并写日志（等同 `--dry-run`）。

## 3. 创建任务

打开 **任务计划程序** → **创建任务**（建议不用「创建基本任务」）

| 页签 | 设置 |
|------|------|
| **常规** | 名称随意（如 `AShareDaily`）；如需可勾选「使用最高权限运行」 |
| **触发器** | **每天** 开始时间 **09:40**；若需仅工作日，在触发器里选「每周」周一～周五，或每天触发后由脚本侧接受周末数据（当前脚本默认周末可跳过，见 `a_share_daily_email.py` 的 `--skip-weekends`） |
| **操作** | 程序：`cmd.exe` |
| | 参数：`/c "D:\你的路径\cursor\scripts\run_a_share_daily.cmd"`（把路径换成你的仓库**绝对路径**） |
| | 起始于（可选）：`D:\你的路径\cursor` |
| **条件** | 笔记本可取消「仅交流电源」 |

> 说明：`run_a_share_daily.cmd` 会调用 `tools\a_share_daily_email.py`。若未配置 SMTP，会自动加 `--dry-run`。

## 4. 输出位置

- 运行日志：`tools\reports\a_share\cron.log`
- 每日 JSON：`tools\reports\a_share\YYYY-MM-DD.json`

## 5. 手动测试

```cmd
cd /d D:\你的路径\cursor
scripts\run_a_share_daily.cmd
```

再打开 `tools\reports\a_share\cron.log` 查看。

## 6. 仅工作日

任务触发器设为 **每周**、周一～周五；或保持每天触发（周末也会跑，但 `a_share_daily_email.py` 默认 `--skip-weekends` 会在周末打印「已跳过」）。
