# Educational A-share SCREEN — session 2026-09-02 (Asia/Shanghai) → for Thu 2026-09-03

**NOT investment advice. NOT a live order recipe.**  
Educational social/filing screen only. Empty result preferred over forcing a name.  
All four gates must pass or the name is SKIP.

Screen as-of: Wed 2026-09-02 after the A-share close. Horizon: next session Thu 2026-09-03.

---

## 0. Result

**NONE.**

No name clears Gate 1 (new issuer filing not yet traded through) **and** Gate 2 (tape not broken) **and** Gate 3 (not an overnight news crutch) **and** Gate 4 (not pure 追板 language).

Closest two SKIPs (documented in §4):

1. **600477 杭萧钢构** — real new overseas contract, already traded through 9/2 with a high-open fade.
2. **000608 阳光股份** — 6.33亿元服务器租赁合同, already traded through 9/2; issuer itself says the new line is not material to the whole company.

---

## 1. Tape facts (verified, not invented)

Sources: Xinhua Finance close review; JRJ/格隆汇 close review; Tencent quote snapshot `qt.gtimg.cn` dated `20260902`.

| Item | Claim (pre-screen) | Verified |
|---|---|---|
| SSE | ~3941 −1.0% | **3941.39, −0.97%** (prev 3979.89; open 3963.07; high 3965.81; low 3932.25) |
| ChiNext | ~−2.4% | **3312.24, −2.39%** |
| Turnover | ~1.82T, down vs prior | Xinhua Finance: **沪深京 18,206亿元**, −~2,319亿元 vs prior. JRJ/格隆汇: 三市 **18,202亿元**, −2,316亿元. Some recaps quote 沪深-only ~1.79T — same tape, different perimeter. |
| Breadth | >3900 down | JRJ/格隆汇: **超3900只下跌**. 九方: 1541 up / **3901 down**, 55 limit-up / 9 limit-down. |
| Seed / grain | fade after Mon squeeze | **Confirmed.** 神农种业 300189 **−11.39%** (7.55→6.69, low 6.67). 敦煌种业 600354 **−9.98%** limit-down. 国投丰乐 000713 **−9.94%** limit-down. 农发种业 600313 **−9.75%**. 农产品 000061 **−6.61%** (close 6.22 vs low 6.21). |
| AI / CPO / memory | weak; 中际 ~−4.3%, 长鑫 ~−3.9% | **中际旭创 300308 822.40 −4.29%** (prev 859.30; open 840.01; high 848.00; low 814.06). **长鑫科技 688825 54.32 −3.86%** (prev 56.50; open 55.55; high 55.88; low 54.00). |
| Defense / BSE anniversary | local greens | **Confirmed.** 地面兵装/航空装备领涨; 内蒙一机 600967 **13.41 +10.01%** sealed 10cm (2连板). 北证50 **+2.50%**; recaps tie it to 北交所宣布设立五周年 — theme, not an issuer filing. |
| BYD | gap-and-fade on Aug sales | Aug NEV sales **440,293 / 出口 189,466** filed **2026-09-01 19:37**. 9/2 Tencent: prev 88.71, **open 88.48**, high 89.00, low 86.60, **close 86.80 −2.15%** (fade toward the low). Exchange tape is a flat-to-slight gap-down then fade, not a large gap-up. Sales print was already in the overnight and was **traded through**. |
| Overnight | US–Iran / oil, higher US yields, Asia risk-off | **Confirmed.** US CENTCOM: new strikes on IRGC targets from 12:00 ET 9/1. WTI **90.22 +5.20%**, Brent **94.65 +4.60%**. UST 10Y **+4.8 bp to 4.80%** (2025-01 high). Fed 9月加息概率 cited **>66%** (Barr hawkish). Asia risk-off into the A-share open. |

Primary tape URLs:

- https://m.cnfin.com/yw-lb//zixun/20260902/4464030_1.html
- https://finance.jrj.com.cn/2026/09/02152558331572.shtml
- https://www.cnfin.com/zs-lb/detail/20260902/4463812_1.html
- BYD 8月产销: https://finance.jrj.com.cn/2026/09/01193758321829.shtml / https://paper.cnstock.com/html/2026-09/02/content_2263999.htm

---

## 2. Gates (ALL must pass)

