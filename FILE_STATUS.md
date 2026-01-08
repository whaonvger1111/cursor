# 文件转换状态

## 统计概览

- **MATLAB文件总数**: 88个
- **Python文件总数**: 38个
- **已转换核心文件**: 约30-35个
- **剩余未转换**: 约50-55个

## 已转换的核心文件 ✅

### 核心函数
- ✅ fun.py (fun.m)
- ✅ fun_prices.py (fun_prices.m)
- ✅ fun_estimation.py (fun_estimation.m)
- ✅ fun_x_entrants.py (fun_x_entrants.m)
- ✅ fun_k_entrants_pareto.py (fun_k_entrants_pareto.m)
- ✅ fun_k_entrants_uniform.py (fun_k_entrants_uniform.m)

### 转移动态
- ✅ fun_transition.py (fun_transition.m)
- ✅ fun_vfi1_transition.py (fun_vfi1_transition.m)
- ✅ fun_distrib1_tran.py (fun_distrib1_tran.m)
- ✅ fun_aggregates_tran.py (fun_aggregates_tran.m)
- ✅ fun_phi_tran.py (fun_phi_tran.m)
- ✅ fun_entry_exit.py (fun_entry_exit.m)
- ✅ fun_pol_update.py (fun_pol_update.m)
- ✅ interp_entry_exit.py (interp_entry_exit.m)
- ✅ compute_cap_adj.py (compute_cap_adj.m)

### 稳态（框架）
- ✅ fun_steady_state.py (fun_steady_state.m) - 框架完成
- ✅ fun_obj.py (fun_obj.m) - 框架完成

### 设置函数
- ✅ set_parameters.py (set_parameters.m)
- ✅ set_targets_ss.py (set_targets_ss.m)
- ✅ set_shocks.py (set_shocks.m)
- ✅ set_grant.py (set_grant.m)
- ✅ read_data_targets.py (read_data_targets.m)

### 辅助函数（sub目录）
- ✅ sub/sub_V1_onestep.py (sub_V1_onestep.m)
- ✅ sub/sub_investment_onestep.py (sub_investment_onestep.m)
- ✅ sub/sub_Bhat_onestep.py (sub_Bhat_onestep.m)
- ✅ sub/sub_kp_onestep.py (sub_kp_onestep.m)
- ✅ sub/sub_mu_onestep.py (sub_mu_onestep.m)
- ✅ sub/sub_aggregates_onestep.py (sub_aggregates_onestep.m)

### 工具函数（tools目录）
- ✅ tools/struct2vec.py (tools/struct2vec.m)
- ✅ tools/vec2struct.py (tools/vec2struct.m)
- ✅ tools/bounds2vec.py (tools/bounds2vec.m)
- ✅ tools/markovapprox.py (tools/markovapprox.m)
- ✅ tools/paretojo.py (tools/paretojo.m)
- ✅ tools/bddparetocdf.py (tools/bddparetocdf.m)
- ✅ tools/find_loc_vec.py (tools/find_loc_vec.m)

### 主程序
- ✅ main.py (main.m) - 框架完成

## 待转换的高优先级文件 🔴

### 核心稳态计算（必需）
1. **fun_vfi1.m** → fun_vfi1.py
   - 稳态价值函数迭代
   - 这是稳态计算的核心
   - 复杂度：高

2. **fun_distrib1.m** → fun_distrib1.py
   - 稳态分布计算
   - 前向迭代
   - 复杂度：中

3. **fun_aggregates.m** → fun_aggregates.py
   - 稳态加总计算
   - 计算总产出、资本、劳动等
   - 复杂度：中

4. **fun_targets.m** → fun_targets.py
   - 模型矩计算
   - 用于校准
   - 复杂度：高（可能需要fun_simulate）

5. **gen_phi_dist.m** → gen_phi_dist.py
   - 生成进入者分布
   - 复杂度：低

6. **sub_vfi_onestep.m** → sub/sub_vfi_onestep.py
   - 约束企业VFI单步
   - 原代码使用MEX文件
   - 复杂度：高

## 待转换的中优先级文件 🟡

### 转移动态相关
- fun_targets_tran.m → fun_targets_tran.py
- fun_calib_transition.m → fun_calib_transition.py
- fun_decomposition.m → fun_decomposition.m
- fun_welfare.m → fun_welfare.py
- fun_zombie.m → fun_zombie.py
- append_tran_txt.m → append_tran_txt.py
- txt_export_tran.m → txt_export_tran.py

### 模拟和分析
- fun_simulate.m → fun_simulate.py
- fun_simulate_agesize.m → fun_simulate_agesize.py
- compute_forced_exit.m → compute_forced_exit.py
- emp_loss_perc.m → emp_loss_perc.py

### 其他函数
- fun_x_entrants_pareto.m → fun_x_entrants_pareto.py

## 待转换的低优先级文件 🟢

### 绘图函数（约15个）
- plot_*.m → plot_*.py
- make_plots_*.m → make_plots_*.py
- 主要用于可视化，不影响核心计算

### 表格生成（约5个）
- make_table_*.m → make_table_*.py
- mystruct2table*.m → mystruct2table*.py
- 主要用于输出格式化

### 其他工具函数
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

## 转换优先级总结

### 🔴 必需（运行完整流程）
**6个文件**
1. fun_vfi1.py
2. fun_distrib1.py
3. fun_aggregates.py
4. fun_targets.py
5. gen_phi_dist.py
6. sub/sub_vfi_onestep.py

### 🟡 重要（功能完善）
**约15个文件**
- 转移动态相关函数
- 模拟和分析函数

### 🟢 可选（可视化和输出）
**约30-35个文件**
- 绘图函数
- 表格生成函数
- 其他工具函数

## 完成度估算

- **核心计算功能**: 约70%完成
- **转移动态**: 约95%完成
- **稳态计算**: 约60%完成（需要fun_vfi1等）
- **整体项目**: 约45-50%完成

## 建议

要运行完整的模型，至少需要转换上述6个高优先级文件。这些文件构成了稳态计算的核心，是转移动态计算的必要前提。

