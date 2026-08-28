# 2026-08-28 A-share BUY candidate screen (educational)

**Label:** social / educational screen, **not investment advice**.  
**Do not place orders. This is not a live trading recipe.**

| Field | Value |
| --- | --- |
| Session | Friday 2026-08-28, Asia/Shanghai, afternoon session still open |
| Screen time | ~14:29 SH |
| Quote source | Tencent Finance `qt.gtimg.cn` (cross-checked Sina `hq.sinajs.cn`) |
| Filing source | CNINFO / Eastmoney announcement stream / SSE-SZSE reprints |
| Universe | Today's **new issuer announcements** only — not `a_share_monitor/watchlist.txt` |
| Output | **1 CANDIDATE** (0 would have been preferred over forcing a weaker name) |

Gates (all must pass, else SKIP):

1. **New public catalyst** dated 2026-08-27 after 15:00 SH or 2026-08-28. Old H1/annual numbers already in the tape do not count. Guidance with no amount does not count. A buyback that has not started does not count as bid. Affiliate/JV share sale is not “major shareholder dumping” unless the filing says so.
2. **Tape not broken:** skip limit-up chase, high-open fade / morning high fully given back, names down ~6%+ hugging the low, and names whose only story is already-traded news (e.g. Nvidia AH Thursday).
3. **Not a news crutch:** skip if the only bull case is “tomorrow will price it.” Kevin Warsh Jackson Hole keynote is 22:00 SH tonight — do not pick names that need a Fed/Warsh overnight gap.
4. **Sentiment:** down-rank 纯追板 / 明天板 language when public Xueqiu/Guba titles are visible. Missing social data is not a pass.

---

## Universe construction

Pulled Eastmoney `np-anotice-stock` for 2026-08-27/28 plus Sina 股海导航 / 操盘必读 reprints of CNINFO/SSE/SZSE filings. Kept only items with a **dated issuer PDF** and a **RMB (or USD-converted) amount**: first-print earnings, orders, approvals, executing buybacks, M&A with terms.

**Immediately rejected (do not shortlist):**

- Planned buybacks not yet executing: 迈赫股份 301199 (6,000–9,000万元拟回购), 盘龙药业 002864.
- Management prep with no amount: 富特科技 301607 (H-share 筹备).
- Capex / 定增 (cash out or dilution, not inbound order): 理奇智能 301599 (拟投20亿元基地), 沃尔德 688028 (定增≤14.5亿元), 运达股份 300772 (拟投30.74亿元海风; tape −11.5% knife).
- Old H1 already previewed or already in Thursday’s tape: 香农芯创 300475 (7月10日预告 35–40亿元; 正式稿 36.42亿元落在区间内), 富瀚微 300613 (7月31日预告 2.7–3.5亿元; 正式稿 3.5亿元顶格), 中芯国际 688981 / 胜宏科技 300476 / 德明利 001309 等半年报。
- Already-traded process news: 中际旭创 300308 H股 8月27日起调入港股通; 新易盛 300502 / 光模块链更接近周四 Nvidia AH 已交易叙事。
- 药明康德 603259 出售药明合联股票（一次性处置，不是买入催化）。
- 安达智能 688125 0元收购亏损子公司少数股权。
- 大普微 8月25日 34.91亿元 SSD 订单 — **before** the 8/27 15:00 cutoff.

---

## Shortlist (one row each)

Tape snapshot **2026-08-28 14:28–14:29 SH**, Tencent. `%` = last vs prev close. Structure = open / high / low / last vs that close.

### 002111 威海广泰 — **CANDIDATE**