1. **New public catalyst.** CNINFO / SSE / SZSE announcement dated **2026-09-02**, or after **15:00 on 9/1 and not yet traded through**. Old H1 already in price does **not** count. Buyback **announced but not executing** does **not** count as a bid. Theme chase / anniversary / limit-up board **without an issuer filing** does **not** count.
2. **Tape structure not broken.** Skip sealed limit-up chase into the close; high-open full fade; names **−6%+ hugging lows** (knife catch); names whose only story is overnight oil / Fed with **no China filing**.
3. **Not a news crutch.** Skip “tomorrow will price it” / Warsh–Fed overnight gap trades.
4. **Sentiment.** If public 股吧 / 雪球 titles are pure **追板 / 明天板**, down-rank to SKIP.

Method: Eastmoney announcement API `begin_time=2026-09-02` (1,384 items, including 9/1 after-hours that carry a 9/2 notice date) plus CNINFO `hisAnnouncement/query` keyword search (`中标` / `重大合同` / `首次回购` / `增持`) for `seDate=2026-09-02~2026-09-02`. Quotes from Tencent `qt.gtimg.cn` after the close.

---

## 3. What the filing tape actually contained

### 3.1 CNINFO keyword hits dated 2026-09-02 (issuer 中标 / 重大合同)

Only four contract-like hits. **All four were 9/1 after 15:00 and were traded on 9/2.**

| Code | Name | Filing | When posted | 9/2 tape | Gate fail |
|---|---|---|---|---|---|
| 600477 | 杭萧钢构 | DEP 采购合同 **USD 166,254,190** (~RMB 11.28亿), **15.87%** of last audited revenue; 30 months; Dangote Nigeria | 9/1 **17:18** | +1.59% (open 2.63 vs prev 2.51 = **+4.8% gap**, high 2.66, close 2.55) | Already traded through; **high-open fade** |
| 000608 | 阳光股份 | 子公司服务器租赁综合服务 **RMB 6.33亿** / 5 years; counterparty anonymized; issuer: H1 related revenue ~93万 (**0.77%**), “对整体生产经营不构成重大影响” | 9/1 **19:43** | +4.69% (7.25→7.59; open 7.46; high 7.66; low 7.30) | Already traded through; issuer materiality disclaimer |
| 301167 | 建研设计 | 联合体《中标通知书》EPC **29.91亿**; 公司份额 mainly 勘察设计费 **8,363.92万** | 9/1 **18:53** | **0.00%** (14.00→14.00) | Already a **8/25 中标候选人** fact; 通知书 is follow-through, already in price |
| 600869 | 远东股份 | 8月子公司中标/签约千万元以上合计 **17.8亿** (monthly roll-up) + 电网主题 | 9/1 **18:29** | **+9.98% 封死涨停** 19.50; bid1 ~22万手 | Already traded through; **sealed limit-up chase**; monthly order tally + 国家能源局电网会, not a single new bid |

威胜信息 688100 (8月中标合计 4,641.26万, **1.56%** of 2025 revenue) is the same 9/1 after-hours bucket — too small, already traded. SKIP.

### 3.2 9/2 after 15:00 — no new 中标 / 重大合同

Eastmoney after-15:00 9/2 book is almost entirely: monthly **回购进展** (first three trading days of September), IR notes, EGM admin, cash-management rolls, ST/监管.

Incremental after-close items that were **not** 中标/合同, and why they still fail:

| Time (9/2) | Code | Name | Fact | Why SKIP |
|---|---|---|---|---|
| 19:06 | 301335 | 天元宠物 | 深交所并购重组委 **第14次审议会议公告** + 上会稿 | Meeting **schedule / 上会稿**, not 审核通过. Deal known since 2025; 8/21 恢复审核 already in price. |
| 18:57 | 301269 | 华大九天 | 与专业机构共同设立投资基金 | Capital **out**, not a bid. Tape 94.09 **−3.61%**, hugging low 94.04. |
| 18:55 | 300044 | *ST赛为 | 预重整投资协议补充协议 | ST / 预重整. Not a clean bid fact. |
| 18:14 | 300308 | 中际旭创 | 实控人部分股票**质押** + 回购前十大股东 | **Negative / admin.** First repurchase was 9/1 18:40 and already faded 9/2. |
| 17:53 | 300406 | 九强生物 | 叶酸测定试剂盒取得北京市药监局医疗器械注册证 | Real 9/2 after-close filing, but a **single IVD kit** line-extension. Forcing it would violate “empty preferred.” 9/2 tape −1.01% (pre-filing). |
| 17:53 | 301132 | 满坤科技 | 回购专项贷款**承诺函** | Financing **commitment**, not executing. Gate 1: announced ≠ bid. |
| 17:31 | 300578 | 会畅科技 | 与专业机构共同投资 | Same as 华大九天: deploying cash. |
| 15:49 | 301115 | 联检科技 | 收购 69.62% 股权进展暨完成工商变更 | Closing an **old** deal, not a new catalyst. |

