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

## 自选股配置

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
