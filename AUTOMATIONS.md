# Cursor Automations：定时运行交易提示

Cursor 的 **Automations** 在网页上创建（[cursor.com/automations](https://cursor.com/automations)），**无法通过本仓库里的配置文件代你完成「一键开通」**。请按下面步骤在 **Automations** 里新建一条自动化；本仓库提供 **可直接执行的脚本** 与 **可复制的中文提示词**。

## 前置条件

1. 本仓库已关联 GitHub，且 Cursor 能对该仓库运行 **Cloud Agents**。
2. 在 [Cloud Agents 环境变量](https://cursor.com/dashboard/cloud-agents) 中为**该仓库**配置 **`OPENAI_API_KEY`**（使用 OpenAI 时）。若改用其他 LLM，需在 TradingAgents 配置与密钥中自行对齐。
3. Automations 会按 **Cloud Agent 用量**计费，见官方文档。

## 在 Automations 里创建（推荐：定时）

1. 打开 [新建 Automation](https://cursor.com/automations/new) 或 Automations 列表中的 **New**。
2. **Repository / Branch**：选本仓库与要跑的分支（如 `main`）。
3. **Trigger**：选 **Scheduled**，用 cron 表达「每个工作日 9:00（中国时间）」时，请在 Automations 里选 **Asia/Shanghai** 时区（若界面提供），或使用等价 cron；若只支持「每天」再辅以提示词说明「仅工作日有效」——**精确排除法定节假日需自行维护日历或在本机用任务计划程序**。
4. **Environment**：开启 **安装依赖**（与文档中 *Environment / 依赖安装* 一致），以便 `pip install -e` 能执行。
5. **Prompt（提示词）**：复制下面「提示词模板」。
6. **Tools**：按需勾选（通常需要能执行命令、写仓库、必要时 **Open pull request** 若要把日志提交进分支）。
7. 保存并启用。

## 提示词模板（复制到 Automation 的 Prompt）

```text
你是本仓库的自动化助手。每次触发时请在仓库根目录执行：

  bash scripts/run_trading_signal_cloud.sh

要求：
1. 若 bash 脚本不存在则报告错误并停止。
2. 脚本会克隆 TauricResearch/TradingAgents 到 tradingagents_vendor/（若尚不存在），安装依赖，并运行 tools/auto_trading_signal_tradingagents.py 生成 JSON 信号到 trading_signal_logs/。
3. 执行成功后，将本次生成的 JSON 摘要（ticker、trade_date、decision）写入提交说明，并打开一个 Pull Request，标题为 "chore: trading signal log"，仅包含 trading_signal_logs/ 下新增或变更的文件；若没有文件变更则说明原因。
4. 不要提交 OPENAI_API_KEY 或任何密钥；密钥仅来自 Cloud Agent 环境变量。

说明：输出为研究/模拟用途，不构成投资建议。
```

可按需删掉「开 PR」一句，若只希望生成日志文件、不提交到 Git。

## 脚本说明

| 文件 | 作用 |
|------|------|
| `scripts/run_trading_signal_cloud.sh` | 克隆 TradingAgents、安装、设置 `TRADINGAGENTS_ROOT`、调用 `tools/auto_trading_signal_tradingagents.py` |
| `tools/auto_trading_signal_tradingagents.py` | 实际调用多智能体图并写 JSON |

环境变量（可在 Cloud Agents 里配置）：

- `TRADING_SIGNAL_TICKERS`：如 `600519.SS,000001.SZ`
- `TRADING_SIGNAL_OUTPUT_DIR`：日志目录，默认仓库内 `trading_signal_logs/`
- `TRADING_SIGNAL_TIMEZONE`：默认 `Asia/Shanghai`

## 与本机 Windows 定时任务的关系

- **Automations**：云端按调度跑 Cloud Agent，适合「仓库里留痕 + PR」。
- **tools/windows/**：本机 Windows 任务计划，适合「自己电脑 9 点跑、不落库」。二者可同时使用，注意别重复消耗 API 配额。

## 参考文档

- [Cursor Automations](https://cursor.com/docs/cloud-agent/automations.md)
- [TradingAgents 上游](https://github.com/TauricResearch/TradingAgents)
