# MATLAB vs Python 校准流程对比

## 1. 优化算法差异

### MATLAB (`main.m` 第210-263行)

MATLAB支持**三种优化算法**，通过`est_algo`变量选择：

#### 选项1: `'simulan'` - 自定义模拟退火
```matlab
case 'simulan'
    disp('Simulated annealing')
    maxim = 0;       % 1 if maximize, 0 otherwise
    rt    = 0.85;    % temperature decreasing ratio
    eps   = 1e-4;    % error tolerance for termination
    ns    = 20;      % number of cycles
    nt    = 100;     % number of iterations before temperature reduction
    neps  = 4;       % number of final functions values used to decide upon termination
    maxevl= 100000;  % maximum number of function evaluations
    iprint= 1;       % control inside printing
    t     = 0.5;     % initial temperature
    option=[maxim rt eps ns nt neps maxevl iprint t]';
    c     = 2*ones(length(guess),1);
    vm    = 0.1*ones(length(guess),1);
    
    [x,fopt,nacc,nfcnev,nobds,ier,t,vm]= SIMULANS(f_obj,guess,option,lbounds_vec,ubounds_vec,c,vm);
```

#### 选项2: `'simulannealbnd'` - MATLAB内置模拟退火
```matlab
case 'simulannealbnd'
    disp('Simulated annealing: simulannealbnd')
    init_temp = 5;
    options = optimoptions(@simulannealbnd,'Display','iter','InitialTemperature',init_temp);
    [x,~,exitflag] = simulannealbnd(f_obj,guess,lbounds_vec,ubounds_vec,options);
```

#### 选项3: `'fminsearch'` - Nelder-Mead（带边界约束）
```matlab
case 'fminsearch'
    disp('Nelder-Mead with bounds')
    options = optimset('MaxIter',5000,'Display','iter');
    [x,~,exitflag] = fminsearchcon(f_obj,guess,lbounds_vec,ubounds_vec,[],[],[],options);
```

**默认算法**：`est_algo = 'fminsearch'`（第72行）

### Python (`run_calibration.py` 和 `quick_test_calibration.py`)

Python只使用**一种优化算法**：

#### L-BFGS-B（拟牛顿法，支持边界约束）
```python
from scipy.optimize import minimize

options = {
    'maxiter': 50,  # 最大迭代次数
    'disp': True,
    'ftol': 1e-4,   # 函数值收敛容差
    'gtol': 1e-4    # 梯度收敛容差
}

result = minimize(
    objective_wrapper,
    guess_flat,
    method='L-BFGS-B',
    bounds=list(zip(lbounds_vec, ubounds_vec)),
    options=options,
    args=(par, bounds, calibNames, data_mom, targetNames, calibWeights, 
          description, dispNames, targetNames_long)
)
```

**差异**：
- ❌ Python **不支持**模拟退火算法
- ❌ Python **不支持**Nelder-Mead算法
- ✅ Python使用L-BFGS-B（通常比Nelder-Mead更快，但需要梯度信息）

---

## 2. 目标函数调用方式

### MATLAB
```matlab
% 定义匿名函数
f_obj = @(x) fun_obj(x,par,bounds,calibNames,data_mom,targetNames,calibWeights,description,dispNames,targetNames_long);

% 直接调用优化器
[x,~,exitflag] = fminsearchcon(f_obj,guess,lbounds_vec,ubounds_vec,[],[],[],options);
```

### Python
```python
# 定义包装函数
def objective_wrapper(x, par_local, bounds_local, calibNames_local, data_mom_local, 
                     targetNames_local, calibWeights_local, description_local, 
                     dispNames_local, targetNames_long_local):
    obj_smm, ... = fun_obj(x, par_local.copy(), bounds_local, calibNames_local, ...)
    return obj_smm

# 调用优化器
result = minimize(
    objective_wrapper,
    guess_flat,
    method='L-BFGS-B',
    bounds=list(zip(lbounds_vec, ubounds_vec)),
    options=options,
    args=(par, bounds, calibNames, data_mom, targetNames, calibWeights, 
          description, dispNames, targetNames_long)
)
```

**差异**：
- MATLAB：使用匿名函数，参数通过闭包传递
- Python：使用包装函数，参数通过`args`显式传递（这是multiprocessing的要求）

---

## 3. 结果保存方式

### MATLAB (`main.m` 第265-270行)
```matlab
% Save estimated parameters in file estim_params.txt
FID = fopen(fullfile(par.InpDir,'estim_params.txt'),'w');
for i = 1:length(x)
    fprintf(FID,'%s  %.10f \n',calibNames{i},x(i));
end
fclose(FID);
```

### Python (`run_calibration.py` 第190-196行)
```python
# 保存校准后的参数到文件
output_file = os.path.join(par['InpDir'], file_params)
with open(output_file, 'w') as f:
    for i, name in enumerate(calibNames):
        f.write(f'{name}  {result.x[i]:.10f}\n')
```

**结论**：✅ **完全一致**

---

## 4. 中间结果记录

### MATLAB (`fun_obj.m` 第128-132行)
```matlab
if obj_smm<obj_smm_best
    obj_smm_best = obj_smm;
    % append results to txt file
    append_results_txt(obj_smm,par,calibNames,data_mom,model_mom,calibWeights,targetNames,par.InpDir);
end
```

### Python (`fun_obj.py` 第148-150行)
```python
if obj_smm < obj_smm_best:
    obj_smm_best = obj_smm
    # 将结果追加到txt文件
    append_results_txt(obj_smm, par, calibNames, data_mom, model_mom, calibWeights, targetNames, par.get('InpDir', 'inputs'))
```

**结论**：✅ **完全一致**

---

## 5. 市场出清条件处理

