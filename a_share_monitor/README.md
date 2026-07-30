# A-share Trading Signal Monitor

基于技术指标的 A 股交易信号监控工具，支持一次性扫描和定时轮询。

## 安装

```bash
pip install -r a_share_monitor/requirements.txt
```

## 快速开始

### 一次性扫描自选股

```bash
python3 -m a_share_monitor.monitor scan
```

### 扫描指定股票

```bash
python3 -m a_share_monitor.monitor scan --codes 600519 000001 300750
```

### 持续监控（默认每 5 分钟轮询）

```bash
python3 -m a_share_monitor.monitor watch --interval 300
```

### 保存扫描结果

```bash
python3 -m a_share_monitor.monitor scan --output signals.json
```

## 扫描范围

默认自选股只有 5 只，所以之前看起来像「小市场」。现在支持按板块扫描**整个 A 股市场**：

| `--market` 参数 | 覆盖范围 | 约股票数量 |
|-----------------|----------|------------|
| `watchlist`（默认） | `watchlist.txt` 自选股 | 自定义 |
| `star` | **科创板**（688 开头） | ~600+ |
| `chinext` | **创业板**（300 开头） | ~900+ |
| `main` | 沪深主板（60/00 开头） | ~3400+ |
| `all` | 全 A 股（主板+科创板+创业板） | ~4900+ |
| `sh` / `sz` | 上海 / 深圳全市场 | 按交易所 |

> 说明：你说的「科幻版」通常对应 **科创板（Sci-Tech STAR Market）**；「中国版」对应 **A 股全市场**。港股、美股目前不在覆盖范围内。

### 扫描整个科创板

```bash
python3 -m a_share_monitor.monitor scan --market star --top 20
```

### 扫描整个创业板

```bash
python3 -m a_share_monitor.monitor scan --market chinext --top 20
```

### 扫描全 A 股（耗时较长，约 1 小时）

```bash
python3 -m a_share_monitor.monitor scan --market all --top 30
```

### 测试用（只扫前 100 只）

```bash
python3 -m a_share_monitor.monitor scan --market star --limit 100 --top 10
```

编辑 `a_share_monitor/watchlist.txt`，每行一个股票代码，支持：

- `600519`
- `sh600519`
- `sz000001`

## 监控信号类型

| 信号 | 方向 | 说明 |
|------|------|------|
| MA_CROSS | BUY/SELL | MA5 与 MA20 金叉/死叉 |
| MACD_CROSS | BUY/SELL | DIF 与 DEA 金叉/死叉 |
| RSI | BUY/SELL | RSI14 超卖(≤30) / 超买(≥70) |
| BREAKOUT | BUY/SELL | 突破/跌破 20 日高/低点 |
| VOLUME_SPIKE | BUY/SELL | 成交量达到 20 日均量 1.8 倍以上 |

## 数据来源

- 历史 K 线：[baostock](http://baostock.com/)（前复权日线）
- 实时行情：腾讯财经接口

## 免责声明

本工具仅用于技术分析学习与行情观察，**不构成任何投资建议**。A 股市场有风险，请独立判断并谨慎决策。