CNINFO `searchkey=增持` for 2026-09-02: **0 hits**. 华厦眼科 301267 实控人拟增持 ≥3,000万 is a **9/1** plan, not executing (9/2 −0.85%). Gate 1: announced but not executing ≠ bid.

9月1–3日窗口里大量「回购进展」是规则要求的月初披露，不是新的首次回购。真正的「首次回购」披露（昊志机电 300503、燕麦科技 688312、远望谷 002161、上海凤凰 B股）都是 **8/31 实施 / 9/1 披露**，9/2 已经交易过，且当日均为下跌或平淡（昊志 −3.15% 收在全日最低 65.89）。

### 3.3 Theme boards with no new issuer filing

- **军工 / 地面兵装:** 内蒙一机 2连板封死; 建设工业、长城军工涨停. Overnight US–Iran is **not** a China issuer filing. Gate 1 + Gate 2 (sealed limit-up) + Gate 3.
- **北证50 +2.50% / 30cm 板:** 北交所宣布设立五周年. Anniversary board. Gate 1.
- **种业 / 粮食:** Monday squeeze fade; several −6% to limit-down hugging lows. Gate 2 knife-catch. 农产品 000061 ESOP 草案 ≤1,500万、二级市场买、尚需 9/21 股东会 — 且是 **9/1 20:26** 披露，9/2 已交易并 **−6.61% 贴最低**.
- **油 / 三桶油:** overnight oil only. Several recaps note energy **高开低走**. Gate 2 + Gate 3.

---

## 4. Closest 2 SKIPs

### SKIP 1 — 600477 杭萧钢构  close **+1.59%**

- **One new fact + URL:** 与 DANGOTE PETROLEUM REFINERY AND PETROCHEMICALS FREE ZONE ENTERPRISE 签署 DEP 项目采购合同，金额 **166,254,190 美元**（约人民币 11.28亿元），占最近一期经审计营业收入 **15.87%**，期限 30 个月。  
  https://paper.cnstock.com/html/2026-09/02/content_2264085.htm  
  (Eastmoney art `AN202609011828884078`, posted **2026-09-01 17:18**)
- **Close %:** +1.59% (2.51 → 2.55). Open 2.63 / high 2.66 / low 2.47.
- **Structure:** High-open fade. Gap +4.8% at the open, failed to hold the high, gave back most of the pop into the close. Not a sealed limit-up, but Gate 2 explicitly skips high-open fades.
- **Why SKIP:** Gate 1 fails for **tomorrow** — the filing is real and material, but it was **already traded through** on 9/2. Gate 2 fails on the fade. Contract is Nigeria refinery equipment; do not recycle it as an overnight-oil proxy (Gate 3).

### SKIP 2 — 000608 阳光股份  close **+4.69%**

- **One new fact + URL:** 控股子公司阳光金汇与 A 公司签服务器租赁综合服务协议，含税总价 **6.33亿元**，期限 5 年。  
  https://static.cninfo.com.cn/finalpage/2026-09-02/1225542534.PDF  
  (posted **2026-09-01 19:43**; 公告落款 2026年9月1日)
- **Close %:** +4.69% (7.25 → 7.59). Open 7.46 / high 7.66 / low 7.30. Structure itself is not a fade or a sealed board.
- **Why SKIP:** (i) Already traded through 9/2 — Gate 1 fails for 9/3. (ii) Issuer **explicitly** says the new line is early-stage, H1 related revenue ~93万元 / 0.77% of revenue, and **“新业务对公司整体生产经营不构成重大影响.”** Counterparty anonymized; servers still to be procured; liquidity / parent-support risk language in the same PDF. (iii) Public recaps frame it as a 地产壳 + 10万元买算力壳 then 6.3亿大单 story — quality / theme risk, not a clean bid. Empty preferred over forcing it.

