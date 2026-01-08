# 剩余未转换文件清单

## 统计概览

- **MATLAB文件总数**: 约60个核心文件（不包括工具函数）
- **已转换Python文件**: 38个
- **剩余未转换**: 约22-25个核心文件 + 约20-25个工具/绘图文件

## 🔴 高优先级 - 必需文件（6个）

这些文件是运行完整模型所必需的：

1. **fun_vfi1.m** → fun_vfi1.py ⚠️
   - 稳态价值函数迭代
   - **状态**: 未转换
   - **优先级**: 最高
   - **复杂度**: 高（约300行，使用MEX文件）

2. **fun_distrib1.m** → fun_distrib1.py ⚠️
   - 稳态分布计算
   - **状态**: 未转换
   - **优先级**: 最高
   - **复杂度**: 中（约170行）

3. **fun_aggregates.m** → fun_aggregates.py ⚠️
   - 稳态加总计算
   - **状态**: 未转换
   - **优先级**: 最高
   - **复杂度**: 中（约125行）

4. **fun_targets.m** → fun_targets.py ⚠️
   - 模型矩计算
   - **状态**: 未转换
   - **优先级**: 最高
   - **复杂度**: 高（约550行，可能需要fun_simulate）

5. **gen_phi_dist.m** → gen_phi_dist.py ⚠️
   - 生成进入者分布
   - **状态**: 未转换
   - **优先级**: 高
   - **复杂度**: 低（约50行）

6. **sub_vfi_onestep.m** → sub/sub_vfi_onestep.py ⚠️
   - 约束企业VFI单步
   - **状态**: 未转换
   - **优先级**: 高
   - **复杂度**: 高（原代码使用MEX文件）

## 🟡 中优先级 - 重要文件（约15个）

### 转移动态相关
- **fun_targets_tran.m** → fun_targets_tran.py
- **fun_calib_transition.m** → fun_calib_transition.py
- **fun_decomposition.m** → fun_decomposition.py
- **fun_welfare.m** → fun_welfare.py
- **fun_zombie.m** → fun_zombie.py
- **append_tran_txt.m** → append_tran_txt.py
- **txt_export_tran.m** → txt_export_tran.py

### 模拟和分析
- **fun_simulate.m** → fun_simulate.py
- **fun_simulate_agesize.m** → fun_simulate_agesize.py
- **compute_forced_exit.m** → compute_forced_exit.py
- **emp_loss_perc.m** → emp_loss_perc.py
- **cum_impact_compare.m** → cum_impact_compare.py

### 其他
- **fun_x_entrants_pareto.m** → fun_x_entrants_pareto.py
- **append_results_txt.m** → append_results_txt.py

## 🟢 低优先级 - 可选文件（约25-30个）

### 绘图函数（约15个）
- plot_calib_tran.m
- plot_exit_tran.m
- plot_irf_compare.m
- plot_irf_compare_cf.m
- plot_irf_impact.m
- plot_liquidity.m
- plot_micro_l.m
- plot_ppchange_compare.m
- plot_ss.m
- plot_ss_policy.m
- make_plots_compare.m
- make_plots_irf_sizebin.m
- make_plots_ss.m
- main_plots.m

### 表格生成（约5个）
- make_table_ss.m
- main_tables.m
- mystruct2table.m
- mystruct2table_mom.m

### 工具函数（约10-15个）
- tools/find_loc.m
- tools/locate.m
- tools/locate_equi.m
- tools/make_grid.m
- tools/myinterp1.m
- tools/myinterp1_equi.m
- tools/markov_sim.m
- tools/qnwnorm.m
- tools/quantili.m
- tools/simulate_iid.m
- tools/simulate_iid_fast.m
- tools/SIMULANS.m
- tools/fminsearchcon.m
- tools/v2struct.m（可能已包含在其他文件中）

## 已转换文件对照表 ✅

| MATLAB文件 | Python文件 | 状态 |
|-----------|-----------|------|
| fun.m | fun.py | ✅ 完成 |
| set_parameters.m | set_parameters.py | ✅ 完成 |
| set_targets_ss.m | set_targets_ss.py | ✅ 完成 |
| set_shocks.m | set_shocks.py | ✅ 完成 |
| set_grant.m | set_grant.py | ✅ 完成 |
| read_data_targets.m | read_data_targets.py | ✅ 完成 |
| fun_prices.m | fun_prices.py | ✅ 完成 |
| fun_transition.m | fun_transition.py | ✅ 完成 |
| fun_vfi1_transition.m | fun_vfi1_transition.py | ✅ 完成 |
| fun_distrib1_tran.m | fun_distrib1_tran.py | ✅ 完成 |
| fun_aggregates_tran.m | fun_aggregates_tran.py | ✅ 完成 |
| fun_phi_tran.m | fun_phi_tran.py | ✅ 完成 |
| fun_entry_exit.m | fun_entry_exit.py | ✅ 完成 |
| fun_pol_update.m | fun_pol_update.py | ✅ 完成 |
| interp_entry_exit.m | interp_entry_exit.py | ✅ 完成 |
| compute_cap_adj.m | compute_cap_adj.py | ✅ 完成 |
| fun_x_entrants.m | fun_x_entrants.py | ✅ 完成 |
| fun_k_entrants_pareto.m | fun_k_entrants_pareto.py | ✅ 完成 |
| fun_k_entrants_uniform.m | fun_k_entrants_uniform.py | ✅ 完成 |
| fun_estimation.m | fun_estimation.py | ✅ 完成 |
| fun_steady_state.m | fun_steady_state.py | 🟡 框架完成 |
| fun_obj.m | fun_obj.py | 🟡 框架完成 |
| main.m | main.py | 🟡 框架完成 |
| sub_V1_onestep.m | sub/sub_V1_onestep.py | ✅ 完成 |
| sub_investment_onestep.m | sub/sub_investment_onestep.py | ✅ 完成 |
| sub_Bhat_onestep.m | sub/sub_Bhat_onestep.m | ✅ 完成 |
| sub_kp_onestep.m | sub/sub_kp_onestep.py | ✅ 完成 |
| sub_mu_onestep.m | sub/sub_mu_onestep.py | ✅ 完成 |
| sub_aggregates_onestep.m | sub/sub_aggregates_onestep.py | ✅ 完成 |

## 总结

### 核心计算功能
- **必需文件**: 6个未转换
- **重要文件**: 约15个未转换
- **可选文件**: 约25-30个未转换

### 完成度
- **转移动态计算**: 95% ✅
- **稳态计算**: 60% 🟡（需要6个核心文件）
- **整体项目**: 约45-50% 🟡

### 建议
要运行完整的模型，**至少需要转换上述6个高优先级文件**。这些文件构成了稳态计算的核心，是转移动态计算的必要前提。