- **ONE new fact:** After the 8/27 close the company filed *关于签订重大合同的公告*: sale of airport GSE (tow tractors, buses, GPUs, container loaders) to India’s Aghport Aviation Services Limited for **USD 17.0424m ≈ RMB 1.15bn**. Prepayment received; contract effective; three batches, cash before each shipment. Company calls it its **largest Asia airport-equipment order**.
- **Source:** Eastmoney/CNINFO reprint [威海广泰:关于签订重大合同的公告](https://pdf.dfcfw.com/pdf/H2_AN202608271828537975_1.pdf) (`AN202608271828537975`, notice date 2026-08-28; wire 17:35 SH on 8/27 via [上海证券报](https://stock.10jqka.com.cn/20260827/c679354785.shtml)). Confirmed in [每日经济新闻](https://www.nbd.com.cn/articles/2026-08-27/4561256.html).
- **Today’s tape:** **+4.04%** (9.79 / prev 9.41). Open 9.53, high 9.94, low 9.51. Holding mid-upper; not limit-up (10% cap ≈ 10.35); morning high not given back; not a 6% knife.
- **Verdict: CANDIDATE.** New dated contract with a RMB amount, already in force (prepay), tape constructive and not a chase, story is airport GSE — not Fed/Warsh/Nvidia overnight. Public Guba commentary quoted by 每经 is caution (“小心”), not 纯追板 / 明天板.
- **Why only a candidate, not a “must”:** 1.15亿元 is modest vs ~RMB 50bn mkt cap and H1 revenue 16.97亿元 (~7% of H1). India counterparty / FX risk is in the filing. H1 itself printed 8/26 and is **not** the catalyst.

### 301111 粤万年青 — **SKIP**

- **ONE new fact:** 控股子公司万宏智算与匿名 A 公司签五年期 GPU 算力云服务《服务采购协议》，**含税预估 124,416万元**. 按用量月结；毛利率约 10–20%；**尚未开始服务，预计对 2026 年经营成果无重大影响**. H1 营收仅 1.45亿元。
- **Source:** CNINFO [1225516754.PDF](https://static.cninfo.com.cn/finalpage/2026-08-28/1225516754.PDF) (公告日期 2026-08-28); Eastmoney `AN202608271828541526`.
- **Today’s tape:** **+7.03%** (24.35 / 22.75). Open 23.52, **high 26.00 (+14.3%)**, low 23.52. ChiNext 20% limit ≈ 27.30 — not limit-up, but **morning spike largely faded**.
- **Verdict: SKIP.** Gate 2 (high-open / morning-high fade) + Gate 4. Public Guba title: [明天必须涨停，我说的，不服来辩！](https://guba.eastmoney.com/news,301111,1374451197.html). 药企跨界算力 + 匿名对手方 + 预估金额 + 对 2026 无影响 = 题材交易，不是干净催化。

### 301085 亚康股份 — **SKIP**

- **ONE new fact:** 下属亚康智算与客户 A 签《通用算力技术服务协议》，**含税 9.25亿元 / 60个月**. (8/18 已有向供应商采购合计 8.68亿元的同类协议，本条是销售侧。)
- **Source:** Eastmoney [AN202608271828547309](https://pdf.dfcfw.com/pdf/H2_AN202608271828547309_1.pdf) (notice date 2026-08-27; wires ~17:52 SH). [金融界 17:52](https://stock.jrj.com.cn/2026/08/27175258252748.shtml).
- **Today’s tape:** **+2.87%** (61.02 / 59.32). Open **62.36**, high 63.30, **low = last 60.99–61.02**. High-open fade, sitting on the session low.
- **Verdict: SKIP.** Catalyst is new and sized, but Gate 2 fails (high-open fade / morning high given back to the low). Do not buy a fade and call it “structure clean.”

### 300136 信维通信 — **SKIP**

- **ONE new fact:** 全资子公司益阳信维拟现金 **11亿元** 收购益阳电子科技 **55%** 股权（关联交易），完成后持股 70% 并表。尚需 9/15 股东会。
- **Source:** CNINFO [1225522626.PDF](https://static.cninfo.com.cn/finalpage/2026-08-28/1225522626.PDF); Eastmoney `AN202608271828555920`. 财联社 8/27 20:24.
- **Today’s tape:** **−2.38%** (60.59 / 62.07). Open 61.67, high 63.20, low 60.33 — near the low, not a 6% knife.
- **Verdict: SKIP.** M&A-with-terms passes Gate 1, but tape is not clean (failed bounce, hugging the low). Related-party cash-out also needs the EGM; not an executing bid.

### 603296 华勤技术 — **SKIP**

- **ONE new fact:** 8/27 半年度业绩说明会：超节点 Q3 批量出货，**下半年收入将超过 100亿元**；全年收入指引超 2000亿元 / 扣非 +20% 左右。
- **Source:** Eastmoney [AN202608271828546986](https://pdf.dfcfw.com/pdf/H2_AN202608271828546986_1.pdf); [每经](https://www.nbd.com.cn/articles/2026-08-27/4561150.html).
- **Today’s tape:** **+0.10%** (78.57 / 78.49). Open 79.70, high 81.27, low 78.50 — faded to the low.
- **Verdict: SKIP.** Amounts exist, but this is **guidance / briefing**, not a signed order, approval, or executing buyback. H1 already printed 8/25–26. AI/CSP beta is the tape that does **not** need to sit through Warsh 22:00 SH. Gate 2 + Gate 3.

### 601995 中金公司 (及 601198 东兴 / 601059 信达) — **SKIP**

- **ONE new fact:** 换股吸收合并获上交所并购重组委 2026 年第 17 次审议通过；仍待证监会注册。
- **Source:** 公司公告临 2026-050，见 [上海证券报 8/28](https://paper.cnstock.com/html/2026-08/28/content_2261725.htm).
- **Today’s tape:** 中金 **−0.26%** (34.77; open=high 35.01). 东兴 −0.35%，信达 −0.47%。
- **Verdict: SKIP.** 上会日程上周已披露；过会是流程节点，不是新的经济事实。周四叙事已在交易，今日完全没定价。Gate 2 “already-traded news.”

### 300475 香农芯创 / 300613 富瀚微 — **SKIP** (shown only as first-print false friends)

- 香农：正式半年报 营收 602.04亿元 / 净利 36.42亿元 (+2207%)。**7月10日已预告 35–40亿元** — old numbers in the tape. Tape +4.64% but storage/AI is Thursday Nvidia leftover + tonight Warsh beta. Gate 1 + Gate 3.
- 富瀚微：正式半年报净利 3.5亿元 (+1419%)。**7月31日已预告 2.7–3.5亿元**。Tape +5.67% 结构尚可，但不是新信息。Gate 1.

### 001289 龙源电力 — **SKIP**

- 拟 **1.4864亿元** 关联收购河南昆吾 100MW 风电项目股权，协议尚未签（不晚于 9/30）。
- Tape **−2.30%** near the low. Immaterial vs Longyuan scale; not executing.

---

## Final list — CANDIDATES only

| Code | Name | New fact (one line) | Tape 14:29 SH | Why it cleared |
| --- | --- | --- | --- | --- |
| **002111** | **威海广泰** | 8/27 15:00 后公告对印度 Aghport **1.15亿元** 空港装备合同，已收预付款并生效 | **+4.04%**, open 9.53 / high 9.94 / low 9.51 / last 9.79 | Dated RMB order, prepaid, structure intact, not a Fed/Nvidia crutch, social not 追板 |

**Count: 1.** Empty was the default; this name cleared all four gates without stretching.

If this row is later discarded (order too small vs market cap, or India risk), the result becomes **NONE**. Closest two SKIPs would then be:

1. **301111 粤万年青** — 12.44亿元合同过 Gate 1，但冲高 +14% 回落到 +7%，且股吧标题已是「明天必须涨停」。
2. **301085 亚康股份** — 9.25亿元合同过 Gate 1，但高开后回落到当日最低。

---

## What this screen did *not* do

- No broker, no order ticket, no position size, no stop, no “buy the close.”
- Did not use the five-name `a_share_monitor` watchlist (600519 / 000001 / 000858 / 300750 / 601318).
- Did not treat “tomorrow Warsh / Nvidia gap” as a long thesis.
- Social coverage is incomplete (Xueqiu API blocked; Guba list pages are JS). Where a public title existed it was used; absence was not treated as a pass.

**Disclaimer:** Educational observation of public filings and tape. Not a recommendation to buy, sell, or hold any security.