---

## 5. Other named SKIPs (so nothing is silently upgraded)

| Code | Name | Close | One fact | Why SKIP |
|---|---|---|---|---|
| 300308 | 中际旭创 | **−4.29%** | 9/1 18:40 首次回购 37.41万股 / 3.18亿元 https://www.nbd.com.cn/articles/2026-09-01/4569382.html | Buyback **was** executing, but already traded 9/2 and faded (open 840 vs 859, close 822, low 814). 9/2 18:14 实控人质押. CPO tape broken. |
| 688825 | 长鑫科技 | **−3.86%** | No 9/2 issuer filing in the CNINFO 中标/合同/增持 set | Memory / overnight semiconductor + yields. Gate 1 empty. Close 54.32 vs low 54.00. |
| 002594 | 比亚迪 | **−2.15%** | 8月新能源车销量 44.03万 / 出口 18.95万 https://finance.jrj.com.cn/2026/09/01193758321829.shtml | 9/1 19:37 披露，9/2 已交易；高点 89.00 后收到 86.80（近最低 86.60）. |
| 301012 | 扬电科技 | **+7.75%** | 7月已披露的算力合同：8/31 前交付 32 节点、9/1 起计费，对应含税 2.15亿元 http://static.cninfo.com.cn/finalpage/2026-09-01/1225541510.PDF | Progress on an **old** contract; 9/1 19:01 披露，9/2 已大涨交易。Chase, not a residual gap. |
| 600869 | 远东股份 | **+9.98% 封板** | 8月订单合计 17.8亿 + 电网政策会 | Sealed limit-up; monthly tally; 股吧/媒体标题是直线涨停/封单（追板语言）. Gate 2 + Gate 4. |
| 600967 | 内蒙一机 | **+10.01% 封板** | No new 9/2 issuer filing in the contract set | 2连板 + 军工主题 + 隔夜美伊. Gates 1–3. |
| 688192 | 迪哲医药 | **−0.88%** | 与 AZ 舒沃哲许可 **8/31 生效**（7/14 已签、7/30 股东会已批） https://paper.cnstock.com/html/2026-09/02/content_2264362.htm | Effectiveness is incremental, but disclosed **9/1** and traded 9/2. Economics were July news. |
| 000061 | 农产品 | **−6.61%** | ESOP 草案资金上限 1,500万、二级市场购买、待 9/21 股东会 | Tiny, not executing, already traded, **−6%+ hugging low**. Seed tape. |
| 300406 | 九强生物 | **−1.01%** (pre-filing) | 9/2 15:53 叶酸试剂盒注册证 https://www.stcn.com/article/detail/4169150.html | Only clean *untraded* 9/2 after-close product filing found. One kit ≠ a bid. Do not force. |

---

## 6. Sentiment note (Gate 4)

Did not scrape every 股吧 thread. Public recap titles on the green boards are already chase-coded: 「直线涨停，封单超44万手」(远东), 「军工逆势爆发 / 2连板」, 「北交所逆市 / 30cm」. That is enough to down-rank those names even if someone wanted to stretch Gate 1. No 追板 language is being used here to *upgrade* a name.

---

## 7. What would have been a CANDIDATE

A 9/2 **after 15:00** CNINFO/SSE/SZSE filing that is:

- a **new** 中标 / 重大合同 / 首次正在执行的回购 / 已成交的增持, not a monthly progress print and not a July/H1 item;
- **not** already printed as 中标候选人 / 框架 / 许可草案;
- on a name whose 9/2 tape is not a sealed board, not a high-open fade, and not −6% hugging the low;
- whose public titles are not 「明天板」.

**That set is empty tonight.** Re-run after 9/3 15:00; do not recycle 9/1 after-hours contracts as if they were still “new.”

---

## 8. Disclaimer (again)

This note is an educational checklist of **public filings vs public tape**. It is not a recommendation to buy, sell, or hold any security. A-share prices can gap, halt, or reverse without a new filing. If the next session prints a real after-hours catalyst that clears the gates, it can be screened then — not invented now.