### MATLAB (`fun_obj.m` 第98-102行)
```matlab
if agg.K_corp<0
    warning("Capital in corporate sector is negative!")
    %sol=[];agg=[];b_grid=[];distribS=[];prices=[];model_mom=[];flag_ss=[];par=[];
    %return
end
```
- ⚠️ 只警告，**不添加惩罚项**
- ⚠️ **不提前返回**（return语句被注释）

### Python (`fun_obj.py` 第93-139行)
```python
# 检查市场出清条件并添加惩罚项
market_clearing_penalty = 0
if agg is not None:
    K_corp = agg.get('K_corp', 0)
    LHS = agg.get('LHS', 0)
    aux = agg.get('aux', 0)
    
    if K_corp < 0:
        market_clearing_penalty += 10000 * abs(K_corp)
    if LHS < 0:
        market_clearing_penalty += 10000 * abs(LHS)
    if aux <= 0:
        market_clearing_penalty += 10000

# 添加市场出清惩罚项
obj_smm += market_clearing_penalty
```
- ✅ **添加惩罚项**，引导优化器找到满足市场出清条件的解

**差异**：⚠️ **有差异**（Python版本是改进）

---

## 6. 目标函数计算

### MATLAB (`fun_estimation.m`)
```matlab
obj_smm = 0;
for i=1:length(model_mom_vec)
    dist2 = ((model_mom_vec(i)-data_mom_vec(i))/data_mom_vec(i))^2;
    obj_smm = obj_smm+dist2*calibWeights_vec(i);
end

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

if 'empshare_small' in model_mom:
    check = model_mom['empshare_small'] > 1
    penalty = 1000 * max(model_mom['empshare_small'] - 1, 0) ** 2
    if check:
        obj_smm += penalty
```

**结论**：✅ **完全一致**（Python添加了`data_mom_vec[i] != 0`检查，这是防御性编程）

---

## 7. 参数边界检查

### MATLAB (`fun_obj.m` 第65-77行)
```matlab
%check if parameters are within lower bounds
if any(guess<lbounds_vec)
    warning('Lower bounds on parameters violated!')
    obj_smm = 10000;
    sol=[];agg=[];b_grid=[];distribS=[];prices=[];model_mom=[];flag_ss=[];par=[];
    return
end
%check if parameters are within upper bounds
if any(guess>ubounds_vec)
    warning('Upper bounds on parameters violated!')
    obj_smm = 10000;
    sol=[];agg=[];b_grid=[];distribS=[];prices=[];model_mom=[];flag_ss=[];par=[];
    return
end
```

### Python (`fun_obj.py` 第66-76行)
```python
# 检查参数是否在下界内
if np.any(guess < lbounds_vec):
    print('警告：参数违反下界！')
    obj_smm = 10000
    return obj_smm, None, None, None, None, None, None, None, None

# 检查参数是否在上界内
if np.any(guess > ubounds_vec):
    print('警告：参数违反上界！')
    obj_smm = 10000
    return obj_smm, None, None, None, None, None, None, None, None
```

**结论**：✅ **完全一致**

---

## 8. 收敛条件

### MATLAB (`fminsearch`)
```matlab
options = optimset('MaxIter',5000,'Display','iter');
```
- 最大迭代次数：5000
- 收敛条件：Nelder-Mead的默认收敛条件

### Python (`L-BFGS-B`)
```python
options = {
    'maxiter': 50,  # 最大迭代次数
    'ftol': 1e-4,   # 函数值收敛容差
    'gtol': 1e-4    # 梯度收敛容差
}
```
- 最大迭代次数：50（快速测试为5）
- 函数值收敛容差：1e-4
- 梯度收敛容差：1e-4

**差异**：
- ⚠️ 算法不同，收敛条件不可直接比较
- ⚠️ Python的迭代次数设置较小（可能需要调整）

---

## 9. 总结

### 主要差异

| 方面 | MATLAB | Python | 说明 |
|------|--------|--------|------|
| **优化算法** | 3种选择（simulan, simulannealbnd, fminsearch） | 1种（L-BFGS-B） | ⚠️ Python不支持模拟退火和Nelder-Mead |
| **默认算法** | fminsearch (Nelder-Mead) | L-BFGS-B | ⚠️ 算法不同 |
| **市场出清惩罚** | ❌ 无 | ✅ 有 | ⚠️ Python版本是改进 |
| **目标函数计算** | ✅ | ✅ | 完全一致 |
| **参数边界检查** | ✅ | ✅ | 完全一致 |
| **结果保存** | ✅ | ✅ | 完全一致 |
| **中间结果记录** | ✅ | ✅ | 完全一致 |

### 关键问题

1. **算法差异**：
   - MATLAB默认使用Nelder-Mead（不需要梯度）
   - Python使用L-BFGS-B（需要梯度，通常更快但可能更敏感）

2. **收敛行为可能不同**：
   - Nelder-Mead：基于函数值比较，对非光滑函数更鲁棒
   - L-BFGS-B：基于梯度信息，对光滑函数更高效

3. **建议**：
   - 如果要完全一致，Python应该实现Nelder-Mead算法（使用`scipy.optimize.minimize`的`method='Nelder-Mead'`，但需要处理边界约束）
   - 或者，MATLAB也可以使用L-BFGS-B（如果MATLAB优化工具箱支持）

### 结论

**校准流程基本一致**，但有以下差异：
1. ⚠️ **优化算法不同**：这是主要差异
2. ✅ **目标函数计算一致**
3. ✅ **参数处理一致**
4. ⚠️ **市场出清条件处理不同**（Python版本是改进）

如果要完全一致，建议：
- Python实现Nelder-Mead算法（带边界约束）
- 或者移除Python的市场出清惩罚项（但**不建议**这样做）














