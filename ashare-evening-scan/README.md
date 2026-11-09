# ashare-evening-scan

A 股教育模拟「晚筛细扫」。**扫描 ≠ 买卖灯 ≠ 下单 ≠ 改灯**。不下真单、不连券商。

## 口径

- `price_asof` 用收盘日（本窗 `2026-11-09`），勿混用盘前/前一交易日。
- 线1 价值分板：主板破净门；创业/科创相对低估放宽；各板 ≤5。
- 线2 技术独立 ≤5：站上均线、非近板、高开≤1%；禁电力；不复述价值票。
- 线2b 全A超跌 5–10：A 硬 ≥1（满 2 优先），默认并乙。科创观察·不对齐。

## 运行

```bash
python3 ashare-evening-scan/run_evening.py --stage collect
python3 ashare-evening-scan/run_evening.py --stage report
python3 ashare-evening-scan/tests/test_screens.py
```

产出写入 `artifacts/evening-YYYY-MM-DD/`。核价东财 / 新浪 / 腾讯。
