# 稳态计算是否使用校准结果？

## 答案：取决于参数文件是否被更新

### 关键机制

**参数值的来源**：`set_parameters.py` 从 `estim_params.txt` 文件读取参数值

```python
# set_parameters.py 第115-130行
filepath = os.path.join(par.get('InpDir', 'inputs'), file_params)

if os.path.exists(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                try:
                    value = float(parts[1])
                    par[name] = value  # 读取参数值
                except ValueError:
                    pass
```

---

## 两种场景

### 场景1：校准完成后，运行稳态计算（`do_calib = 0`）

**流程**：
```
1. 运行校准（do_calib = 2）
   → 优化器找到最优参数值
   → 保存到 estim_params.txt（覆盖原文件）

2. 运行稳态计算（do_calib = 0）
   → set_parameters() 读取 estim_params.txt
   → 读取的是校准后的参数值
   → fun_steady_state() 使用校准后的参数值计算稳态
```

**结论**：✅ **稳态计算使用校准后的参数值**

**代码证据**（`run_calibration.py` 第190-196行）：
```python
# 保存校准后的参数到文件
output_file = os.path.join(par['InpDir'], file_params)
with open(output_file, 'w') as f:
    for i, name in enumerate(calibNames):
        f.write(f'{name}  {result.x[i]:.10f}\n')  # 覆盖原文件
```

---

### 场景2：未运行校准，直接运行稳态计算（`do_calib = 0`）

**流程**：
```
1. estim_params.txt 包含初始参数值（未校准）

2. 运行稳态计算（do_calib = 0）
   → set_parameters() 读取 estim_params.txt
   → 读取的是初始参数值
   → fun_steady_state() 使用初始参数值计算稳态
```

**结论**：❌ **稳态计算使用初始参数值，不使用校准结果**

---

## 实际验证

### 检查参数文件

**校准前**（`estim_params.txt`）：
```
mass  0.045
fixcost1  0.1652544033 
...
```

**校准后**（`estim_params.txt` 被更新）：
```
mass  0.045  (可能改变)
fixcost1  0.1652544033  (可能改变)
...
```

### 验证方法

```python
# 1. 运行校准
python run_calibration.py
# → estim_params.txt 被更新

# 2. 检查参数文件
cat inputs/estim_params.txt
# → 应该看到校准后的值

# 3. 运行稳态计算
python main.py  # do_calib = 0
# → 会使用校准后的参数值
```

---

## MATLAB 的行为

### MATLAB 也遵循相同的机制

**MATLAB (`main.m` 第265-270行)**：
```matlab
% Save estimated parameters in file estim_params.txt
FID = fopen(fullfile(par.InpDir,'estim_params.txt'),'w');
for i = 1:length(x)
    fprintf(FID,'%s  %.10f \n',calibNames{i},x(i));
end
fclose(FID);
```

**MATLAB (`main.m` 第92-95行，`do_calib = 0`)**：
```matlab
if par.do_calib == 0
    % 调用 set_parameters，会读取 estim_params.txt
    [par,guess,bounds,calibNames,...] = set_parameters(par,file_params);
    % 然后计算稳态
    [obj_smm,sol,agg,...] = fun_obj(guess,par,...);
end
```

**结论**：✅ **MATLAB 和 Python 的行为一致**

---

## 总结

### 回答您的问题

**"稳态计算没有用到校准结果？"**

**答案**：
- ✅ **如果已经运行过校准**：稳态计算**会使用**校准后的参数值
- ❌ **如果没有运行过校准**：稳态计算**不会使用**校准结果（使用初始参数值）

### 关键点

1. **参数值的来源**：`estim_params.txt` 文件
2. **校准会更新文件**：校准完成后，`estim_params.txt` 被更新为校准后的值
3. **稳态计算读取文件**：`set_parameters()` 总是从 `estim_params.txt` 读取参数值
4. **因此**：如果文件已被校准更新，稳态计算会使用校准后的值

### 更准确的表述

- **稳态计算本身不依赖校准过程**：可以使用任何参数值
- **但稳态计算会读取参数文件**：如果文件包含校准后的值，就会使用这些值
- **校准会更新参数文件**：因此校准后的稳态计算会使用校准结果

### 实际工作流程

```
步骤1：运行校准
  python run_calibration.py
  → estim_params.txt 被更新为校准后的值

步骤2：运行稳态计算
  python main.py  # do_calib = 0
  → set_parameters() 读取 estim_params.txt（现在是校准后的值）
  → fun_steady_state() 使用校准后的参数值
  → 稳态结果基于校准后的参数
```

**结论**：✅ **校准后的稳态计算会使用校准结果**














