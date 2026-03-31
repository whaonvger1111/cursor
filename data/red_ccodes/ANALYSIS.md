# 数量宏观相关：基于 IDEAS「RED Computer Codes」的整理与简析

## 1. 范围说明（重要）

- **已覆盖**：[`Review of Economic Dynamics` — Computer Codes](https://ideas.repec.org/s/red/ccodes.html) 全系列在 IDEAS 上的条目（本仓库抓取 **690** 条去重记录）。
- **「宏观相关」子集**：**570** 条。规则：JEL 含 **E**（宏观）或 **F2/F3/F4**（开放宏观）或 **Q5**（环境，常与宏观模型耦合）→ 标为宏观；**无 JEL** 时默认归入宏观（该系列以动态宏观/计量应用为主，但会有误判风险）。
- **无法做到**：RePEc 上「全部数量宏观文献」及「全部代码」。多数论文代码在 **GitHub、Zenodo、期刊补充材料**，未必进入 IDEAS 的 Computer Codes 系列。完整书目应使用 [RePEc 元数据](https://ideas.repec.org/getdata.html) 按 JEL **E** 全库拉取，而非仅 RED。

## 2. 分类维度

### 2.1 按 JEL 首字母（宏观子集中「第一条 JEL」）

| 首字母 | 条数 | 含义（粗略） |
|--------|------|----------------|
| E | 333 | 宏观、货币、周期、增长等 |
| D | 68 | 微观基础、家庭异质性、博弈等（常与宏观结构模型结合） |
| （无） | 55 | 元数据未标 JEL |
| C | 42 | 计量与计算方法 |
| F | 29 | 国际、开放经济 |
| 其他 | 少量 | 见 `index_macro.jsonl` |

### 2.2 按编程环境（宏观子集，粗归类）

| 类别 | 条数（约） |
|------|------------|
| 仅 Matlab 或含 Matlab | 多数（与 SUMMARY 中 `Matlab*` 行一致） |
| Matlab + Dynare | 约 80+（DSGE/NK 常见） |
| Fortran | 若干（传统计算/结构估计） |
| Fortran + Matlab + Stata | 若干（混合复制包） |
| Python / Julia / R | 少量 |

详见 `SUMMARY.md` 中的原始字符串列表（IDEAS 对语言字段的写法不统一，如 `Matlab` vs `Matlab; Dynare`）。

### 2.3 按主题（建议用标题关键词自行再分）

`index_macro.jsonl` 每条含 `title`（复制包标题）与 `paper_title_guess`（链到 RED 论文时的标题）。可在本地用关键词检索，例如：

- `monetary` / `fiscal` / `NK` / `New Keynesian`
- `HANK` / `heterogeneous` / `incomplete markets`
- `climate` / `carbon`
- `DSGE` / `business cycle` / `unemployment`

## 3. 本地索引字段

每行 JSON 含：`id`, `handle`, `ideas_code_url`, `title`, `programming_language`, `jel_codes`, `jel_labels`, `paper_url`, `paper_title_guess`, `file_urls`, `abstract`, `macro_related`, `macro_reason`。

## 4. 下载复制包

已提供脚本：`tools/repec_red_ccodes/download_red_ccodes.py`（默认限流）。  
示例：仅下载 `23-118` 的复制文件到 `data/red_ccodes/downloads/`（默认不提交到 git，见该目录下 `.gitignore`）。

```bash
python3 tools/repec_red_ccodes/download_red_ccodes.py \
  --index data/red_ccodes/index_macro.jsonl --id 23-118
```

**不建议**一次性对 500+ 条跑满量下载（体积与带宽、以及对 S3/IDEAS 的负载）；请分批或只拉取需要的 `id`。

## 5. 简易结论

- RED 的复制包**高度集中**在 **Matlab（及 Dynare）** 与 **Fortran/Stata** 组合，符合**动态宏观结构模型 + 实证**的主流工具链。
- 以 JEL 粗看，**E 类占主导**，其余多为**与宏观结构联动的微观/计量**（D、C）或**开放宏观**（F）。
- 若需「全库数量宏观」，应在 RePEc 元数据中按 **JEL E*** 筛选，再**单独**匹配作者提供的代码链接；本仓库仅解决 **IDEAS 上 RED 代码系列** 的一键索引与示例下载。
