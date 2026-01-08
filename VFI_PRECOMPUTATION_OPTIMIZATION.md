# 约束VFI预计算优化

## ✅ 优化完成

### 优化目标
将约束VFI之前的运算存储起来，在约束VFI迭代中直接调用，避免重复计算。

---

## 🔧 实现内容

### 1. 创建预计算函数

**文件**: `sub/sub_vfi_onestep.py`

**函数**: `precompute_vfi_constants` (Numba版本) 和 `precompute_vfi_constants_wrapper` (包装函数)

**预计算的值**:
1. **`kp_ub_ind_mat`** (nk, nb, nx): 下一期资本上界的索引
   - 原来：每次迭代都要重新计算 `kp_ub_ind`
   - 现在：在约束VFI之前一次性计算并存储

2. **`threshold_mat`** (nk, nb, nx): 清算阈值矩阵
   - 原来：每次迭代都要重新计算 `threshold_val = theta * (1.0 - delta) * k_val - b_val`
   - 现在：在约束VFI之前一次性计算并存储

---

### 2. 修改VFI主函数

**文件**: `sub/sub_vfi_onestep.py`

**函数**: `sub_vfi_onestep_numba`

**改进**:
- 添加了 `kp_ub_ind_mat` 和 `threshold_mat` 参数
- 在函数内部检查是否使用预计算值
- 如果提供了预计算值，直接使用；否则使用原来的计算方法（向后兼容）

---

### 3. 修改调用代码

**文件**: `fun_vfi1.py`

**改进**:
- 在约束VFI循环之前调用 `precompute_vfi_constants_wrapper`
- 将预计算的值传递给 `sub_vfi_onestep` 函数

---

## 📊 性能提升

### 优化前
- 每次VFI迭代都要重新计算：
  - `kp_ub_ind`: O(nk) 搜索操作，每个 (k_c, b_c, x_c) 都要执行
  - `threshold_val`: 每个 (k_c, b_c, x_c) 都要计算

### 优化后
- 预计算一次，所有迭代复用：
  - `kp_ub_ind_mat`: 一次性计算，O(nk × nb × nx × nk) = O(nk² × nb × nx)
  - `threshold_mat`: 一次性计算，O(nk × nb × nx)

### 预期性能提升
- **减少计算量**: 在VFI迭代中，每个 (k_c, b_c, x_c) 减少约 2-3 次计算
- **提升缓存效率**: 预计算的值存储在连续内存中，访问更快
- **总体提升**: 预计约束VFI部分速度提升 **10-20%**

---

## 🔍 代码示例

### 使用预计算值

```python
# 在约束VFI之前
kp_ub_ind_mat, threshold_mat = precompute_vfi_constants_wrapper(
    kp_bar, k_grid, b_grid, profit_mat, theta, delta)

# 在VFI迭代中
val_new, pol_kp_ind_con = sub_vfi_onestep(
    val, val0_unc, kp_bar, B_hat, profit_mat, k_grid, b_grid, 
    pi_x, theta, q, delta, psi, do_howard, n_howard,
    kp_ub_ind_mat, threshold_mat)  # 传递预计算值
```

### 不使用预计算值（向后兼容）

```python
# 不传递预计算值，函数会自动使用原来的计算方法
val_new, pol_kp_ind_con = sub_vfi_onestep(
    val, val0_unc, kp_bar, B_hat, profit_mat, k_grid, b_grid, 
    pi_x, theta, q, delta, psi, do_howard, n_howard)
```

---

## ✅ 验证结果

- ✅ 预计算函数编译成功
- ✅ 导入测试通过
- ✅ 预计算值形状正确
- ✅ 向后兼容性保持

---

## 📝 注意事项

1. **内存使用**: 预计算值需要额外的内存空间：
   - `kp_ub_ind_mat`: nk × nb × nx × 4 bytes (int32)
   - `threshold_mat`: nk × nb × nx × 8 bytes (float64)
   - 总计: nk × nb × nx × 12 bytes

2. **向后兼容**: 如果不传递预计算值，函数会自动使用原来的计算方法

3. **Numba优化**: 预计算函数使用Numba JIT编译，计算速度很快

---

## 🚀 使用建议

1. **对于稳态计算**: 推荐使用预计算，因为VFI迭代次数较多
2. **对于转移动态**: 可以根据实际情况选择是否使用预计算
3. **内存受限**: 如果内存紧张，可以不使用预计算（向后兼容）

---

生成时间: 2026-01-05









