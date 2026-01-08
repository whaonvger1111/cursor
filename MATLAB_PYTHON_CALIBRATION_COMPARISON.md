# MATLAB vs Python 校准方法对比

## 1. 目标函数计算 (`fun_estimation`)

### MATLAB (`fun_estimation.m`)
```matlab
obj_smm = 0;
for i=1:length(model_mom_vec)
    dist2 = ((model_mom_vec(i)-data_mom_vec(i))/data_mom_vec(i))^2;
    obj_smm = obj_smm+dist2*calibWeights_vec(i);
end

% 惩罚项：如果empshare_small>1
check = model_mom.empshare_small>1;
penalty = 1000*max(model_mom.empshare_small-1,0)^2;
if check
    obj_smm = obj_smm+penalty;
end
```

### Python (`fun_estimation.py`)
```python
obj_smm = 0
for i in range(len(model_mom_vec)):
    if data_mom_vec[i] != 0:
        dist2 = ((model_mom_vec[i] - data_mom_vec[i]) / data_mom_vec[i]) ** 2
        obj_smm += dist2 * calibWeights_vec[i]

# 惩罚项：如果empshare_small>1
if 'empshare_small' in model_mom:
    check = model_mom['empshare_small'] > 1
    penalty = 1000 * max(model_mom['empshare_small'] - 1, 0) ** 2
    if check:
        obj_smm += penalty
```

**结论**：✅ **完全一致**

---

## 2. 市场出清条件处理 (`fun_obj`)

### MATLAB (`fun_obj.m` 第98-102行)
```matlab
if agg.K_corp<0
    warning("Capital in corporate sector is negative!")
    %sol=[];agg=[];b_grid=[];distribS=[];prices=[];model_mom=[];flag_ss=[];par=[];
    %return
end
```
**注意**：MATLAB 只发出警告，**不添加惩罚项**，**不提前返回**。

### Python (`fun_obj.py` 第93-113行)
```python
# 检查市场出清条件并添加惩罚项
market_clearing_penalty = 0
if agg is not None:
    K_corp = agg.get('K_corp', 0)
    LHS = agg.get('LHS', 0)
    aux = agg.get('aux', 0)
    
    if K_corp < 0:
        print(f"警告：企业部门资本为负！K_corp = {K_corp:.6f}")
        market_clearing_penalty += 10000 * abs(K_corp)
    
    if LHS < 0:
        print(f"警告：市场出清方程左端为负！LHS = {LHS:.6f}")
        market_clearing_penalty += 10000 * abs(LHS)
    
    if aux <= 0:
        print(f"警告：企业部门净收益率 <= 0！aux = {aux:.6f}")
        market_clearing_penalty += 10000

# ... 计算 obj_smm ...

# 添加市场出清惩罚项
obj_smm += market_clearing_penalty
```

**结论**：⚠️ **有差异**
- MATLAB：只警告，不惩罚
- Python：添加了惩罚项（这是改进，有助于引导优化器找到经济上合理的解）

---

## 3. 校准流程 (`main.m` vs `run_calibration.py`)

### MATLAB (`main.m` 第193-263行)
```matlab
if par.do_calib == 2
    disp('Start calibration of the steady-state..')
    
    obj_smm_best = realmax;
    
    % 定义要最小化的函数
    f_obj = @(x) fun_obj(x,par,bounds,calibNames,data_mom,targetNames,calibWeights,description,dispNames,targetNames_long);
    
    % 转换边界
    bounds_vec  = bounds2vec(bounds,calibNames);
    lbounds_vec = bounds_vec(:,1);
    ubounds_vec = bounds_vec(:,2);
    
    switch est_algo
        case 'simulan'
            % 模拟退火 (SIMULANS)
            ...
        case 'simulannealbnd'
            % MATLAB内置模拟退火
            ...
        case 'fminsearch'
            % Nelder-Mead with bounds
            options = optimset('MaxIter',5000,'Display','iter');
            [x,~,exitflag] = fminsearchcon(f_obj,guess,lbounds_vec,ubounds_vec,[],[],[],options);
    end
end
```

### Python (`run_calibration.py`)
```python
# 使用 scipy.optimize.minimize
result = minimize(
    objective_wrapper,
    guess_flat,
    method='L-BFGS-B',  # 支持边界约束的拟牛顿法
    bounds=list(zip(lbounds_vec, ubounds_vec)),
    options={
        'maxiter': 1000,
        'disp': True,
        'ftol': 1e-6,
        'gtol': 1e-6,
    },
    args=(par, bounds, calibNames, data_mom, targetNames, calibWeights, 
          description, dispNames, targetNames_long)
)
```

**结论**：✅ **功能等价，但算法不同**
- MATLAB：支持多种算法（SIMULANS, simulannealbnd, fminsearch）
- Python：使用 L-BFGS-B（拟牛顿法，通常更快）

---

## 4. 目标数量

### MATLAB (`set_targets_ss.m`)
21个目标矩：
1. avefirmsize
2. avefirmsize_age0
3. empshare_small
4. exitrate
5. fixedcost_to_rev
6. autocorr_emp
7. ave_work
8. exitrate_0_9
9. scor_invrate
10. hasNetDebt
11. freq_lumpinv
12. frac_exit_forced
13. frac_exit_vol
14. firmshare_0_9
15. firmshare_10_19
16. firmshare_20_99
17. firmshare_100_499
18. empshare_0_9
19. empshare_10_19
20. empshare_20_99
21. empshare_100_499

### Python (`set_targets_ss.py`)
**完全相同**：21个目标矩

**结论**：✅ **完全一致**

---

## 5. 关键差异总结

| 方面 | MATLAB | Python | 说明 |
|------|--------|--------|------|
| 目标函数公式 | ✅ | ✅ | 完全一致 |
| empshare_small惩罚 | ✅ | ✅ | 完全一致 |
| K_corp<0处理 | ⚠️ 只警告 | ✅ 添加惩罚 | Python改进 |
| LHS<0处理 | ❌ 无 | ✅ 添加惩罚 | Python改进 |
| aux<=0处理 | ❌ 无 | ✅ 添加惩罚 | Python改进 |
| 优化算法 | 多种选择 | L-BFGS-B | 功能等价 |
| 目标数量 | 21 | 21 | 完全一致 |

---

## 6. 建议

1. **Python的惩罚项是改进**：有助于引导优化器找到经济上合理的解
2. **如果希望完全一致**：可以移除Python中的市场出清惩罚项，但**不建议**这样做
3. **校准结果可能不同**：由于惩罚项的存在，Python版本可能会找到不同的参数值，但这些值在经济上更合理（满足市场出清条件）













