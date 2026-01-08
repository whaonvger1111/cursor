# 稳态计算参数监控总结

## 监控结果

### 当前状态（2026-01-04）

**参数文件中的值** (`inputs/estim_params.txt`):
```
mass         = 0.0450000000
fixcost1     = 0.1652544033
fixcost2     = 0.0047081982
theta        = 0.9094588315
psi          = 0.0039413875
k_alpha      = 0.4458454251
x0           = 1.0743375933
epsx         = 0.0983399600
rhox         = 0.9572858171
zeta         = 23.4199308730
```

**验证结果**：
- ✅ **参数文件值与实际使用值完全一致**
- ✅ **稳态计算会使用参数文件中的值**

**结论**：
- 如果参数文件包含**校准后的值**，稳态计算会使用**校准后的值**
- 如果参数文件包含**初始值**，稳态计算会使用**初始值**
- 当前参数值看起来是**初始值**（因为快速测试只运行了5次迭代，参数几乎未变）

---

## 监控工具

### 1. `monitor_steady_state_params.py`

**功能**：监控稳态计算使用的参数值

**使用方法**：
```bash
python monitor_steady_state_params.py
```

**输出**：
- 显示参数文件中的值
- 显示 `set_parameters()` 设置后的值
- 对比两者是否一致
- 保存监控报告到文件

**用途**：
- 验证稳态计算是否使用了参数文件中的值
- 检查参数值是否正确传递

---

### 2. `check_calibration_usage.py`

**功能**：检查校准前后的参数值变化

**使用方法**：
```bash
python check_calibration_usage.py
```

**输出**：
- 显示当前参数文件中的值
- 显示校准前的值（如果有备份文件）
- 对比校准前后的变化
- 保存检查报告到文件

**用途**：
- 确认参数是否已被校准更新
- 查看校准前后参数值的变化

---

### 3. `fun_steady_state.py`（已修改）

**功能**：在稳态计算开始时记录使用的参数值

**修改内容**：
- 在稳态计算开始时，记录所有校准参数的值
- 写入日志文件 `steady_state_iterations.log`

**用途**：
- 实时监控稳态计算使用的参数值
- 便于调试和验证

---

## 使用流程

### 场景1：运行校准后，验证稳态计算使用校准后的值

```
步骤1：运行校准
  python run_calibration.py
  → estim_params.txt 被更新为校准后的值
  → estim_params_backup.txt 保存校准前的值

步骤2：检查校准前后的变化
  python check_calibration_usage.py
  → 显示参数值的变化

步骤3：验证稳态计算使用的值
  python monitor_steady_state_params.py
  → 确认稳态计算会使用校准后的值

步骤4：运行稳态计算
  python main.py  # do_calib = 0
  → 查看 steady_state_iterations.log
  → 确认使用的参数值是校准后的值
```

### 场景2：直接运行稳态计算，验证使用的参数值

```
步骤1：检查当前参数值
  python check_calibration_usage.py
  → 查看当前参数文件中的值

步骤2：验证稳态计算使用的值
  python monitor_steady_state_params.py
  → 确认参数值一致

步骤3：运行稳态计算
  python main.py  # do_calib = 0
  → 查看 steady_state_iterations.log
  → 确认使用的参数值
```

---

## 监控报告文件

### 1. `steady_state_params_monitor_YYYYMMDD_HHMMSS.txt`

**内容**：
- 参数文件中的值
- `set_parameters()` 设置后的值
- 对比结果

**生成时机**：运行 `monitor_steady_state_params.py` 时

---

### 2. `calibration_usage_check_YYYYMMDD_HHMMSS.txt`

**内容**：
- 当前参数文件中的值
- 校准前的值（如果有备份）
- 对比结果

**生成时机**：运行 `check_calibration_usage.py` 时

---

### 3. `steady_state_iterations.log`

**内容**：
- 稳态计算的详细日志
- 每次计算开始时使用的参数值（已添加）

**生成时机**：运行 `fun_steady_state()` 时

---

## 关键结论

### ✅ 已验证

1. **参数值传递正确**：
   - 参数文件中的值 → `set_parameters()` → `fun_steady_state()`
   - 所有值完全一致

2. **稳态计算会使用参数文件中的值**：
   - 如果文件包含校准后的值，会使用校准后的值
   - 如果文件包含初始值，会使用初始值

3. **监控机制已建立**：
   - 可以随时检查参数值
   - 可以对比校准前后的变化
   - 稳态计算时会记录使用的参数值

### 📋 建议

1. **运行完整校准后**：
   - 运行 `check_calibration_usage.py` 查看参数变化
   - 运行 `monitor_steady_state_params.py` 验证参数值
   - 运行稳态计算，查看日志确认使用的值

2. **每次运行稳态计算前**：
   - 可以运行 `monitor_steady_state_params.py` 快速检查
   - 查看日志文件确认使用的参数值

3. **调试时**：
   - 使用监控工具确认参数值是否正确
   - 检查日志文件查看详细过程

---

## 下一步

1. ✅ **已完成**：建立监控机制
2. ⏳ **待完成**：运行完整校准（至少50-100次迭代）
3. ⏳ **待完成**：校准后验证参数值变化
4. ⏳ **待完成**：使用校准后的参数值运行稳态计算













